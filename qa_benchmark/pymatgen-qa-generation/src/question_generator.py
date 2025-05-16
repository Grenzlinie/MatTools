from abc import ABC, abstractmethod
import json
import re
from openai import OpenAI

class BaseQuestionGenerator(ABC):
    
    def __init__(self, logger, prompt: str, llm: OpenAI = None):
        if logger is None:
            raise ValueError("Logger must be provided and cannot be None.")
        self.logger = logger
        self.prompt = prompt
        self.llm = llm
        self.logger.info("Initialized BaseQuestionGenerator.")

    def load_pymatgen_doc(self, file_path: str) -> list:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            self.logger.info(f"Loaded {len(data)} documents from {file_path}.")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load document file {file_path}: {e}", exc_info=True)
            raise

    def check_answer(self, answer: str):
        try:
            extracted_data = []
            question_blocks = re.findall(
                r"<question(\d+)>(.*?)</question\1>.*?<answer_choices\1>(.*?)</answer_choices\1>.*?<correct_answer\1>(.*?)</correct_answer\1>",
                answer,
                re.DOTALL
            )

            for block in question_blocks:
                question_id, question_text, choices_text, correct_answer = block

                choices = re.findall(r"<choice>(.*?)</choice>", choices_text, re.DOTALL)
                choices = [choice.strip() for choice in choices]

                if len(choices) != 4 or correct_answer.strip() not in ["A", "B", "C", "D"]:
                    self.logger.warning(f"Invalid answer format detected in question {question_id}.")
                    return False, None

                extracted_data.append({
                    "question_id": question_id,
                    "question": question_text.strip(),
                    "choices": {
                        "A": choices[0],
                        "B": choices[1],
                        "C": choices[2],
                        "D": choices[3]
                    },
                    "correct_answer": correct_answer.strip()
                })

            if not extracted_data:
                self.logger.warning("No valid questions extracted from the answer.")
                return False, None

            self.logger.info(f"Successfully validated {len(extracted_data)} questions.")
            return True, extracted_data
        except Exception as e:
            self.logger.error(f"Error while checking answer format: {e}", exc_info=True)
            return False, None    

    def store_result(self, result: list, output_file: str):
        try:
            with open(output_file, "w") as file:
                json.dump(result, file, indent=4)
            self.logger.info(f"Results successfully stored in {output_file}.")
        except Exception as e:
            self.logger.error(f"Failed to store results: {e}", exc_info=True)
            raise
    
    @abstractmethod
    def process_documents(self, docs: list, model_args: dict):
        pass
    
    @abstractmethod
    def generate_question(self, doc_segment: str, model_args: dict) -> str:
        pass

class QuestionGenerator(BaseQuestionGenerator):

    def generate_question(self, doc_segment: str, model_args: dict) -> str:
        message = self.prompt.format(Document=doc_segment)
        try:
            response = self.llm.chat.completions.create(
                messages=[{"role": "user", "content": message}],
                **model_args
            )
            self.logger.info("Generated question successfully.")
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Failed to generate question: {e}", exc_info=True)
            raise

    def process_documents(self, docs: list, model_args: dict):
        qa_result = []
        for idx, doc in enumerate(docs):
            doc_segment = "Code Source File: " + doc['metadata']['code_source_file'] + "\n\n" + "Document: \n" + doc["page_content"]
            max_retries = 3
            retry_count = 0
            is_valid = False
            data = None

            self.logger.info(f"Processing document {idx+1}/{len(docs)}: {doc['metadata']['code_source_file']}")

            while retry_count < max_retries and not is_valid:
                try:
                    question = self.generate_question(doc_segment, model_args)
                    is_valid, data = self.check_answer(question)
                    if not is_valid:
                        self.logger.warning(f"Invalid question format on attempt {retry_count + 1}")
                except Exception as e:
                    self.logger.error(f"Error generating question for document {idx+1}: {e}", exc_info=True)
                retry_count += 1

            if is_valid:
                qa_result.append({
                    "source": doc,
                    "questions": data
                })
                self.logger.info(f"Successfully generated valid questions for document {idx+1}.")
            else:
                self.logger.warning(f"Failed to generate valid questions for document {idx+1} after {max_retries} retries.")

        return qa_result
        


class CodeQuestionGenerator(BaseQuestionGenerator):

    def generate_question(self, code_source_file:str, code_segment: str, model_args: dict) -> str:
        message = self.prompt.format(CodeSourceFile=code_source_file, CodeSnippet=code_segment)
        try:
            response = self.llm.chat.completions.create(
                messages=[{"role": "user", "content": message}],
                **model_args
            )
            self.logger.info("Generated question successfully.")
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Failed to generate question: {e}", exc_info=True)
            raise

    def process_documents(self, docs: list, model_args: dict):
        qa_result = []
        for idx, doc in enumerate(docs):
            code_source_file = doc['metadata']['code_source_file']
            code_segment = doc["metadata"]["code_content"]
            max_retries = 3
            retry_count = 0
            is_valid = False
            data = None

            self.logger.info(f"Processing document {idx+1}/{len(docs)}: {doc['metadata']['code_source_file']}")

            while retry_count < max_retries and not is_valid:
                try:
                    question = self.generate_question(code_source_file, code_segment, model_args)
                    is_valid, data = self.check_answer(question)
                    if not is_valid:
                        self.logger.warning(f"Invalid question format on attempt {retry_count + 1}")
                except Exception as e:
                    self.logger.error(f"Error generating question for document {idx+1}: {e}", exc_info=True)
                retry_count += 1

            if is_valid:
                qa_result.append({
                    "source": doc,
                    "questions": data
                })
                self.logger.info(f"Successfully generated valid questions for document {idx+1}.")
            else:
                self.logger.warning(f"Failed to generate valid questions for document {idx+1} after {max_retries} retries.")

        return qa_result