import logging
from question_generator import QuestionGenerator, CodeQuestionGenerator
import os
from files.prompt import question_generation_prompt, question_code_generation_prompt
from dotenv import load_dotenv
from openai import OpenAI
from settings import settings

def load_llm(model_name: str) -> OpenAI:
    load_dotenv()
    if "gemini" in model_name:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            logger.error("Gemini API key not found in environment variables.")
            raise EnvironmentError("Gemini API key not set in environment.")
        logger.info("Successfully loaded Gemini API key.")
        return OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=600,
            max_retries=3,
        )
    else:
        raise ValueError("Invalid model name selected.")

if __name__ == "__main__":
    model_name = settings.model_name
    prompt_type = settings.prompt_type
    output_file = settings.output_file
    logger_file = settings.logger_file
    LOG_DIR = "logs"
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, logger_file),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting question generation process.")
    
    llm = load_llm(model_name=model_name)
    
    if prompt_type == "question_generation":
        prompt = question_generation_prompt
        # 初始化生成器
        generator = QuestionGenerator(logger=logger, prompt=prompt, llm=llm)
    elif prompt_type == "code_generation":
        prompt = question_code_generation_prompt
        generator = CodeQuestionGenerator(logger=logger, prompt=prompt, llm=llm)
    else:
        logger.error("Invalid prompt type selected.")
        raise ValueError("Invalid prompt type selected.")

    logger.info("Using prompt type: %s", prompt_type)
    logger.info("Using model: %s", model_name)
    
    try:
        # 加载文档数据
        doc_file_path = "files/documents_llm_doc_gemini_20_flash_full.json"
        docs = generator.load_pymatgen_doc(doc_file_path)

        # 设置模型参数
        model_args = {
            "model": model_name,
            "temperature": 0.7,
        }

        # 处理文档，生成问题
        results = generator.process_documents(docs, model_args)

        # 存储结果
        generator.store_result(results, output_file=output_file)

        logger.info("Question generation process completed successfully.")
        print(f"Question generation completed. Results saved to {output_file}.")

    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        print("An error occurred. Check logs for details.")