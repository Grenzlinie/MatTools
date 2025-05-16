import json
import logging
import os
import csv
from openai import OpenAI
from dotenv import load_dotenv
from files.prompt import question_test_prompt
from settings import test_settings

class LLMEvaluator:
    def __init__(self, model_args, logger, model_type):
        self.logger = logger
        self.llm = self.load_llm(model_args["model"], model_type)
        self.model_args = model_args
        
    def load_llm(self, model_name: str, model_type: str) -> OpenAI:
        load_dotenv()
        if model_type == "remote":
            if "gemini" in model_name:
                gemini_key = os.getenv("GEMINI_API_KEY")
                if not gemini_key:
                    self.logger.error("Gemini API key not found in environment variables.")
                    raise EnvironmentError("Gemini API key not set in environment.")
                self.logger.info("Successfully loaded Gemini API key.")
                return OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    timeout=600,
                    max_retries=3,
                )
            elif "deepseek" in model_name:
                deepseek_key = os.getenv("DEEPSEEK_API_KEY")
                if not deepseek_key:
                    self.logger.error("DeepSeek API key not found in environment variables.")
                    raise EnvironmentError("DeepSeek API key not set in environment.")
                self.logger.info("Successfully loaded DeepSeek API key.")
                return OpenAI(
                    api_key=deepseek_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    timeout=600,
                    max_retries=3,
                )
            else:
                raise ValueError("Invalid model name selected.")
        elif model_type == "local":
            client = OpenAI(
                base_url="http://localhost:8000/v1",
                api_key="token-abc123",
                timeout=600,
                max_retries=3,
            )
            self.logger.info("Successfully loaded local LLM.")
            return client
        else:
            raise ValueError("Invalid model name selected.")

    def ask_llm(self, question_prompt: str) -> str:
        """向 LLM 发送格式化后的问题并获取答案"""
        response = self.llm.chat.completions.create(
            messages=[{"role": "user", "content": question_prompt}],
            **self.model_args
        )
        return response.choices[0].message.content.strip()

    def evaluate_questions(self, json_file: str, csv_store_name: str):
        """评估所有问题并记录结果"""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = {}
        csv_results = []
        total_correct = 0
        total_questions = 0

        for item in data:
            source_name = item["source"]["metadata"]["code_source_file"] + "/" + item["source"]["metadata"]["name"]
            if source_name not in results:
                results[source_name] = {"correct": 0, "incorrect": 0, "total": 0}

            for question_data in item["questions"]:
                question = question_data["question"]
                correct_answer = question_data["correct_answer"]
                first_choice = question_data["choices"]['A']
                second_choice = question_data["choices"]['B']
                third_choice = question_data["choices"]['C']
                fourth_choice = question_data["choices"]['D']

                # 生成格式化的问题
                formatted_question = question_test_prompt.format(
                    question=question,
                    first_choice=first_choice,
                    second_choice=second_choice,
                    third_choice=third_choice,
                    fourth_choice=fourth_choice,
                )

                # 发送到 LLM 获取答案
                llm_answer = self.ask_llm(formatted_question)

                # 解析 LLM 的回答，只提取 <answer> 标签中的内容
                extracted_answer = llm_answer.strip().replace("<answer>", "").replace("</answer>", "").strip()

                # 评估是否正确
                is_correct = extracted_answer == correct_answer

                results[source_name]["total"] += 1
                total_questions += 1
                if is_correct:
                    results[source_name]["correct"] += 1
                    total_correct += 1
                else:
                    results[source_name]["incorrect"] += 1

                # 记录日志
                logging.info(f"Question: {question}")
                logging.info(f"LLM Answer: {extracted_answer}")
                logging.info(f"Correct Answer: {correct_answer}")
                logging.info(f"Result: {'✔ Correct' if is_correct else '❌ Incorrect'}\n")

            # 计算正确率
            accuracy = (results[source_name]["correct"] / results[source_name]["total"]) * 100
            csv_results.append([source_name, results[source_name]["total"], results[source_name]["correct"],
                                results[source_name]["incorrect"], f"{accuracy:.2f}%"])
        
        # 计算整体成功率
        overall_accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        logging.info(f"Overall Accuracy: {overall_accuracy:.2f}%")
        print(f"Overall Accuracy: {overall_accuracy:.2f}%")
        
        # 保存到 CSV
        csv_filename = f"files/{csv_store_name}"
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Source", "Total Questions", "Correct Answers", "Incorrect Answers", "Accuracy"])
            csv_writer.writerows(csv_results)
            csv_writer.writerow(["Overall", total_questions, total_correct, total_questions - total_correct, f"{overall_accuracy:.2f}%"])

        logging.info(f"Results saved to {csv_filename}")
        print(f"Results saved to {csv_filename}")

if __name__ == "__main__":
    model_name = test_settings.model_name
    model_type = test_settings.model_type
    test_file_path = test_settings.test_file_path
    logger_file = test_settings.logger_file
    csv_filename = test_settings.csv_filename
    
    # 设置日志
    log_filename = f"logs/{logger_file}"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(asctime)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Starting question generation process.")
    
    # 设置模型参数
    model_args = {
        "model": model_name,
        "temperature": 0.7,
    }
    
    evaluator = LLMEvaluator(model_args, logger, model_type)
    evaluator.evaluate_questions(json_file=f"../../generated_qa/{test_file_path}", csv_store_name=csv_filename)
