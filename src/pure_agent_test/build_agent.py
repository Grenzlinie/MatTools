'''
This file is used to build the LLM agents to generate solution and check correctness of results.
'''
import argparse
from datetime import datetime
import json
from openai import OpenAI
from tqdm import tqdm
import sys
sys.path.append("..")
from src.call_llms import load_llm
import os
from typing import List
from mtb_logger import MatToolBenLogger
import re

ANSWER_FORMAT = """**Answer format**:
Please make sure the response is enclosed within `<answer>`, `<code>` and `<name>` tags. Follow this example format:

<answer>
<code>\n```python\n# The generated function code\ndef example_function():\npass\n```\n</code>
<name>name_of_generated_function</name>
</answer>"""

def load_questions_path_from_directories(base_dir: str) -> List[str]:
    """
    Load question file paths from the specified base directory.

    Args:
        base_dir (str): The base directory to search for question files.

    Returns:
        List[str]: A list of file paths to 'question.txt' files found in the directory.
    """
    questions_files_path = [os.path.join(root, 'question.txt') for root, _, files in os.walk(base_dir) if 'question.txt' in files]
    return questions_files_path

def get_answer(client: OpenAI, message: str, model_args: dict) -> str:
    """
    Get the response from the LLM based on the provided message.

    Args:
        client (Any): The LLM client used to get the response.
        message (str): The message to send to the LLM.

    Returns:
        str: The content of the response from the LLM.
    """
    message_to_log = message.replace('\n', ' ')
    mtb_logger.info(f"Model_args: {model_args}")
    mtb_logger.info(f"Message sent to LLM: {message_to_log}")
    message = "\n".join([message, ANSWER_FORMAT])
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": message}],
        **model_args
    )
    processed_response = response.choices[0].message.content.replace('\n', ' ')
    mtb_logger.info(f"Received response from LLM: {processed_response}")
    mtb_logger.info(f"Conversation ID: {response.id} | Created: {response.created} | Model: {response.model} | System Fingerprint: {response.system_fingerprint}")
    mtb_logger.info(f"Usage: {response.usage}")
    return response.choices[0].message.content

def generate_request_bodies(questions_files_path: List[str], model_args: dict) -> List[dict]:
    request_bodies = []
    for index, question_file_path in enumerate(questions_files_path):
        with open(question_file_path, 'r') as file:
            question = file.read().strip()
        question = "\n".join([question, ANSWER_FORMAT])
        request_body = {
            "custom_id": f"task_{index + 1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model_args['model'],
                "messages": [{"role": "user", "content": question}],
                "temperature": model_args["temperature"],
            }
        }
        request_bodies.append(request_body)
        mtb_logger.info(f"Generated request body for question {index + 1}: {request_body}")
    return request_bodies

def evaluate_all_questions(questions_files_path: List[str], llm_name: str, model_args: dict, batch_mode=False) -> List[str]:
    """
    Evaluate all questions by getting responses from the LLM.

    Args:
        questions (List[str]): A list of file paths to question files.

    Returns:
        List[str]: A list of responses from the LLM for each question.
    """
    client = load_llm(llm_name=llm_name)
    mtb_logger.info(f"Total number of questions: {len(questions_files_path)}")
    mtb_logger.info(f"Loaded LLM client: {llm_name}")
    if batch_mode == True and 'gpt' in llm_name:
        mtb_logger.info("Batch mode enabled. Processing all questions.")
        request_bodies = generate_request_bodies(questions_files_path, model_args)
        # Save request_bodies to a JSONL file
        jsonl_file_path = os.path.join(store_path, 'request_bodies.jsonl')
        with open(jsonl_file_path, 'w', encoding='utf-8') as jsonl_file:
            for request_body in request_bodies:
                jsonl_file.write(json.dumps(request_body) + '\n')
        mtb_logger.info(f"Saved request bodies to {jsonl_file_path}")
        batch_file = client.files.create(file=open(jsonl_file_path, "rb"),purpose="batch")
        batch_job = client.batches.create(input_file_id=batch_file.id, endpoint="/v1/chat/completions", completion_window="24h", metadata={"description": f"evaluate questions on model {model_args['model']}"})
        mtb_logger.info(f"Created batch file: {batch_file} | Created batch job: {batch_job} | Batch job ID: {batch_job.id}")
        mtb_logger.info("Please visit the OpenAI official website to view the status.")
        return batch_job.id
    else:   
        llm_responses = []
        for question_file_path in tqdm(questions_files_path, desc="Processing", file=tqdm_logger):
            mtb_logger.info(f"Path to question file: {question_file_path}")
            with open(question_file_path, 'r') as file:
                message = file.read().strip()
            llm_responses.append(get_answer(client, message, model_args))
        mtb_logger.info("All tasks completed successfully.")
        return llm_responses

