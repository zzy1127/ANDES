import random
import re
from andes.utils.registry import OPERATOR_REGISTRY
from andes import get_logger
from andes.core import OperatorABC
from andes.utils.storage import DataFlowStorage
import pandas as pd
from andes.core import LLMServingABC
from andes.prompts.andes_prompts import ANDESFusionPrompt
from andes.core.prompt import DIYPromptABC, prompt_restrict
from typing import Union

@prompt_restrict(
    ANDESFusionPrompt
) 

@OPERATOR_REGISTRY.register()
class ANDESGenerator(OperatorABC):
    def __init__(self, llm_serving: LLMServingABC = None, num_samples=15, use_task_diversity=True, prompt_template: Union[ANDESFusionPrompt, DIYPromptABC] = None):
        self.logger = get_logger()
        self.logger.info(f'Initializing {self.__class__.__name__}...')
        self.llm_serving = llm_serving
        self.num_questions = num_samples // 3  
        self.prompt = prompt_template
        self.use_task_diversity = use_task_diversity 
        self.logger.info(f'{self.__class__.__name__} initialized.')
    
    @staticmethod
    def get_desc(lang: str = "zh"):
        pass

    def parse_generated_responses(self, questions_responses):
        questions_data = []
        for response in questions_responses:
            try:
                question_data = {}
                
                easy_match = re.search(r'\[Easy\]\[Question Start\](.*?)\[Question End\]', response, flags=re.DOTALL)
                if easy_match:
                    question_data["Easy"] = easy_match.group(1).strip()
                    
                medium_match = re.search(r'\[Medium\]\[Question Start\](.*?)\[Question End\]', response, flags=re.DOTALL)
                if medium_match:
                    question_data["Medium"] = medium_match.group(1).strip()
                    
                hard_match = re.search(r'\[Hard\]\[Question Start\](.*?)\[Question End\]', response, flags=re.DOTALL)
                if hard_match:
                    question_data["Hard"] = hard_match.group(1).strip()

                if question_data:
                    questions_data.append(question_data)
            except Exception as e:
                self.logger.error(f"Error parsing response: {e}")
                continue
        return questions_data

    def run(self, storage: DataFlowStorage, input_configs: list = None, output_instruction_key: str = "instruction", output_output_key: str = "output", output_difficulty_key: str = "difficulty"):
        """Generate from router configs (topic, domain, theme, is_fusion, description, optional format_requirement)."""
        if not input_configs:
            self.logger.error("No configs provided from the router!")
            return []

        prompts = []
        prompt_metadata = []

        for config in input_configs:
            topic = config.get('topic')
            domain = config.get('domain')
            theme = config.get('theme')
            is_fusion = config.get('is_fusion', False)
            description = config.get('description', '')
            format_requirement = config.get('format_requirement', None)

            prompt = self.prompt.build_prompt(theme=theme, domain=domain, description=description, is_fusion=is_fusion, format_requirement=format_requirement)

            task_type = None
            if self.use_task_diversity and getattr(self.prompt, 'task_types', None):
                task_type = random.choice(self.prompt.task_types)
            if task_type:
                prompt = f"""Task Scenario: {task_type}
                
{prompt}

Remember to frame the questions within the context of "{task_type}" scenario."""
            
            prompts.append(prompt)
            metadata = {
                'topic': topic,
                'domain': domain,
                'theme': theme,
                'task_type': task_type,
                'is_fusion': is_fusion,
                'description': description,
            }
            if format_requirement is not None:
                metadata['format_requirement'] = format_requirement
            prompt_metadata.append(metadata)

        self.logger.info("Generating questions...")
        questions_responses = self.llm_serving.generate_from_input(user_inputs=prompts)

        self.logger.info("Parsing questions...")
        questions_data = self.parse_generated_responses(questions_responses)

        answer_prompts = []
        for idx, question in enumerate(questions_data):
            sample_metadata = prompt_metadata[idx] if idx < len(prompt_metadata) else {}
            is_fusion = sample_metadata.get("is_fusion", False)
            format_requirement = sample_metadata.get("format_requirement")
            for difficulty_level in ["Easy", "Medium", "Hard"]:
                question_text = question.get(difficulty_level)
                if question_text:
                    answer_prompt = f"Please answer this question truthfully. Question: {question_text}"
                    if is_fusion and format_requirement:
                        answer_prompt += f"\n\nYou must strictly follow this output format requirement:\n{format_requirement}"
                    answer_prompts.append(answer_prompt)

        self.logger.info("Generating answers...")
        answer_responses = self.llm_serving.generate_from_input(user_inputs=answer_prompts)

        answers_data = []
        answer_idx = 0
        for idx, question in enumerate(questions_data):
            is_fusion = prompt_metadata[idx].get('is_fusion', False)
            topic = prompt_metadata[idx].get('topic')
            domain = prompt_metadata[idx].get('domain')
            theme = prompt_metadata[idx].get('theme')
            description = prompt_metadata[idx].get('description')
            task_type = prompt_metadata[idx].get('task_type')
            format_requirement = prompt_metadata[idx].get('format_requirement')
            for difficulty_level in ["Easy", "Medium", "Hard"]: 
                question_text = question.get(difficulty_level)
                if question_text:
                    answer_text = answer_responses[answer_idx].strip()
                    answers_data.append({
                        output_difficulty_key: difficulty_level, 
                        output_instruction_key: question_text,
                        output_output_key: answer_text,
                        "is_fusion": is_fusion,
                        "topic": topic,
                        "domain": domain,
                        "theme": theme,
                        "description": description,
                        "task_type": task_type,
                    })
                    if format_requirement is not None:
                        answers_data[-1]["format_requirement"] = format_requirement
                    answer_idx += 1

        df = pd.DataFrame(answers_data)
        storage.write(df)
        self.logger.info(f'SFT data generated')
        
        return [output_instruction_key, output_output_key, output_difficulty_key]
