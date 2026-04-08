import json
import random
import re
from collections import Counter
from andes.utils.registry import OPERATOR_REGISTRY
from andes import get_logger
from andes.core import OperatorABC
from andes.utils.storage import DataFlowStorage
from andes.core import LLMServingABC
from andes.prompts.andes_prompts import ANDESRefinePrompt
from andes.core.prompt import prompt_restrict, DIYPromptABC
from typing import Union

@prompt_restrict(
    ANDESRefinePrompt
)
@OPERATOR_REGISTRY.register()
class ANDESRefiner(OperatorABC):
    def __init__(self, llm_serving: LLMServingABC = None, prompt_template: Union[ANDESRefinePrompt, DIYPromptABC] = None):
        self.logger = get_logger()
        self.logger.info(f'Initializing {self.__class__.__name__}...')
        self.llm_serving = llm_serving
        self.prompt_template = prompt_template
        self.logger.info(f'{self.__class__.__name__} initialized.')
    
    @staticmethod
    def get_desc(lang: str = "zh"):
        pass

    def generate_critique(self, question, answer, is_fusion, topic, domain, theme, description, format_requirement=None):
        if format_requirement is None:
            format_requirement = [None] * len(question)
        critique_prompts = [
            self.prompt_template.build_prompt(
                mode="critique", 
                question=q, 
                answer=a,
                is_fusion=f,
                topic=t,
                domain=d,
                theme=th,
                description=desc,
                format_requirement=fmt,
            ) 
            for q, a, f, t, d, th, desc, fmt in zip(question, answer, is_fusion, topic, domain, theme, description, format_requirement)
        ]
        critique_responses = self.llm_serving.generate_from_input(critique_prompts)
        return critique_responses

    @staticmethod
    def _parse_logic_diversity_json(res: str) -> tuple[str, str, str]:
        """Parse batch audit from JSON only (no regex on free-form layout)."""
        text = (res if isinstance(res, str) else "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return "MEDIUM", "Batch JSON parse failed.", ""

        level_raw = str(obj.get("collapse_level", obj.get("Collapse Level", ""))).strip().upper()
        if level_raw not in ("LOW", "MEDIUM", "HIGH"):
            level = "MEDIUM"
        else:
            level = level_raw

        pattern = str(obj.get("core_pattern", obj.get("Core Pattern", ""))).strip()
        evidence = str(obj.get("evidence", obj.get("Evidence", ""))).strip()
        if not pattern:
            pattern = "Pattern not explicitly provided."
        if not evidence:
            evidence = "Evidence not explicitly provided."
        return level, pattern, evidence

    def _summarize_cross_batch_patterns(self, batch_reports: list) -> str:
        """One LLM call: condense per-batch pattern/evidence into common recurring patterns."""
        lines = []
        for i, r in enumerate(batch_reports, start=1):
            lines.append(
                f"Batch {i} | Collapse Level: {r['level']} | "
                f"Core Pattern: {r['pattern']} | Evidence: {r.get('evidence', '')}"
            )
        block = "\n".join(lines)
        prompt = self.prompt_template._build_logic_diversity_cross_batch_prompt(block)
        try:
            out = self.llm_serving.generate_from_input([prompt])[0]
            return (out or "").strip() or "Cross-batch pattern summary unavailable."
        except Exception as e:
            self.logger.warning(f"Cross-batch pattern summarization failed: {e}")
            return "Cross-batch pattern summary unavailable (API error)."

    def _evaluate_logic_diversity(
        self, questions, answers, descriptions, topics, domains, themes, sample_size=25, coverage_fraction=0.2
    ):
        """Scenario-collapse audit: mini-batches cover ~coverage_fraction of the fusion pool (cap sample_size each)."""
        total = len(questions)
        if total == 0:
            return "No samples available for diversity analysis."

        num_batches = max(1, round(total * coverage_fraction / sample_size))

        all_indices = list(range(total))
        remaining_indices = all_indices[:]
        random.shuffle(remaining_indices)
        batch_reports = []
        sampled_count = 0
        sampled_unique_indices = set()

        for _ in range(num_batches):
            if not remaining_indices:
                remaining_indices = all_indices[:]
                random.shuffle(remaining_indices)

            current_batch_size = min(sample_size, total)
            batch_indices = remaining_indices[:current_batch_size]
            remaining_indices = remaining_indices[current_batch_size:]
            if not batch_indices:
                continue

            sampled_count += len(batch_indices)
            sampled_unique_indices.update(batch_indices)

            shared_desc = next(
                (str(descriptions[i]).strip() for i in batch_indices if descriptions[i] and str(descriptions[i]).strip()),
                "",
            )

            batch = [{
                "topic": str(topics[i]) if topics[i] else "Unknown",
                "domain": str(domains[i]) if domains[i] else "Unknown",
                "theme": str(themes[i]) if themes[i] else "Unknown",
                "description": str(descriptions[i]) if descriptions[i] else "",
                "instruction": str(questions[i]),
                "output": str(answers[i])
            } for i in batch_indices]
            if shared_desc:
                task_scope_block = (
                    "Task scope (one Target Description for this batch; required alignment, not a diversity defect):\n"
                    f"---\n{shared_desc}\n---\n"
                )
            else:
                task_scope_block = "No Target Description in this batch; infer task from Topic/Domain/Theme and samples below.\n"

            examples = []
            for j, item in enumerate(batch, start=1):
                examples.append(
                    f"[Sample {j}]\n"
                    f"Topic/Domain/Theme: {item['topic']} / {item['domain']} / {item['theme']}\n"
                    f"Instruction: {item['instruction']}\n"
                    f"Output: {item['output']}\n"
                )
            prompt = self.prompt_template._build_logic_diversity_batch_prompt(
                task_scope_block, "\n".join(examples)
            )
            try:
                res = self.llm_serving.generate_from_input([prompt])[0]
                level, pattern, evidence = self._parse_logic_diversity_json(res)
                batch_reports.append({"level": level, "pattern": pattern, "evidence": evidence})
            except Exception as e:
                self.logger.warning(f"Logic diversity batch analysis failed: {e}")
                batch_reports.append({"level": "MEDIUM", "pattern": "Batch analysis fallback due to parsing/API issue.", "evidence": ""})

        if not batch_reports:
            return "Diversity analysis did not produce valid batches."

        level_counter = Counter([r["level"] for r in batch_reports])
        high_ratio = round(level_counter.get("HIGH", 0) / len(batch_reports), 4)
        medium_ratio = round(level_counter.get("MEDIUM", 0) / len(batch_reports), 4)
        patterns_summary = self._summarize_cross_batch_patterns(batch_reports)
        overall_level = "LOW"
        if high_ratio >= 0.5:
            overall_level = "HIGH"
        elif high_ratio >= 0.2 or (high_ratio + medium_ratio) >= 0.5:
            overall_level = "MEDIUM"

        analysis_text = (
            f"Scenario-collapse analysis on {sampled_count} sampled items "
            f"({len(sampled_unique_indices)} unique fusion items): "
            f"overall collapse level is {overall_level}. "
            f"Collapse-level shares => HIGH: {high_ratio:.2%}, MEDIUM: {medium_ratio:.2%}, "
            f"LOW: {1 - high_ratio - medium_ratio:.2%}. "
            f"Cross-batch common patterns (LLM-merged): {patterns_summary}"
        )
        return analysis_text

    def parse_and_summarize_critiques(self, critique_responses, is_fusion_list, topic_list, domain_list, theme_list, questions, answers, descriptions):
        """Build agent report: fusion tag stats, effort scores, logic-diversity text."""
        effort_scores = []
        tag_counter = Counter()

        total_samples = len(is_fusion_list)
        domain_count = sum(is_fusion_list)
        general_count = total_samples - domain_count

        for idx, (critique, is_fusion) in enumerate(zip(critique_responses, is_fusion_list)):
            if not is_fusion:
                continue

            t = topic_list[idx] if topic_list[idx] else "Unknown"
            d = domain_list[idx] if domain_list[idx] else "Unknown"
            th = theme_list[idx] if theme_list[idx] else "Unknown"
            tag_counter[f"{t} -> {d} -> {th}"] += 1

            e_match = re.search(r'\[Effort Score Start\](.*?)\[Effort Score End\]', critique, flags=re.DOTALL)
            if e_match:
                score_str = e_match.group(1).strip()
                digit_match = re.search(r'\d', score_str)
                if digit_match:
                    effort_scores.append(int(digit_match.group(0)))
                else:
                    effort_scores.append(0)

        fusion_indices = [i for i, f in enumerate(is_fusion_list) if f]
        if fusion_indices:
            logic_diversity_summary = self._evaluate_logic_diversity(
                questions=[questions[i] for i in fusion_indices],
                answers=[answers[i] for i in fusion_indices],
                descriptions=[descriptions[i] for i in fusion_indices],
                topics=[topic_list[i] for i in fusion_indices],
                domains=[domain_list[i] for i in fusion_indices],
                themes=[theme_list[i] for i in fusion_indices],
            )
        else:
            logic_diversity_summary = "No fusion samples in this batch; scenario-collapse analysis skipped."

        report = {
            "synthesis_counts": {
                "total_samples": total_samples,
                "general_data_count": general_count,
                "domain_data_count": domain_count
            },
            "domain_tag_distribution": dict(tag_counter),
            "effort_score_distribution": dict(Counter(effort_scores)),
            "logic_diversity_analysis": logic_diversity_summary
        }
        
        return report

    def _extract_effort_scores(self, critique_responses):
        """Extract 1-5 effort scores from critique responses."""
        effort_scores = []
        for critique in critique_responses:
            e_match = re.search(r'\[Effort Score Start\](.*?)\[Effort Score End\]', critique, flags=re.DOTALL)
            if not e_match:
                effort_scores.append(0)
                continue

            score_str = e_match.group(1).strip()
            digit_match = re.search(r'\d', score_str)
            effort_scores.append(int(digit_match.group(0)) if digit_match else 0)
        return effort_scores

    def generate_refined_answer(self, question, answer, critique, topic, domain, theme, description, format_requirement=None):
        if format_requirement is None:
            format_requirement = [None] * len(question)
        refine_prompts = [
            self.prompt_template.build_prompt(
                mode="refine", 
                question=q, 
                answer=a, 
                critique=c,
                topic=t,
                domain=d,
                theme=th,
                description=desc,
                format_requirement=fmt,
            ) 
            for q, a, c, t, d, th, desc, fmt in zip(question, answer, critique, topic, domain, theme, description, format_requirement)
        ]
        refined_answers = self.llm_serving.generate_from_input(refine_prompts)
        refined_answers = [ans.replace('[Improved Answer Start]', '').replace('[Improved Answer End]', '').strip() for ans in refined_answers]
        return refined_answers

    def run(self, storage: DataFlowStorage, input_instruction_key: str='instruction', input_output_key: str='output'):
        df = storage.read('dataframe')
        questions = df.get(input_instruction_key).to_list()
        answers = df.get(input_output_key).to_list()
        is_fusion = df['is_fusion'].to_list() if 'is_fusion' in df.columns else [False] * len(df)
        topic = df['topic'].to_list() if 'topic' in df.columns else [None] * len(df)
        domain = df['domain'].to_list() if 'domain' in df.columns else [None] * len(df)
        theme = df['theme'].to_list() if 'theme' in df.columns else [None] * len(df)
        description = df['description'].to_list() if 'description' in df.columns else [None] * len(df)
        format_requirement = df['format_requirement'].to_list() if 'format_requirement' in df.columns else [None] * len(df)

        # Step 1: Generate Critiques
        critique_responses = self.generate_critique(questions, answers, is_fusion, topic, domain, theme, description, format_requirement)
        self.logger.info(f'Generated Critiques for the answers.')

        # Step 2: Extract Effort Scores
        effort_scores = self._extract_effort_scores(critique_responses)
        keep_indices = [idx for idx, score in enumerate(effort_scores) if score <= 4]
        drop_count = len(effort_scores) - len(keep_indices)
        if drop_count > 0:
            self.logger.info(f'Dropping {drop_count} samples with effort score > 4 before refinement.')

        # Step 3: Filter Samples by Effort Score
        if not keep_indices:
            self.logger.warning('All samples were filtered out by effort score > 4.')
            empty_df = df.iloc[0:0].copy()
            storage.write(empty_df)
            agent_report = self.parse_and_summarize_critiques(
                critique_responses, is_fusion, topic, domain, theme, questions, answers, description
            )
            return agent_report

        filtered_df = df.iloc[keep_indices].reset_index(drop=True)
        questions = [questions[i] for i in keep_indices]
        answers = [answers[i] for i in keep_indices]
        is_fusion = [is_fusion[i] for i in keep_indices]
        topic = [topic[i] for i in keep_indices]
        domain = [domain[i] for i in keep_indices]
        theme = [theme[i] for i in keep_indices]
        description = [description[i] for i in keep_indices]
        format_requirement = [format_requirement[i] for i in keep_indices]
        critique_responses = [critique_responses[i] for i in keep_indices]

        # Step 4: Parse and Summarize Critiques
        self.logger.info(f'Extracting stats and generating Agent Synthesis Report...')
        agent_report = self.parse_and_summarize_critiques(
            critique_responses, is_fusion, topic, domain, theme, questions, answers, description
        )

        # Step 5: Generate Refined Answers
        refined_answers = self.generate_refined_answer(questions, answers, critique_responses, topic, domain, theme, description, format_requirement)
        self.logger.info(f'Refined Answers generated.')
        
        filtered_df[input_output_key] = refined_answers
        storage.write(filtered_df)
        self.logger.info(f'Refined answers updated in storage.')

        return agent_report
