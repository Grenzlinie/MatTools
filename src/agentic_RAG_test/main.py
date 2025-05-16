import os
import argparse
from typing_extensions import List
from mtb_logger import MatToolBenLogger
from rag import PymatgenRepoAssistant
from langchain_chroma import Chroma
from src.call_llms import load_llm, load_embedding_model
import json    

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

if __name__ == "__main__":
        # replace the model name with the model you want to test
    parser = argparse.ArgumentParser(description='Run LLM evaluation with specified model. Example input: --model_names gpt-4o-mini-2024-07-18')
    parser.add_argument('--model_name', default='gpt-4o-mini-2024-07-18', type=str,
                      help='Name of models to evaluate. Example: gpt-4o-mini-2024-07-18')
    parser.add_argument('--temperature', type=lambda x: max(0, float(x)), default=0.7,
                      help='Temperature setting for the model. Default is 0.7. Minimum value is 0.')
    parser.add_argument('--retriever_type', type=str, default='llm-doc-full', help='Type of retriever to use. Default is code. Options: [llm-doc, llm-doc-full].')
    args = parser.parse_args()
    model_name = args.model_name
    temperature = args.temperature
    retriever_type = args.retriever_type
    
    if model_name == "o1-preview-2024-09-12":
        o1 = True
    else:
        o1 = False
        
    # the result will be saved in the following directory
    if retriever_type == 'llm-doc':
        store_path = f"agentic_RAG_test/{model_name}_method3/"
    elif retriever_type == 'llm-doc-full':
        store_path = f"agentic_RAG_test/{model_name}_method4/"
    else:
        raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of ['llm-doc', 'llm-doc-full'].")
    
    # load the questions from the directory and evaluate them
    base_directory = 'question_segments/pymatgen_analysis_defects/'
    questions_files_path = load_questions_path_from_directories(base_directory)
    
    # initialize logger
    mtb_logger = MatToolBenLogger()
    mtb_logger.set_logger(file_path=store_path, filename='agentic_RAG_generation.log')
    

    # load LLM model
    llm = load_llm(llm_name=model_name)
    model_args = {"model": model_name, "temperature": temperature}
    mtb_logger.info(f"Loaded LLM client: {model_name}")
    mtb_logger.info(f"Model args: model_name={model_name}, temperature={temperature}")
    # load embedding model
    embedding_model = load_embedding_model("text-embedding-3-large")
    mtb_logger.info(f"Loaded embedding model: text-embedding-3-large")
    # load vector store
    if retriever_type == 'llm-doc':
        vector_store = Chroma(collection_name='pymatgen_llm_doc', embedding_function=embedding_model, persist_directory="vector_store/vs_method3/")
    elif retriever_type == 'llm-doc-full':
        vector_store = Chroma(collection_name='pymatgen_llm_doc_full', embedding_function=embedding_model, persist_directory="vector_store/vs_method4/")
    else:
        raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of ['code', 'doc', 'llm-doc'].")
    
    if retriever_type == 'llm-doc':
        dp_path = "./documents_llm_doc_gemini_20_flash.json"
    elif retriever_type == 'llm-doc-full':
        dp_path = "./documents_llm_doc_gemini_20_flash_full.json"
    # Initialize the PymatgenRepoAssistant
    assistant = PymatgenRepoAssistant(llm=llm, db_path=dp_path, logger=mtb_logger, vectorstore=vector_store, model_args=model_args)
    mtb_logger.info(f"---------Initialized PymatgenRepoAssistant successfully.---------")
    
    # Evaluate all questions
    results = []
    for index, question_file_path in enumerate(questions_files_path, start=1):
        mtb_logger.info(f"Processing question {index}/{len(questions_files_path)}")
        mtb_logger.info(f"Path to question file: {question_file_path}")
        with open(question_file_path, 'r') as file:
            message = file.read().strip()
        mtb_logger.info("Question: {}".format(message.replace('\n', ' ')))
        result = assistant.respond(message)
        results.append(result)
        
    output_data = [
                {"question_file_path": os.path.basename(os.path.dirname(q)), "function": r[0], "function_name": r[1]}
                for q, r in zip(questions_files_path, results)
            ]
    output_file = os.path.join(store_path, "function_generation_results.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in output_data:
            f.write(json.dumps(entry) + "\n")
    mtb_logger.info("All tasks completed successfully.")