def extract_response(response: str) -> str:
    """
    Extract the response from the LLM output.

    Args:
        response (str): The response from the LLM.

    Returns:
        str: The extracted response.
    """
    code_match = re.search(r"<code>\s*```python\s*(.*?)```\s*</code>", response, re.DOTALL)
    name_match = re.search(r"<name>(.*?)</name>", response, re.DOTALL)
    if not code_match or not name_match:
        mtb_logger.info(f"Failed to extract response from: {response}")
        return ["", ""]
    else:
        return [code_match.group(1).strip(), name_match.group(1).strip()]

if __name__ == "__main__":
    # replace the model name with the model you want to test
    parser = argparse.ArgumentParser(description='Run LLM evaluation with specified models. Example input: --model_names gpt-4o-mini gpt-3.5-turbo --batch_mode')
    parser.add_argument('--model_names', nargs='+', default=['gpt-4o-mini-2024-07-18'],
                      help='Names of models to evaluate (can specify multiple). Example: gpt-4o-mini gpt-3.5-turbo')
    parser.add_argument('--batch_mode', action='store_true', default=False,
                      help='Enable batch mode processing. Use this flag to process all questions in batch mode.')
    parser.add_argument('--temperature', type=lambda x: max(0, float(x)), default=0.7,
                      help='Temperature setting for the model. Default is 0.7. Minimum value is 0.')
    args = parser.parse_args()
    
    model_names = args.model_names
    batch_mode = args.batch_mode
    temperature = args.temperature
    
    # load the questions from the directory and evaluate them
    base_directory = 'question_segments/pymatgen_analysis_defects/'
    questions_files_path = load_questions_path_from_directories(base_directory)
    
    if batch_mode:
        batch_job_ids = []
         
    mtb_logger = MatToolBenLogger()
    id_for_logger = None
    
    for model_name in model_names:
        store_path = f'pure_agent_test/{model_name}/'
        model_args = {"model": model_name, "temperature": temperature}
        # Initialize the logger
        if id_for_logger:
            mtb_logger.remove_logger(id_for_logger)
        id_for_logger = mtb_logger.set_logger(store_path, 'generation.log')
        tqdm_logger = None
        if not batch_mode:
            tqdm_logger = mtb_logger.get_tqdm_logger()
        try:
            # Evaluate all questions
            results = evaluate_all_questions(
                questions_files_path,
                llm_name=model_name,
                model_args=model_args,
                batch_mode=batch_mode
            )
            if batch_mode:
                batch_job_ids.append({"model_name": model_name, "batch_job_id": results})
            else:
                # Extract the responses
                results = [extract_response(r) for r in results]
                # Save the responses to a JSON file
                output_data = [
                    {"question_file_path": os.path.basename(os.path.dirname(q)), "function": r[0], "function_name": r[1]}
                    for q, r in zip(questions_files_path, results)
                ]
                output_file = os.path.join(store_path, "function_generation_results.jsonl")
                with open(output_file, "w", encoding="utf-8") as f:
                    for entry in output_data:
                        f.write(json.dumps(entry) + "\n")

                mtb_logger.info(f"Saved responses to {output_file}")
        except Exception as e:
            mtb_logger.error(f"An error occurred for model {model_name}: {e}")
            
    if batch_mode:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'pure_agent_test/batch_job_ids_{current_time}.jsonl', 'w') as f:
            for batch_job_id in batch_job_ids:
                f.write(json.dumps(batch_job_id) + "\n")
    
    
