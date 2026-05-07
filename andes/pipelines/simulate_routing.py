"""Router-only simulation for ANDES.

This script exercises the dynamic tag manager (router) without invoking the
generator or the refiner. It is useful for validating that a given
``task_description`` produces a healthy fusion/general split and that taxonomy
expansions trigger as expected before paying for a full synthesis run.
"""

from __future__ import annotations

import argparse
import ast
import io
import math
import os
import random
import sys
from collections import Counter
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Optional

# Direct script run: ensure this checkout is imported as `andes`, not some
# unrelated install that may live in site-packages.
_repo_root = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import json  # noqa: E402

from andes import get_logger  # noqa: E402
from andes.prompts.andes_prompts import ANDESFusionPrompt  # noqa: E402
from andes.serving import APILLMServing_request  # noqa: E402


AGENT_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
ANDES_CACHE_DIR = os.path.join(AGENT_TOOL_DIR, "cache")
# Expects users to point --config at examples/config.example.json (or a copy).
DEFAULT_CONFIG_PATH = os.path.join(_repo_root, "examples", "config.example.json")
DEFAULT_MODEL_NAME = "gpt-4o-mini"
DEFAULT_NUM_SAMPLES = 12000
DEFAULT_ROUND_SIZE = 1000
DEFAULT_ROUTER_BATCH_SIZE = 5

FORMAT_REQUIREMENTS = {
    "unstructured": None,
    "yaml": (
        "The output must contain valid YAML with the required keys, indentation, and structure. "
        "It must be wrapped in a Markdown fenced code block labeled yaml (```yaml ... ```). "
        "It must not include any explanation or extra text before or after the code block."
    ),
    "code": (
        "The output must contain the required code in the target language with correct syntax and complete structure. "
        "It must be wrapped in a Markdown fenced code block labeled with the target language (```target_language ... ```). "
        "It must not include any explanation or extra text before or after the code block."
    ),
    "tool_call": (
        "The output must contain valid tool call in the required JSON structure with the correct name and arguments. "
        "It must be wrapped in a Markdown fenced code block labeled json (```json ... ```). "
        "It must not include any explanation or extra text before or after the code block."
    ),
}


def _load_agent_tool_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)

    required = ("api_url", "task_description", "format_requirement", "num_samples")
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"config missing required keys: {', '.join(missing)}")
    return cfg


def resolve_format_requirement(format_requirement):
    if format_requirement is None:
        return None

    if not isinstance(format_requirement, str):
        raise ValueError("format_requirement must be a string selector or None.")

    selector = format_requirement.strip().lower()
    if not selector:
        return None

    if selector not in FORMAT_REQUIREMENTS:
        valid_keys = ", ".join(sorted(FORMAT_REQUIREMENTS.keys()))
        raise ValueError(f"Unknown format_requirement '{format_requirement}'. Allowed values: {valid_keys}.")

    return FORMAT_REQUIREMENTS[selector]


