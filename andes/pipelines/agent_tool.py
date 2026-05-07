"""End-to-end ANDES pipeline entry point.

This module exposes :class:`ANDESAgentTool`, a single-call wrapper that runs
``router -> generator -> refiner`` for one task description and writes the
synthesis artifacts into ``andes/pipelines/cache/``. It can be used as a
Python API or driven from the command line via ``python -m andes.pipelines.agent_tool``.

See ``examples/config.example.json`` for the expected config schema.
"""

import argparse
import ast
import json
import os
import random
import shutil
import sys
from collections import Counter
from datetime import datetime
from typing import Optional

# Direct script run: ensure this checkout is imported as `andes`, not some
# unrelated install that may live in site-packages.
_repo_root = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from andes.operators.text_sft import ANDESGenerator, ANDESRefiner  # noqa: E402
from andes.prompts.andes_prompts import ANDESFusionPrompt, ANDESRefinePrompt  # noqa: E402
from andes.serving import APILLMServing_request  # noqa: E402
from andes.utils.storage import FileStorage  # noqa: E402

_AGENT_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
ANDES_CACHE_DIR = os.path.join(_AGENT_TOOL_DIR, "cache")


def _andes_run_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


FORMAT_REQUIREMENTS = {
    "unstructured": None,
    "code": (
        "The output must contain the required code in the target language with correct syntax and complete structure. "
        "It must be wrapped in a Markdown fenced code block labeled with the target language (```target_language ... ```). "
        "It must not include any explanation or extra text before or after the code block."
    ),
    "tool_call": (
        "The output must contain valid tool call in the required JSON structure with the correct name and arguments. "
        "It must be wrapped in a Markdown fenced code block labeled json (```json ... ```). "
        "It must not include any explanation or extra text before or after the code block."
    )
}


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


