import os
import json
from docker_sandbox import DockerSandbox
import logging
from typing import List, Dict
import json
import os
import argparse
from datetime import datetime
import pandas as pd
from utils import ComplexDictParser

# Initialize logger
def setup_logger(generated_function_path: str):
    """
    Set up a logger that will log the results to a file with the current date.
    """
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(generated_function_path, f"evaluation_logs_{current_date}.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger()

def check_file_name_consistency(generated: list) -> bool:
    """
    Check if the generated file names are consistent with the original files in the directory.
    Args:
        generated (list): A list of dictionaries containing the 'question_file_path'.
    Returns:
        bool: True if the file names are consistent, False otherwise.
    """
    qdp = [ci['question_file_path'] for ci in generated]
    folder_path = 'question_segments/pymatgen_analysis_defects/'
    all_items = os.listdir(folder_path)
    folders = [item for item in all_items if os.path.isdir(os.path.join(folder_path, item))]
    if len(qdp) != len(folders):
        return False
    for gen, orig in zip(qdp, folders):
        if gen != orig:
            return False
    return True

def read_function_generation_results(file_path: str) -> List[Dict]:
    """
    Read function generation results from a JSONL file.
    Args:
        file_path (str): The path to the JSONL file containing function generation results.
    Returns:
        List[Dict]: A list of dictionaries containing the results.
    """
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                results.append(json.loads(line.strip()))
        logger.info(f"Successfully read {len(results)} function generation results from {file_path}")
        return results
    except Exception as e:
        logger.error(f"Failed to read function generation results from {file_path}: {str(e)}")
        return []

def code_validation(codeinfo: dict, sandbox: DockerSandbox) -> str:
    """
    Validates the code by executing it in the DockerSandbox.
    Args:
        codeinfo (dict): A dictionary containing the generated code information.
        sandbox (DockerSandbox): The DockerSandbox instance to execute the code.
    Returns:
        str: The result of the code execution (either 'ok', or an error message).
    """
    try:
        code = codeinfo['function']
        code_name = f"print({codeinfo['function_name']}())"
        execution_code = "\n".join([code, code_name])
        code_execution_result = sandbox.execute_code(execution_code)
        logger.info(f"Code validation for {codeinfo['function_name']} completed successfully.")
        logger.info(f"Code execution result: {code_execution_result}")
        return code_execution_result
    except Exception as e:
        logger.error(f"Code validation failed for {codeinfo['function_name']}: {str(e)}")
        return str(e)

def run_test(unit_test_file_path: str, generated_output: dict, sandbox: DockerSandbox, function_name: str) -> str:
    """
    Run tests using the execute_file method in DockerSandbox.
    Args:
        unit_test_file_path (str): The path to the unit test file.
        generated_output (dict): The generated output (the result of code execution).
        sandbox (DockerSandbox): The DockerSandbox instance.
        function_name (str): The function name being tested.
    Returns:
        str: The test results, which can be 'ok', a list with errors, or an error message.
    """
    try:
        logger.info(f"Running tests for function {function_name} using file {unit_test_file_path}.")
        test_result = sandbox.execute_file(
            params_dict=generated_output, 
            py_filename=unit_test_file_path, 
            function_name=function_name
        )
        
        if type(test_result) == str and "ok" in test_result:
            logger.info(f"Test passed for function {function_name}.")
            return "ok"
        elif isinstance(json.loads(test_result), list):
            logger.info(f"Test partially passed for function {function_name}, returned result: {test_result}")
            return json.loads(test_result)
        else:
            logger.error(f"Test failed for function {function_name}, result: {test_result}")
            return f"Error: The code did not pass the unit tests. Output: {test_result}"

    except Exception as e:
        logger.error(f"Error during test execution for function {function_name}: {str(e)}")
        return f"Error during test execution: {str(e)}"

def parse_complex_string(input_str):
    parser = ComplexDictParser()
    return parser.parse(input_str)

def evaluate_generated_code(i:int, unit_test_file_path: str, codeinfo: dict, sandbox: DockerSandbox) -> str:
    """
    Evaluates the generated code by executing it in the Docker sandbox and comparing the results with expected values.
    Args:
        unit_test_file_path (str): The path to the unit test file.
        codeinfo (dict): The generated code information.
        sandbox (DockerSandbox): The DockerSandbox instance.
    Returns:
        str: The evaluation result (either 'ok', a list of errors, or an error message).
    """
    try:
        logger.info(f"------Evaluating generated code {i} for function {codeinfo['function_name']}------")
        result = code_validation(codeinfo, sandbox)
        
        try:
            if result['stdout'] == "":
                raise ValueError("No dict output from code execution")
            code = result['stdout']
            parsed_dict = parse_complex_string(code)
            if parsed_dict == None:
                raise ValueError("The output has something that cannot be parsed as a dict")
            if isinstance(parsed_dict, dict) and parsed_dict != {}:
                logger.info(f"Code execution successful for {codeinfo['function_name']}. Output: {parsed_dict}")
            else:
                raise ValueError("The output has something that cannot be parsed as a dict")
        except (ValueError, SyntaxError) as e:
            logger.error(f"FunctionError: Unable to process the result for {codeinfo['function_name']}. Error: {str(e)}. Output: {result}")
            return "FunctionError"
        
        test_function_name = codeinfo['question_file_path']
        test_result = run_test(unit_test_file_path, parsed_dict, sandbox, test_function_name)
        
        return test_result
        
    except Exception as e:
        logger.error(f"Error during evaluation for function {codeinfo['function_name']}: {str(e)}")
        return f"Error during test execution: {str(e)}"

def print_accuracy_summary(correct_tasks, partially_correct_tasks, incorrect_tasks, function_errors, result_errors, success_count, total_tasks, correct_subtasks, incorrect_subtasks, total_subtasks, file_name="accuracy_summary.xlsx"):
    """
    Print a summary table of the accuracy and error types, and save it as an Excel file.
    Args:
        correct_tasks (int): Number of correctly completed tasks.
        partially_correct_tasks (int): Number of partially correct tasks.
        incorrect_tasks (int): Number of tasks with errors.
        function_errors (int): Number of tasks with function errors.
        result_errors (int): Number of tasks with result errors.
        success_count (int): Number of successful tasks.
        total_tasks (int): Total number of tasks.
        correct_subtasks (int): Number of correct sub-tasks.
        incorrect_subtasks (int): Number of incorrect sub-tasks.
        total_subtasks (int): Total number of sub-tasks.
        file_name (str): Name of the file to save the Excel summary to.
    """
    task_accuracy = correct_tasks / total_tasks * 100
    subtask_accuracy = correct_subtasks / total_subtasks * 100
    function_runnable_rate = (total_tasks - function_errors) / total_tasks * 100

    logger.info(f"Total tasks: {total_tasks}, Correct: {correct_tasks}, Partially Correct: {partially_correct_tasks}, Incorrect: {incorrect_tasks}, Function Errors: {function_errors}, Result Errors: {result_errors}, Successes: {success_count}, Accuracy: {task_accuracy:.2f}%, Function Runnable Rate: {function_runnable_rate:.2f}%")
    logger.info(f"Total sub-tasks: {total_subtasks}, Correct: {correct_subtasks}, Incorrect: {incorrect_subtasks}, Accuracy: {subtask_accuracy:.2f}%")
    
    # Create a dataframe for the error summary
    error_summary = pd.DataFrame({
        "Task/ Sub-task": ["Tasks", "Sub-tasks"],
        "Total": [total_tasks, total_subtasks],
        "Correct": [correct_tasks, correct_subtasks],
        "Partially Correct": [partially_correct_tasks, ""],
        "Incorrect": [incorrect_tasks, incorrect_subtasks],
        "Function Runnable Rate": [function_runnable_rate, ""],
        "Accuracy (%)": [task_accuracy, subtask_accuracy],  # Accuracy for tasks and subtasks
        "Function Errors": [function_errors, ""],  # Function errors only apply to tasks
        "Result Errors": [result_errors, ""],  # Result errors only apply to tasks
    })

    logger.info("\n" + error_summary.to_string(index=False))

    return error_summary
    

if __name__ == "__main__":
    """
    Main script to evaluate the generated functions by running tests in a Docker sandbox environment.
    The script tracks the number of successful tasks, tasks with errors, and the accuracy of the sub-tasks.
    """
    # 预计是除非最后结果是ok或者返回list，否则都报错误信息。List则表明部分通过或者至少import正确。
    # 分成三类，function error, result error, success
    # 1. function error: 无法import或函数使用错误，则代码无法运行
    # 2. result error: import成功，也使用了存在的pymatgen函数/方法，返回dict，但是dict的值与预期不符，结果错误，返回错误list
    # 3. success: import成功，返回dict，dict的值与预期一致，返回ok
    # In English:
    # 1. FunctionError: Unable to import or use the necessary functions (code cannot run).
    # 2. ResultError: Code runs, but the output is incorrect or does not match expectations.
    # 3. Success: The code runs correctly and returns the expected result.
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated_function_path", type=str, default="", help="generated_function_path, e.g. 'thinking_agent_test/gpt-3.5-turbo-0125_method1/'")
    args = parser.parse_args()
    generated_function_path = args.generated_function_path
    logger = setup_logger(generated_function_path)  # Initialize logger with the generated function path
    generated_function_path_with_jsonl = os.path.join(generated_function_path, "function_generation_results.jsonl")
    logger.info(f"------Starting evaluation process for functions at {generated_function_path_with_jsonl}------")
    
    function_lists = read_function_generation_results(generated_function_path_with_jsonl)
    total_tasks_number = 49
    total_sub_tasks = 138
    
    if len(function_lists) != total_tasks_number:
        logger.error(f"Total tasks number is not equal to {total_tasks_number}")
        raise ValueError(f"Total tasks number is not equal to {total_tasks_number}")
    if not check_file_name_consistency(function_lists):
        logger.error("File names are not consistent.")
        raise ValueError("File names are not consistent.")
        
    sandbox = DockerSandbox()
    base_path = "question_segments/pymatgen_analysis_defects/{path}/new_unit_test.py"
    ref_sub_tasks_list = [10, 4, 1, 2, 18, 3, 4, 1, 1, 3, 1, 1, 1, 2, 3, 1, 2, 2, 2, 1, 1, 2, 1, 9, 1, 3, 1, 2, 1, 2, 11, 2, 4, 2, 2, 2, 1, 2, 4, 2, 1, 3, 2, 1, 3, 2, 3, 3, 2]

    correct_tasks = 0
    partially_correct_tasks = 0
    incorrect_tasks = 0
    correct_subtasks = 0
    incorrect_subtasks = 0
    function_errors = 0
    result_errors = 0
    success_count = 0

    for i, codeinfo in enumerate(function_lists):
        unit_test_file_path = base_path.format(path=codeinfo['question_file_path'])
        evaluation_result = evaluate_generated_code(i, unit_test_file_path, codeinfo, sandbox)
        
        # Count correct and incorrect results based on the evaluation
        if "ok" in evaluation_result:
            correct_tasks += 1
            correct_subtasks += ref_sub_tasks_list[i]  # Assuming 'sub_tasks' field exists
            success_count += 1
        elif isinstance(evaluation_result, list):
            partially_correct_tasks += 1
            correct_subtasks += evaluation_result[-1] - evaluation_result[-2]  # Correct sub-tasks count
            incorrect_subtasks += evaluation_result[-2]  # Incorrect sub-tasks count
            result_errors += 1
        elif evaluation_result == "FunctionError":
            function_errors += 1
            incorrect_tasks += 1
            incorrect_subtasks += ref_sub_tasks_list[i]
        else:
            incorrect_tasks += 1
            incorrect_subtasks += ref_sub_tasks_list[i]
            function_errors += 1  # For all other errors
            
        logger.info(f"Evaluation result for function | {codeinfo['function_name']} | {evaluation_result}")
        logger.info(f"-------------------------------------------------------------")
    
    # Print the summary including task and sub-task accuracies, errors, and types
    error_summary = print_accuracy_summary(
        correct_tasks, partially_correct_tasks, incorrect_tasks, function_errors, result_errors, success_count, 
        total_tasks_number, correct_subtasks, incorrect_subtasks, total_sub_tasks
    )

    # Store the error summary in an Excel file
    error_summary.to_excel(os.path.join(generated_function_path, "accuracy_summary.xlsx"), index=False)
    logger.info(f"Accuracy summary saved as 'accuracy_summary.xlsx'.")
    logger.info(f"------Evaluation process completed successfully------")