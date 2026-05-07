"""HTTP-based LLM serving backend for ANDES.

`APILLMServing_request` is a thread-pooled wrapper around OpenAI-compatible
``/chat/completions`` and ``/embeddings`` endpoints. It is the default serving
backend used by ANDES operators and pipelines.
"""

from __future__ import annotations

import json
import os
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm

from andes import __version__ as ANDES_VERSION
from andes.core import LLMServingABC

from ..logger import get_logger


class APILLMServing_request(LLMServingABC):
    """OpenAI-compatible chat/embedding client driven by a thread pool.

    The API key is read at construction time from the environment variable
    named by ``key_name_of_api_key`` (default: ``OPENAI_API_KEY``); raising
    early avoids leaking secrets through call signatures or process listings.
    """

    def start_serving(self) -> None:
        self.logger.info("APILLMServing_request: no local service to start.")

    def __init__(
        self,
        api_url: str = "https://api.openai.com/v1/chat/completions",
        key_name_of_api_key: str = "OPENAI_API_KEY",
        model_name: str = "gpt-4o",
        temperature: float = 0.0,
        max_workers: int = 10,
        max_retries: int = 5,
        connect_timeout: float = 10.0,
        read_timeout: float = 120.0,
        **configs: dict,
    ):
        self.api_url = api_url
        self.model_name = model_name
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.timeout = (connect_timeout, read_timeout)

        if "timeout" in configs:
            warnings.warn(
                "The `timeout` parameter is deprecated. "
                "Please use `connect_timeout` and `read_timeout` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.timeout = (connect_timeout, configs.pop("timeout"))

        self.configs = configs
        self.configs.update({"temperature": temperature})

        self.logger = get_logger()

        # Read the API key from the environment so that it never lives on the
        # call stack or in serialized config files.
        self.api_key = os.environ.get(key_name_of_api_key)
        if self.api_key is None:
            error_msg = (
                f"Missing `{key_name_of_api_key}` in the environment. "
                f"Please export `{key_name_of_api_key}` with your API key for {api_url} "
                "before instantiating APILLMServing_request."
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=self.max_workers,
            pool_maxsize=self.max_workers,
            # Retries are handled at the application layer in
            # `_api_chat_id_retry`; do not double-retry at the transport layer.
            max_retries=0,
            # Block when the pool is exhausted instead of opening unbounded
            # extra connections.
            pool_block=True,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"ANDES/{ANDES_VERSION}",
        }

    def format_response(self, response: dict, is_embedding: bool = False) -> str:
        """Normalize either an embedding or chat-completion response payload."""
        if is_embedding:
            return response.get("data", [{}])[0].get("embedding", [])

        message = response.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")

        # Already wrapped in <think>...<answer> by the model: pass through.
        if re.search(r"<think>.*?</think>.*?<answer>.*?</answer>", content, re.DOTALL):
            return content

        # OpenAI-style reasoning models expose a separate `reasoning_content`.
        # Wrap both into a single string so downstream operators stay simple.
        reasoning_content = message.get("reasoning_content")
        if reasoning_content:
            return f"<think>{reasoning_content}</think>\n<answer>{content}</answer>"

        return content

    def _api_chat_with_id(
        self,
        id: int,
        payload,
        model: str,
        is_embedding: bool = False,
        json_schema: Optional[dict] = None,
    ):
        start = time.time()
        try:
            if is_embedding:
                payload = {"model": model, "input": payload}
            elif json_schema is None:
                payload = {"model": model, "messages": payload}
            else:
                payload = {
                    "model": model,
                    "messages": payload,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "custom_response",
                            "strict": True,
                            "schema": json_schema,
                        },
                    },
                }

            payload.update(self.configs)
            payload = json.dumps(payload)
            response = self.session.post(
                self.api_url, headers=self.headers, data=payload, timeout=self.timeout
            )
            cost = time.time() - start
            if response.status_code == 200:
                return id, self.format_response(response.json(), is_embedding)

            self.logger.error(
                f"API request failed id={id} status={response.status_code} "
                f"cost={cost:.2f}s body={response.text[:500]}"
            )
            return id, None

        # Connect-phase timeout: server is unreachable. Surface as RuntimeError
        # so the caller can decide whether to abort the whole batch.
        except requests.exceptions.ConnectTimeout as exc:
            cost = time.time() - start
            self.logger.error(f"API connect timeout (id={id}) cost={cost:.2f}s: {exc}")
            raise RuntimeError(
                f"Cannot connect to LLM server (connect timeout): {exc}"
            ) from exc

        # Read-phase timeout: server accepted the request but did not respond
        # within `read_timeout`. Treat as a soft failure so it gets retried.
        except requests.exceptions.ReadTimeout as exc:
            cost = time.time() - start
            warnings.warn(
                f"API read timeout (id={id}) cost={cost:.2f}s: {exc}", RuntimeWarning
            )
            return id, None

        except requests.exceptions.Timeout as exc:
            cost = time.time() - start
            warnings.warn(
                f"API timeout (id={id}) cost={cost:.2f}s: {exc}", RuntimeWarning
            )
            return id, None

        # `ConnectionError` may wrap several underlying conditions on different
        # platforms (read timeouts, refused, reset, etc.). Disambiguate by
        # message text and route accordingly.
        except requests.exceptions.ConnectionError as exc:
            cost = time.time() - start
            msg = str(exc).lower()

            if "read timed out" in msg:
                warnings.warn(
                    f"API read timeout (id={id}) cost={cost:.2f}s: {exc}",
                    RuntimeWarning,
                )
                return id, None

            if "connect timeout" in msg or ("timed out" in msg and "connect" in msg):
                self.logger.error(
                    f"API connect timeout (id={id}) cost={cost:.2f}s: {exc}"
                )
                raise RuntimeError(
                    f"Cannot connect to LLM server (connect timeout): {exc}"
                ) from exc

            self.logger.error(f"API connection error (id={id}) cost={cost:.2f}s: {exc}")
            raise RuntimeError(f"Cannot connect to LLM server: {exc}") from exc

        except Exception as exc:
            cost = time.time() - start
            self.logger.exception(
                f"API request error (id={id}) cost={cost:.2f}s: {exc}"
            )
            return id, None

    def _api_chat_id_retry(
        self, id, payload, model, is_embedding: bool = False, json_schema: Optional[dict] = None
    ):
        for i in range(self.max_retries):
            id, response = self._api_chat_with_id(
                id, payload, model, is_embedding, json_schema
            )
            if response is not None:
                return id, response
            time.sleep(2 ** i)
        return id, None

    def _run_threadpool(self, task_args_list: list[dict], desc: str) -> list:
        """Submit ``task_args_list`` to the thread pool and return responses.

        Each element of ``task_args_list`` is a kwargs dict for
        ``_api_chat_id_retry``. Results are reordered by ``id`` so callers can
        rely on positional alignment with the input.
        """
        responses = [None] * len(task_args_list)
        n = len(task_args_list)
        if n == 0:
            return responses

        self.logger.info(
            "%s | %d request(s), max_workers=%d", desc.strip("."), n, self.max_workers
        )

        executor = ThreadPoolExecutor(max_workers=self.max_workers)
        interrupted = False
        try:
            futures = [
                executor.submit(self._api_chat_id_retry, **task_args)
                for task_args in task_args_list
            ]
            for future in tqdm(
                as_completed(futures),
                total=n,
                desc=desc,
                miniters=1,
                mininterval=0.25,
            ):
                try:
                    response = future.result()
                    responses[response[0]] = response[1]
                except Exception:
                    self.logger.exception(
                        "Worker crashed unexpectedly in threadpool"
                    )
        except KeyboardInterrupt:
            interrupted = True
            self.logger.warning(
                "KeyboardInterrupt: cancelling pending API requests "
                "(not waiting on workers)."
            )
            raise
        finally:
            executor.shutdown(wait=not interrupted, cancel_futures=interrupted)

        return responses

    def generate_from_input(
        self,
        user_inputs: list[str],
        system_prompt: str = "You are a helpful assistant",
        json_schema: Optional[dict] = None,
    ) -> list[str]:
        task_args_list = [
            dict(
                id=idx,
                payload=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                model=self.model_name,
                json_schema=json_schema,
            )
            for idx, question in enumerate(user_inputs)
        ]
        return self._run_threadpool(
            task_args_list, desc="Generating responses from prompts......"
        )

    def generate_from_conversations(
        self, conversations: list[list[dict]]
    ) -> list[str]:
        task_args_list = [
            dict(id=idx, payload=dialogue, model=self.model_name)
            for idx, dialogue in enumerate(conversations)
        ]
        return self._run_threadpool(
            task_args_list, desc="Generating responses from conversations......"
        )

    def generate_embedding_from_input(self, texts: list[str]) -> list[list[float]]:
        task_args_list = [
            dict(id=idx, payload=txt, model=self.model_name, is_embedding=True)
            for idx, txt in enumerate(texts)
        ]
        return self._run_threadpool(task_args_list, desc="Generating embedding......")

    def cleanup(self):
        self.logger.info("Cleaning up resources in APILLMServing_request")
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
        except Exception:
            self.logger.exception("Failed to close requests session")