def _normalize_is_fusion(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _load_jsonl_records(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️ Final summary skipped invalid JSONL line {line_no}: {e}")
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _format_percent(count: int, total: int) -> str:
    if total <= 0:
        return "0.00%"
    return f"{(count / total) * 100:.2f}%"


def _collect_final_summary(synthesis_path, replacement_counts):
    records = _load_jsonl_records(synthesis_path)
    total_samples = len(records)

    topic_counter = Counter()
    fusion_count = 0
    for record in records:
        topic = record.get("topic")
        topic_name = str(topic).strip() if topic not in (None, "") else "Unknown"
        topic_counter[topic_name] += 1
        if _normalize_is_fusion(record.get("is_fusion", False)):
            fusion_count += 1

    general_count = total_samples - fusion_count
    top_topics = topic_counter.most_common(8)

    return {
        "replacement_counts": {
            "topic": int(replacement_counts.get("topic", 0)),
            "domain": int(replacement_counts.get("domain", 0)),
            "theme": int(replacement_counts.get("theme", 0)),
        },
        "total_samples": total_samples,
        "top_topics": [
            {
                "topic": topic,
                "count": count,
                "ratio": _format_percent(count, total_samples),
            }
            for topic, count in top_topics
        ],
        "fusion_count": fusion_count,
        "fusion_ratio": _format_percent(fusion_count, total_samples),
        "general_count": general_count,
        "general_ratio": _format_percent(general_count, total_samples),
    }


def _print_final_summary(summary):
    replacement_counts = summary["replacement_counts"]
    print("📊 [ANDES Final Summary]")
    print(
        "1. World tree replacements | "
        f"topic: {replacement_counts['topic']} | "
        f"domain: {replacement_counts['domain']} | "
        f"theme: {replacement_counts['theme']}"
    )

    top_topics = summary["top_topics"]
    if top_topics:
        topic_parts = [f"{item['topic']} ({item['ratio']})" for item in top_topics]
        print("2. Top-8 topics after refine | " + " | ".join(topic_parts))
    else:
        print("2. Top-8 topics after refine | None")

    print(
        "3. Final refine data mix | "
        f"fusion: {summary['fusion_count']}/{summary['total_samples']} ({summary['fusion_ratio']}) | "
        f"general: {summary['general_count']}/{summary['total_samples']} ({summary['general_ratio']})"
    )


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
        """Expand crowded topic subtree; avoid overlap with tag_history."""
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
            cleaned_response = response.replace('```python', '').replace('```json', '').replace('```', '').strip()
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
        """Weighted topic sample, optional taxonomy expansion, LLM suitability triage, fusion flags."""
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

        themes_list_str = "\n".join([f"{i}. {item['theme']} (from {item['topic']})" for i, item in enumerate(sampled_items)])

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
            start = response.find('{')
            end = response.rfind('}') + 1
            categorization = ast.literal_eval(response[start:end])

            strong_indices = categorization.get("Strong", [])
            ambiguous_indices = categorization.get("Ambiguous", [])
            weak_indices = categorization.get("Weak", [])

            for idx in strong_indices:
                t = sampled_items[idx]["topic"]
                self.tag_weights[t] *= self.reward_factor

            for idx in weak_indices:
                t = sampled_items[idx]["topic"]
                self.tag_weights[t] = max(0.1, self.tag_weights[t] * self.decay_factor)

            top_topics = sorted(self.tag_weights.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"📈 [RL Feedback] Top sampling weights: {[(k, round(v, 2)) for k, v in top_topics]}")

            suitable_indices = set(strong_indices)
            for idx in ambiguous_indices:
                if random.random() < 0.8:
                    suitable_indices.add(idx)

            print(f"📊 [Router Classification] Strong: {len(strong_indices)}, Ambiguous: {len(ambiguous_indices)}, Weak: {len(weak_indices)}")

        except Exception as e:
            print(f"⚠️ Router parse failed; falling back to random split: {e}")
            suitable_indices = set(random.sample(range(batch_size), k=batch_size // 2))

        configs = []
        for idx, item in enumerate(sampled_items):
            is_fusion = (idx in suitable_indices)
            config = {
                "topic": item["topic"],
                "domain": item["domain"],
                "theme": item["theme"],
                "is_fusion": is_fusion,
                "description": description,
            }
            if format_requirement is not None:
                config["format_requirement"] = format_requirement
            configs.append(config)

        fusion_count = sum(1 for c in configs if c["is_fusion"])
        print(f"🔀 [Router Result] Batch size: {batch_size} | Domain Fusion: {fusion_count} | Standard Generation: {batch_size - fusion_count}")

        return configs


class ANDESAgentTool:
    """End-to-end pipeline: router -> generator -> refiner.

    A single instance is reusable across multiple ``__call__`` invocations as
    long as the same model / endpoint applies. The caller is responsible for
    persisting the returned synthesis and report paths.
    """

    _DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_url=None, model_name="gpt-4o", max_workers=8):
        cache_dir = os.path.abspath(ANDES_CACHE_DIR)
        os.makedirs(cache_dir, exist_ok=True)
        self.storage = FileStorage(
            first_entry_file_name="",
            cache_path=cache_dir,
            file_name_prefix="andes_cache_step",
            cache_type="jsonl",
        )
        self.llm_serving = APILLMServing_request(
            api_url=api_url or self._DEFAULT_API_URL,
            model_name=model_name,
            max_workers=max_workers,
        )
        self.prompt_template = ANDESFusionPrompt()
        self.tag_manager = DynamicTagManager(self.prompt_template, self.llm_serving)
        self.generator = ANDESGenerator(llm_serving=self.llm_serving, prompt_template=self.prompt_template)
        self.refiner = ANDESRefiner(llm_serving=self.llm_serving, prompt_template=ANDESRefinePrompt())

    def __call__(
        self,
        task_description: str,
        num_samples: int,
        format_requirement: str = None,
        run_stamp: Optional[str] = None,
    ):
        stamp = run_stamp or _andes_run_stamp()
        resolved_format_requirement = resolve_format_requirement(format_requirement)
        print(f"Task: {task_description}")
        if resolved_format_requirement is not None:
            print(f"Format requirement: {resolved_format_requirement}")

        total_prompts = max(1, num_samples // 3)
        router_batch_size = 5
        all_configs = []

        print(f"🔄 [ANDES Router] Sliding-window routing; {total_prompts} nodes to process...")

        for i in range(0, total_prompts, router_batch_size):
            current_batch = min(router_batch_size, total_prompts - i)
            print(f"   -> 📡 Routing nodes {i+1}–{i+current_batch}...")
            batch_configs = self.tag_manager.sample_and_route_batch(
                description=task_description,
                batch_size=current_batch,
                format_requirement=resolved_format_requirement
            )
            all_configs.extend(batch_configs)

        print(f"✅ Routing done; {len(all_configs)} generation configs.")

        print("⚙️ [ANDES Engine] Starting generation...")
        self.generator.run(
            storage=self.storage.step(),
            input_configs=all_configs,
        )

        print("🔍 [ANDES Refiner] Running refinement...")
        agent_report = self.refiner.run(
            storage=self.storage.step(),
            input_instruction_key='instruction',
            input_output_key='output'
        )

        print("🎉 Generation and refinement finished for this batch.")

        cache_dir = os.path.abspath(ANDES_CACHE_DIR)
        os.makedirs(cache_dir, exist_ok=True)

        step2_name = f"{self.storage.file_name_prefix}_step2.{self.storage.cache_type}"
        step2_path = os.path.join(self.storage.cache_path, step2_name)
        step2_path = os.path.normpath(os.path.abspath(step2_path))
        synthesis_path = os.path.join(cache_dir, f"andes_synthesis_{stamp}.{self.storage.cache_type}")
        synthesis_path = os.path.normpath(os.path.abspath(synthesis_path))

        if not os.path.isfile(step2_path):
            print(f"❌ Expected synthesis file missing: {step2_path}")
            return None, None

        shutil.copy2(step2_path, synthesis_path)
        print(f"📦 Synthesis saved to: {synthesis_path}")

        final_summary = _collect_final_summary(
            synthesis_path=synthesis_path,
            replacement_counts=self.tag_manager.replacement_counts,
        )

        report_path: Optional[str] = None
        if isinstance(agent_report, dict) and "logic_diversity_analysis" in agent_report:
            body = agent_report["logic_diversity_analysis"]
            if not isinstance(body, str):
                body = str(body)
            report_path = os.path.join(cache_dir, f"andes_report_{stamp}.txt")
            report_path = os.path.normpath(os.path.abspath(report_path))
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"📝 Report saved to: {report_path}")
        else:
            print("❌ agent_report has no logic_diversity_analysis; no report file written.")

        _print_final_summary(final_summary)

        return synthesis_path, report_path


def _load_agent_tool_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)

    required = ("api_url", "task_description", "format_requirement", "num_samples")
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"config missing required keys: {', '.join(missing)}")

    return cfg


def _run_with_log_redirection(log_file, fn):
    """Redirect stdout/stderr to log_file; real stdout stays for the analysis path only."""
    os.makedirs(os.path.dirname(os.path.abspath(log_file)) or ".", exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as log_fp:
        old_out, old_err = sys.stdout, sys.stderr

        class _StreamRedirect:
            __slots__ = ("_fp",)

            def __init__(self, fp):
                self._fp = fp

            def write(self, data):
                self._fp.write(data)
                self._fp.flush()

            def flush(self):
                self._fp.flush()

        redir = _StreamRedirect(log_fp)
        sys.stdout = redir
        sys.stderr = redir
        try:
            return fn()
        finally:
            sys.stdout = old_out
            sys.stderr = old_err


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Run the ANDES end-to-end pipeline from a JSON config. "
            "Stdout prints two lines on success: the synthesis file path and the report file path. "
            f"Artifacts are written under {ANDES_CACHE_DIR} as "
            "andes_synthesis_<stamp>.jsonl, andes_report_<stamp>.txt, andes_log_<stamp>.txt. "
            "See examples/config.example.json for the expected schema."
        )
    )
    parser.add_argument(
        "config",
        help=(
            "Path to a JSON config. Required keys: api_url, task_description, "
            "format_requirement, num_samples. See examples/config.example.json."
        ),
    )
    args = parser.parse_args()

    cfg = _load_agent_tool_config(args.config)
    stamp = _andes_run_stamp()
    log_path = os.path.join(ANDES_CACHE_DIR, f"andes_log_{stamp}.txt")

    def _job():
        tool = ANDESAgentTool(
            api_url=cfg["api_url"],
            model_name=cfg.get("model_name", "gpt-4o"),
            max_workers=int(cfg.get("max_workers", 8)),
        )
        return tool(
            task_description=cfg["task_description"],
            num_samples=int(cfg["num_samples"]),
            format_requirement=cfg["format_requirement"],
            run_stamp=stamp,
        )

    result = _run_with_log_redirection(log_path, _job)

    if not result or not isinstance(result, tuple):
        print("Run failed: unexpected tool return.", file=sys.stderr)
        sys.exit(1)

    data_path, report_path = result
    if not data_path:
        print("Run failed: synthesis file was not produced.", file=sys.stderr)
        sys.exit(1)
    if not report_path:
        print("Run failed: report file was not written.", file=sys.stderr)
        sys.exit(1)

    print(data_path)
    print(report_path)
