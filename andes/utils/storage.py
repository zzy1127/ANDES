"""Storage abstractions used by ANDES operators.

Operators read their input and write their output through a `StorageABC`
implementation. The default implementation, `FileStorage`, is a thin wrapper
around pandas readers/writers that materializes each operator step as a file
on disk.
"""

from __future__ import annotations

import copy
import os
from abc import ABC, abstractmethod
from typing import Any, Literal

import pandas as pd

from andes import get_logger


class StorageABC(ABC):
    """Abstract base class for ANDES storage backends."""

    @abstractmethod
    def get_keys_from_dataframe(self) -> list[str]:
        """Return the column names of the data currently held in storage."""

    @abstractmethod
    def read(self, output_type) -> Any:
        """Read data from the current step.

        Args:
            output_type: Desired return type, e.g. ``"dataframe"`` or ``"dict"``.
        """

    @abstractmethod
    def write(self, data: Any) -> Any:
        """Persist ``data`` for the current step and return its location."""

    def __repr__(self) -> str:
        attrs = self.__dict__
        attr_strs = []
        for key, value in attrs.items():
            if isinstance(value, pd.DataFrame):
                value_repr = f"<DataFrame shape={value.shape}>"
            elif isinstance(value, set):
                value_repr = f"<{type(value).__name__} size={len(value)}>"
            elif isinstance(value, dict):
                value_repr = f"<{type(value).__name__} size={len(value)}>"
            else:
                value_repr = repr(value)
                if len(value_repr) > 100:
                    value_repr = value_repr[:97] + "..."
            attr_strs.append(f"  {key} = {value_repr}")

        body = "\n".join(attr_strs)
        return f"<{self.__class__.__name__} Object:\n{body}\n>"


