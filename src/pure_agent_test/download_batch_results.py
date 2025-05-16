import os
import json
import sys
sys.path.append("..")
from src.call_llms import load_llm
from build_agent import load_questions_path_from_directories
import re

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
        print(f"Could not extract code or name from response: {response}")
        return ["", ""]
    else:
        return [code_match.group(1).strip(), name_match.group(1).strip()]

def download_file(job_info: str):
    client = load_llm(llm_name="gpt-4.5-preview-2025-02-27")
    batch_job = client.batches.retrieve(job_info['batch_job_id'])
    batch_job_status = batch_job.status
    if batch_job_status != 'completed':
        raise RuntimeError(f"Batch job {job_info['batch_job_id']} is not completed. Current status: {batch_job_status}")
    responses = client.files.content(batch_job.output_file_id)
    responses.write_to_file(os.path.join(f"pure_agent_test/{job_info['model_name']}/", 'raw_responses.jsonl'))
    llm_responses = []
    with open(os.path.join(f"pure_agent_test/{job_info['model_name']}/", 'raw_responses.jsonl'), 'r') as file:
        tmp = []
        for line in file:
            # Parsing the JSON string into a dict and appending to the list of results
            json_object = json.loads(line.strip())
            tmp.append(json_object)
    sorted_responses = sorted(tmp, key=lambda x: int(x['custom_id'].split('_')[1]))
    for sorted_response in sorted_responses:
        llm_responses.append(sorted_response['response']['body']['choices'][0]['message']['content'])
    return llm_responses

def download_results_from_ids(file_path: str):
    """
    Download files based on the provided list of batch job IDs from the specified file.

    Args:
        file_path (str): The path to the json file containing batch job IDs.

    Returns:
        None
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, 'r') as f:
        batch_job_ids = [json.loads(line.strip()) for line in f]

    for job_info in batch_job_ids:
        try:
            base_directory = 'question_segments/pymatgen_analysis_defects/'
            questions_files_path = load_questions_path_from_directories(base_directory)
            results = download_file(job_info)
            results = [extract_response(r) for r in results]
            # Save the responses to a JSON file
            output_data = [
                {"question_file_path": os.path.basename(os.path.dirname(q)), "function": r[0], "function_name": r[1]}
                for q, r in zip(questions_files_path, results)
            ]
            output_file = os.path.join(f"pure_agent_test/{job_info['model_name']}", "function_generation_results.jsonl")
            with open(output_file, "w", encoding="utf-8") as f:
                for entry in output_data:
                    f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Error downloading results for job ID {job_info['batch_job_id']}: {e}")

if __name__ == "__main__":
    download_results_from_ids("pure_agent_test/batch_job_ids_20250330_003704.jsonl")