class DynamicTagManager:
    def __init__(self, prompt_template, llm_serving):
        self.prompt_template = prompt_template
        self.tags = self.prompt_template.tag

        self.tag_weights = {topic: 1.0 for topic in self.tags.keys()}
        self.tag_usage_count = {topic: 0 for topic in self.tags.keys()}
        self.tag_history = {topic: set(self.tags[topic].keys()) for topic in self.tags.keys()}
        self.llm_serving = llm_serving
        self.reward_factor = 1.5
        self.decay_factor = 0.8
        self.replacement_counts = {"topic": 0, "domain": 0, "theme": 0}

    def _expand_tag(self, topic, description):
        print(f"⚠️ [Dynamic Expansion] Top-level topic '{topic}' is crowded; expanding...")
        history_list = list(self.tag_history[topic])

        prompt = f"""
        You are an expert taxonomist expanding a knowledge tree for the topic "{topic}".

        We ultimately want to use these new tags as background scenarios to teach the following Target Task:
        [Target Task]: "{description}"

        Your task:
        Generate 6 BRAND NEW sub-domains under the topic "{topic}".
        For each new sub-domain, provide exactly 6 specific themes.

        CRITICAL CONSTRAINTS:
        1. DIRECTIONAL BUT PURE: The new tags should provide excellent, natural settings or metaphors for the Target Task. However, DO NOT directly use technical jargon from the Target Task in the tags. Keep them looking like natural real-world categories of "{topic}".
        2. NO DUPLICATES: You MUST NOT generate any sub-domains that overlap with this history list: {history_list}

        Output strictly in valid Python dict format like this:
        {{"New Sub-domain 1": ["Theme 1", "Theme 2", "Theme 3"], "New Sub-domain 2": [...]}}
        Do NOT output markdown code blocks. Return ONLY the dictionary string.
        """

        try:
            response = self.llm_serving.generate_from_input([prompt])[0]
            cleaned_response = response.replace("```python", "").replace("```json", "").replace("```", "").strip()
            new_sub_tags = ast.literal_eval(cleaned_response)

            if isinstance(new_sub_tags, dict):
                domain_count = len(new_sub_tags)
                theme_count = 0
                for themes in new_sub_tags.values():
                    if isinstance(themes, (list, tuple, set)):
                        theme_count += len(themes)
                    elif themes not in (None, ""):
                        theme_count += 1
                self.tags[topic] = new_sub_tags
                self.tag_history[topic].update(new_sub_tags.keys())
                self.replacement_counts["topic"] += 1
                self.replacement_counts["domain"] += domain_count
                self.replacement_counts["theme"] += theme_count
                print(f"✅ Expansion succeeded; replaced tags ({len(new_sub_tags)} sub-domains), history updated.")
            else:
                print("❌ Expansion failed: LLM output is not a dict.")
        except Exception as e:
            print(f"❌ Expansion parse failed: {e}")

    def sample_and_route_batch(self, description: str, batch_size: int, format_requirement: str = None):
        topics = list(self.tags.keys())
        sampled_items = []

        weights_list = [self.tag_weights[t] for t in topics]
        sampled_topics = random.choices(topics, weights=weights_list, k=batch_size)
        topic_counts = Counter(sampled_topics)

        for topic, count in topic_counts.items():
            self.tag_usage_count[topic] += count

            total_themes = sum(len(themes) for themes in self.tags[topic].values())
            dynamic_threshold = 0.8 * total_themes

            if self.tag_usage_count[topic] > dynamic_threshold:
                self._expand_tag(topic, description)
                self.tag_usage_count[topic] = 0
                self.tag_weights[topic] = 1.0

        for topic in sampled_topics:
            domain = random.choice(list(self.tags[topic].keys()))
            theme = random.choice(self.tags[topic][domain])
            sampled_items.append({"topic": topic, "domain": domain, "theme": theme})

        themes_list_str = "\n".join(f"{i}. {item['theme']} (from {item['topic']})" for i, item in enumerate(sampled_items))

        eval_prompt = f"""
        Target Dataset Description: {description}

        Here is a batch of background themes:
        {themes_list_str}

        Categorize each theme's index into one of three levels based on how suitable it is to be used as a background scenario for the target dataset:
        1. "Strong": Highly suitable, natural fit for the target dataset.
        2. "Ambiguous": Borderline, could be forced to fit with some creativity, but not a natural match.
        3. "Weak": Irrelevant, forced integration would be highly absurd or nonsensical.

        Return ONLY a valid Python dictionary containing three keys: 'Strong', 'Ambiguous', and 'Weak', mapping to lists of integer indices. Do not include markdown formatting.
        Example: {{"Strong": [0, 3], "Ambiguous": [1, 4], "Weak": [2]}}
        """

        try:
            response = self.llm_serving.generate_from_input([eval_prompt])[0]
            start = response.find("{")
            end = response.rfind("}") + 1
            categorization = ast.literal_eval(response[start:end])

            strong_indices = categorization.get("Strong", [])
            ambiguous_indices = categorization.get("Ambiguous", [])
            weak_indices = categorization.get("Weak", [])

            for idx in strong_indices:
                topic = sampled_items[idx]["topic"]
                self.tag_weights[topic] *= self.reward_factor

            for idx in weak_indices:
                topic = sampled_items[idx]["topic"]
                self.tag_weights[topic] = max(0.1, self.tag_weights[topic] * self.decay_factor)

            suitable_indices = set(strong_indices)
            for idx in ambiguous_indices:
                if random.random() < 0.8:
                    suitable_indices.add(idx)
        except Exception:
            suitable_indices = set(random.sample(range(batch_size), k=batch_size // 2))

        configs = []
        for idx, item in enumerate(sampled_items):
            config = {
                "topic": item["topic"],
                "domain": item["domain"],
                "theme": item["theme"],
                "is_fusion": idx in suitable_indices,
                "description": description,
            }
            if format_requirement is not None:
                config["format_requirement"] = format_requirement
            configs.append(config)

        return configs


def _sample_label(num_samples: int) -> str:
    if num_samples > 0 and num_samples % 1000 == 0:
        return f"{num_samples // 1000}k"
    return str(num_samples)


def _default_log_path(num_samples: int) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(ANDES_CACHE_DIR, f"routing_simulation_{_sample_label(num_samples)}_{stamp}.log")


def _format_percent(count: int, total: int) -> str:
    if total <= 0:
        return "0.00%"
    return f"{(count / total) * 100:.2f}%"


def _topic_ratio_text(topic_counter: Counter, total: int, limit: int = 5) -> str:
    ranked_topics = sorted(topic_counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    if not ranked_topics:
        return "None"
    return ", ".join(f"{topic}={_format_percent(count, total)}" for topic, count in ranked_topics)


@contextmanager
def _suppress_andes_noise():
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        yield


def _validate_positive_int(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def _emit(log_fp, line: str) -> None:
    print(line)
    log_fp.write(line + "\n")
    log_fp.flush()


def _build_round_lines(
    round_index: int,
    total_rounds: int,
    replacement_counts: dict,
    topic_counter: Counter,
    round_total: int,
    round_fusion: int,
    round_general: int,
    cumulative_total: int,
    cumulative_fusion: int,
) -> list[str]:
    round_label = str(round_index).zfill(max(2, len(str(total_rounds))))
    replacements_line = (
        f"Round {round_label} | replacements | cumulative "
        f"topic={int(replacement_counts.get('topic', 0))}, "
        f"domain={int(replacement_counts.get('domain', 0))}, "
        f"theme={int(replacement_counts.get('theme', 0))}"
    )
    topics_line = f"Round {round_label} | top5 topics | {_topic_ratio_text(topic_counter, round_total)}"
    fusion_line = (
        f"Round {round_label} | fusion/general | "
        f"round fusion={_format_percent(round_fusion, round_total)}, "
        f"round general={_format_percent(round_general, round_total)}, "
        f"cumulative fusion={_format_percent(cumulative_fusion, cumulative_total)}"
    )
    return [replacements_line, topics_line, fusion_line]


def run_simulation(
    config_path: str,
    num_samples: int,
    round_size: int,
    model_name: str,
    max_workers: Optional[int],
    log_path: Optional[str],
) -> str:
    _validate_positive_int("num_samples", num_samples)
    _validate_positive_int("round_size", round_size)

    cfg = _load_agent_tool_config(config_path)
    resolved_format_requirement = resolve_format_requirement(cfg["format_requirement"])
    effective_max_workers = int(max_workers if max_workers is not None else cfg.get("max_workers", 100))
    _validate_positive_int("max_workers", effective_max_workers)

    logger = get_logger()
    previous_logger_disabled = logger.disabled
    logger.disabled = True
    llm_serving = APILLMServing_request(
        api_url=cfg["api_url"],
        model_name=model_name,
        max_workers=effective_max_workers,
    )
    tag_manager = DynamicTagManager(ANDESFusionPrompt(), llm_serving)

    final_log_path = log_path or _default_log_path(num_samples)
    os.makedirs(os.path.dirname(os.path.abspath(final_log_path)) or ".", exist_ok=True)

    total_rounds = math.ceil(num_samples / round_size)
    cumulative_total = 0
    cumulative_fusion = 0

    try:
        with open(final_log_path, "w", encoding="utf-8") as log_fp:
            for round_index in range(1, total_rounds + 1):
                round_target = min(round_size, num_samples - cumulative_total)
                round_topic_counter = Counter()
                round_fusion = 0
                round_general = 0
                round_consumed = 0

                while round_consumed < round_target:
                    remaining = round_target - round_consumed
                    batch_size = min(DEFAULT_ROUTER_BATCH_SIZE, math.ceil(remaining / 3))
                    with _suppress_andes_noise():
                        configs = tag_manager.sample_and_route_batch(
                            description=cfg["task_description"],
                            batch_size=batch_size,
                            format_requirement=resolved_format_requirement,
                        )

                    for config in configs:
                        if round_consumed >= round_target:
                            break
                        take = min(3, round_target - round_consumed)
                        topic_name = str(config.get("topic") or "Unknown").strip() or "Unknown"
                        round_topic_counter[topic_name] += take
                        if bool(config.get("is_fusion", False)):
                            round_fusion += take
                        else:
                            round_general += take
                        round_consumed += take

                cumulative_total += round_consumed
                cumulative_fusion += round_fusion
                round_lines = _build_round_lines(
                    round_index=round_index,
                    total_rounds=total_rounds,
                    replacement_counts=tag_manager.replacement_counts,
                    topic_counter=round_topic_counter,
                    round_total=round_consumed,
                    round_fusion=round_fusion,
                    round_general=round_general,
                    cumulative_total=cumulative_total,
                    cumulative_fusion=cumulative_fusion,
                )
                for line in round_lines:
                    _emit(log_fp, line)
    finally:
        llm_serving.cleanup()
        logger.disabled = previous_logger_disabled

    return final_log_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate ANDES routing without generating synthesis data.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to the ANDES config JSON.")
    parser.add_argument("--num-samples", type=int, default=DEFAULT_NUM_SAMPLES, help="Total simulated final samples.")
    parser.add_argument("--round-size", type=int, default=DEFAULT_ROUND_SIZE, help="Samples per reporting round.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="Model name for routing LLM calls.")
    parser.add_argument("--max-workers", type=int, default=None, help="Override max_workers from config.")
    parser.add_argument("--log-path", default=None, help="Optional explicit log output path.")
    args = parser.parse_args()
    run_simulation(
        config_path=args.config,
        num_samples=args.num_samples,
        round_size=args.round_size,
        model_name=args.model_name,
        max_workers=args.max_workers,
        log_path=args.log_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