class FileStorage(StorageABC):
    """Disk-backed storage that materializes each operator step as a file.

    Step 0 (the "first entry") can be loaded from:
      * a local file path, whose extension determines the reader, or
      * a remote dataset specified with the ``hf:`` (HuggingFace) or ``ms:``
        (ModelScope) prefix.

    Subsequent steps are written under ``cache_path`` with filenames derived
    from ``file_name_prefix`` and ``cache_type``.
    """

    def __init__(
        self,
        first_entry_file_name: str,
        cache_path: str = "./cache",
        file_name_prefix: str = "andes_cache_step",
        cache_type: Literal["json", "jsonl", "csv", "parquet", "pickle"] = "jsonl",
    ):
        self.first_entry_file_name = first_entry_file_name
        self.cache_path = cache_path
        self.file_name_prefix = file_name_prefix
        self.cache_type = cache_type
        self.operator_step = -1
        self.logger = get_logger()

    def _get_cache_file_path(self, step: int) -> str:
        if step == -1:
            msg = (
                "You must call storage.step() before reading or writing data. "
                "Please call storage.step() first for each operator step."
            )
            self.logger.error(msg)
            raise ValueError(msg)
        if step == 0:
            return os.path.join(self.first_entry_file_name)
        return os.path.join(
            self.cache_path,
            f"{self.file_name_prefix}_step{step}.{self.cache_type}",
        )

    def step(self) -> "FileStorage":
        self.operator_step += 1
        # Shallow copy is enough for the current usage pattern; if a future
        # version maintains in-memory dataframes we should switch to a custom
        # deepcopy that skips DataFrame buffers to avoid OOM.
        return copy.copy(self)

    def reset(self) -> "FileStorage":
        self.operator_step = -1
        return self

    def get_keys_from_dataframe(self) -> list[str]:
        dataframe = self.read(output_type="dataframe")
        return dataframe.columns.tolist() if isinstance(dataframe, pd.DataFrame) else []

    def _load_local_file(self, file_path: str, file_type: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File {file_path} does not exist. Please check the path."
            )
        try:
            if file_type == "json":
                return pd.read_json(file_path)
            if file_type == "jsonl":
                return pd.read_json(file_path, lines=True)
            if file_type == "csv":
                return pd.read_csv(file_path)
            if file_type == "parquet":
                return pd.read_parquet(file_path)
            if file_type == "pickle":
                return pd.read_pickle(file_path)
            if file_type == "xlsx":
                return pd.read_excel(file_path)
            raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as exc:
            raise ValueError(f"Failed to load {file_type} file: {exc}") from exc

    def _convert_output(self, dataframe: pd.DataFrame, output_type: str) -> Any:
        if output_type == "dataframe":
            return dataframe
        if output_type == "dict":
            return dataframe.to_dict(orient="records")
        raise ValueError(f"Unsupported output type: {output_type}")

    def read(self, output_type: Literal["dataframe", "dict"] = "dataframe") -> Any:
        """Read data from the current step.

        ``first_entry_file_name`` may also be a remote dataset, identified by
        a prefix:

            * ``hf:{dataset_name}[:config][:split]`` — HuggingFace dataset,
              e.g. ``hf:openai/gsm8k:main:train``
            * ``ms:{dataset_name}[:split]`` — ModelScope dataset,
              e.g. ``ms:modelscope/gsm8k:train``
        """
        if self.operator_step == 0 and self.first_entry_file_name == "":
            self.logger.info("first_entry_file_name is empty, returning empty dataframe")
            empty_dataframe = pd.DataFrame()
            return self._convert_output(empty_dataframe, output_type)

        file_path = self._get_cache_file_path(self.operator_step)
        self.logger.info(f"Reading data from {file_path} with type {output_type}")

        if self.operator_step == 0:
            source = self.first_entry_file_name
            self.logger.info(
                f"Reading remote dataset from {source} with type {output_type}"
            )
            if source.startswith("hf:"):
                from datasets import load_dataset

                _, dataset_name, *parts = source.split(":")
                if len(parts) == 1:
                    config, split = None, parts[0]
                elif len(parts) == 2:
                    config, split = parts
                else:
                    config, split = None, "train"

                dataset = (
                    load_dataset(dataset_name, config, split=split)
                    if config
                    else load_dataset(dataset_name, split=split)
                )
                dataframe = dataset.to_pandas()
                return self._convert_output(dataframe, output_type)

            if source.startswith("ms:"):
                from modelscope import MsDataset

                _, dataset_name, *split_parts = source.split(":")
                split = split_parts[0] if split_parts else "train"
                dataset = MsDataset.load(dataset_name, split=split)
                dataframe = pd.DataFrame(dataset)
                return self._convert_output(dataframe, output_type)

            local_cache = file_path.split(".")[-1]
        else:
            local_cache = self.cache_type

        dataframe = self._load_local_file(file_path, local_cache)
        return self._convert_output(dataframe, output_type)

    def write(self, data: Any) -> Any:
        """Persist ``data`` to the next-step file managed by this storage.

        Strings inside the payload are passed through a UTF-8 round-trip with
        ``errors="replace"`` so that lone surrogate characters returned by
        upstream LLM responses do not break the JSON writers.
        """

        def _sanitize(obj):
            if isinstance(obj, str):
                return obj.encode("utf-8", "replace").decode("utf-8")
            if isinstance(obj, dict):
                return {k: _sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(item) for item in obj]
            if isinstance(obj, (int, float, bool)) or obj is None:
                return obj
            try:
                return _sanitize(str(obj))
            except Exception:
                return obj

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                cleaned = [_sanitize(item) for item in data]
                dataframe = pd.DataFrame(cleaned)
            else:
                raise ValueError(
                    f"Unsupported list element type: "
                    f"{type(data[0]) if data else 'empty list'}"
                )
        elif isinstance(data, pd.DataFrame):
            dataframe = data.map(_sanitize)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        file_path = self._get_cache_file_path(self.operator_step + 1)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.logger.success(
            f"Writing data to {file_path} with type {self.cache_type}"
        )

        if self.cache_type == "json":
            dataframe.to_json(file_path, orient="records", force_ascii=False, indent=2)
        elif self.cache_type == "jsonl":
            dataframe.to_json(file_path, orient="records", lines=True, force_ascii=False)
        elif self.cache_type == "csv":
            dataframe.to_csv(file_path, index=False)
        elif self.cache_type == "parquet":
            dataframe.to_parquet(file_path)
        elif self.cache_type == "pickle":
            dataframe.to_pickle(file_path)
        elif self.cache_type == "xlsx":
            dataframe.to_excel(file_path, index=False)
        else:
            raise ValueError(
                "Unsupported file type: "
                f"{self.cache_type}; expected json, jsonl, csv, parquet, pickle or xlsx."
            )

        return file_path
