import sys
from typing_extensions import List, TypedDict
sys.path.append("..")
from mtb_logger import MatToolBenLogger
import argparse
import os
from src.call_llms import load_chat_llm, load_embedding_model
from langchain_chroma import Chroma
import tiktoken
from langgraph.graph import START, StateGraph, END
import json
import re

# Prompts templates
SYSTEM_PROMPT = "You are an assistant for code generation tasks. Use the following retrieved code segments to answer the user’s question. Use the retrieved code as needed and generate a concise, well-commented solution."
USER_PROMPT = """**Question**:
{question}

**Retrieved code segments from helper**:
{retrieved_code_segments}

**Answer format**:
Please make sure the response is enclosed within `<answer>`, `<code>` and `<name>` tags. Follow this example format:

<answer>
<code>\n```python\n# The generated function code\ndef example_function():\npass\n```\n</code>
<name>name_of_generated_function</name>
</answer>"""

USER_PROMPT_DOC = """**Question**:
{question}

**Retrieved code documents from helper**:
{retrieved_code_documents}

**Answer format**:
Please make sure the response is enclosed within `<answer>`, `<code>` and `<name>` tags. Follow this example format:

<answer>
<code>\n```python\n# The generated function code\ndef example_function():\npass\n```\n</code>
<name>name_of_generated_function</name>
</answer>"""

USER_PROMPT_LLM_DOC = """**Question**:
{question}

**Retrieved code documents from helper**:
{retrieved_code_documents}

***Notes on documents usage***
1. When attempting to load a file, do not use the file path from the retrieved documents, be sure to use the path provided in the question.
2. If the question provides some code, the code provided in the question must be used in the generated function.

**Answer format**:
Please make sure the response is enclosed within `<answer>`, `<code>` and `<name>` tags. Follow this example format:

<answer>
<code>\n```python\n# The generated function code\ndef example_function():\npass\n```\n</code>
<name>name_of_generated_function</name>
</answer>"""

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

def analyze_token_lengths(docs, mtb_logger):
    """
    Analyzes the token lengths of a list of documents and logs the results.

    This function calculates the number of tokens in each document using a specified
    encoding, logs the token count for each document, and determines the longest,
    shortest, and average token lengths across all documents. It also calculates the
    total token count and the cost based on $0.130 per 1M tokens.

    Args:
        docs (List[Document]): A list of Document objects to analyze.
        mtb_logger (MatToolBenLogger): Logger instance for logging the token information.

    Returns:
        None
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    token_lengths = []
    total_tokens = 0
    for doc in docs:
        token_length = len(encoding.encode(doc.page_content))
        token_lengths.append((doc.metadata['source'], token_length))
        total_tokens += token_length
        mtb_logger.info(f"Document {doc.metadata['source']} has {token_length} tokens.")
        
    if token_lengths:
        longest_doc = max(token_lengths, key=lambda x: x[1])
        shortest_doc = min(token_lengths, key=lambda x: x[1])
        average_token_length = total_tokens / len(token_lengths)
        mtb_logger.info(f"Longest document: {longest_doc[0]} with {longest_doc[1]} tokens.")
        mtb_logger.info(f"Shortest document: {shortest_doc[0]} with {shortest_doc[1]} tokens.")
        mtb_logger.info(f"Average token length: {average_token_length:.2f} tokens.")
        
    # Calculate total cost
    cost_per_million_tokens = 0.130
    total_cost = (total_tokens / 1_000_000) * cost_per_million_tokens
    mtb_logger.info(f"Total tokens: {total_tokens}")
    mtb_logger.info(f"Estimated cost: ${total_cost:.4f}")

# Define state for application
class State(TypedDict):
    question: str
    context: str
    answer: str
    retriever_type: str
    
# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"], k=5)
    source = ["This code belongs to the module: " + doc.metadata["source"] for doc in retrieved_docs]
    first_function_or_class = ["The top-level function or class of this code: " + doc.metadata.get("first_function_or_class", "None") for doc in retrieved_docs]
    contexts = []
    for i in range(len(retrieved_docs)):
        context = "\n".join([source[i], first_function_or_class[i], retrieved_docs[i].page_content])
        contexts.append(context)
    contexts = "\n\n---------------------------------\n\n".join(contexts)
    mtb_logger.info(f"Contexts: {contexts}")
    return {"context": contexts, "retriever_type": "code"}

def retrieve_doc(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"], k=5)
    source = ["Source of this document: " + doc.metadata["title"] for doc in retrieved_docs]
    contexts = []
    for i in range(len(retrieved_docs)):
        context = "\n".join([source[i], retrieved_docs[i].page_content])
        contexts.append(context)
    contexts = "\n\n---------------------------------\n\n".join(contexts)
    mtb_logger.info(f"Contexts: {contexts}")
    return {"context": contexts, "retriever_type": "doc"}

def retrieve_llm_doc(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"], k=5)
    code_source_file = ["Source of this document: " + doc.metadata["code_source_file"] for doc in retrieved_docs]
    contexts = []
    for i in range(len(retrieved_docs)):
        context = "\n".join([code_source_file[i], retrieved_docs[i].page_content])
        contexts.append(context)
    contexts = "\n\n---------------------------------\n\n".join(contexts)
    mtb_logger.info(f"Contexts: {contexts}")
    return {"context": contexts, "retriever_type": "llm-doc"}

def generate(state: State):
    retrieved_content = state['context']
    if state['retriever_type'] == 'code':
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT.format(question=state["question"], retrieved_code_segments=retrieved_content)}]
    elif state['retriever_type'] == 'doc':
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}]
    else:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT_LLM_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}]
    response = llm.invoke(messages)
    mtb_logger.info("Received response from LLM: {}".format(response.content.replace('\n', ' ')))
    mtb_logger.info(f"Response metadata: {response.response_metadata} | Additional kwargs: {response.additional_kwargs} | ID: {response.id} | model_config: {response.model_config}")
    return {"answer": response.content}

def generate_o1(state: State):
    retrieved_content = state['context']
    if state['retriever_type'] == 'code':
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT.format(question=state["question"], retrieved_code_segments=retrieved_content)}]
    elif state['retriever_type'] == 'doc':
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}]
    else:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': USER_PROMPT_LLM_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}]
    response = llm.invoke(messages)
    mtb_logger.info("Received response from LLM: {}".format(response.content.replace('\n', ' ')))
    mtb_logger.info(f"Response metadata: {response.response_metadata} | Additional kwargs: {response.additional_kwargs} | ID: {response.id} | model_config: {response.model_config}")
    return {"answer": response.content}

def build_graph(o1=False, retriever_type='code'):
    retrievers = {
        'code': retrieve,
        'doc': retrieve_doc,
        'llm-doc': retrieve_llm_doc,
        'llm-doc-full': retrieve_llm_doc
    }
    
    retriever = retrievers.get(retriever_type)
    if retriever is None:
        raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of {list(retrievers.keys())}.")
    
    generate_func = generate_o1 if o1 else generate
    
    workflow = StateGraph(State)
    workflow.add_node("retrieve", retriever)
    workflow.add_node("generate", generate_func)
    
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

if __name__ == "__main__":
    # replace the model name with the model you want to test
    parser = argparse.ArgumentParser(description='Run LLM evaluation with specified model. Example input: --model_names gpt-4o-mini-2024-07-18')
    parser.add_argument('--model_name', default='gpt-4o-mini-2024-07-18', type=str,
                      help='Name of models to evaluate. Example: gpt-4o-mini-2024-07-18')
    parser.add_argument('--temperature', type=lambda x: max(0, float(x)), default=0.7,
                      help='Temperature setting for the model. Default is 0.7. Minimum value is 0.')
    parser.add_argument('--retriever_type', type=str, default='code', help='Type of retriever to use. Default is code. Options: [code, doc, llm-doc, llm-doc-full].')
    args = parser.parse_args()
    model_name = args.model_name
    temperature = args.temperature
    retriever_type = args.retriever_type
    
    if model_name == "o1-preview-2024-09-12":
        o1 = True
    else:
        o1 = False
        
    # the result will be saved in the following directory
    if retriever_type == 'code':
        store_path = f"RAG_agent_test/{model_name}_method1/"
    elif retriever_type == 'doc':
        store_path = f"RAG_agent_test/{model_name}_method2/"
    elif retriever_type == 'llm-doc':
        store_path = f"RAG_agent_test/{model_name}_method3/"
    elif retriever_type == 'llm-doc-full':
        store_path = f"RAG_agent_test/{model_name}_method4/"
    else:
        raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of ['code', 'doc', 'llm-doc', 'llm-doc-full'].")
    
    # load the questions from the directory and evaluate them
    base_directory = 'question_segments/pymatgen_analysis_defects/'
    questions_files_path = load_questions_path_from_directories(base_directory)
    
    # initialize logger
    mtb_logger = MatToolBenLogger()
    mtb_logger.set_logger(file_path=store_path, filename='RAG_generation.log')
    
    # load LLM model
    llm = load_chat_llm(model_name, temperature)
    mtb_logger.info(f"Loaded LLM client: {model_name}")
    mtb_logger.info(f"Model args: model_name={model_name}, temperature={temperature}")
    # load embedding model
    embedding_model = load_embedding_model("text-embedding-3-large")
    mtb_logger.info(f"Loaded embedding model: text-embedding-3-large")
    # load vector store
    if retriever_type == 'code':
        vector_store = Chroma(collection_name='pymatgen', embedding_function=embedding_model, persist_directory="vector_store/vs_method1/")
    elif retriever_type == 'doc':
        vector_store = Chroma(collection_name='pymatgen-doc', embedding_function=embedding_model, persist_directory="vector_store/vs_method2/")
    elif retriever_type == 'llm-doc':
        vector_store = Chroma(collection_name='pymatgen_llm_doc', embedding_function=embedding_model, persist_directory="vector_store/vs_method3/")
    elif retriever_type == 'llm-doc-full':
        vector_store = Chroma(collection_name='pymatgen_llm_doc_full', embedding_function=embedding_model, persist_directory="vector_store/vs_method4/")
    else:
        raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of ['code', 'doc', 'llm-doc', 'llm-doc-full'].")
    # Compile application and test
    graph = build_graph(o1=o1, retriever_type=retriever_type)
    # graph.get_graph().draw_mermaid_png(output_file_path=os.path.join(store_path, "visualization.png"))
    
    # Run the test
    try:
        # Evaluate all questions
        results = []
        for index, question_file_path in enumerate(questions_files_path, start=1):
            mtb_logger.info(f"Processing question {index}/{len(questions_files_path)}")
            mtb_logger.info(f"Path to question file: {question_file_path}")
            with open(question_file_path, 'r') as file:
                message = file.read().strip()
            mtb_logger.info("Question: {}".format(message.replace('\n', ' ')))
            result = graph.invoke({"question": message})
            results.append(result['answer'])
        
        results = [extract_response(r) for r in results]
        output_data = [
                    {"question_file_path": os.path.basename(os.path.dirname(q)), "function": r[0], "function_name": r[1]}
                    for q, r in zip(questions_files_path, results)
                ]
        output_file = os.path.join(store_path, "function_generation_results.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in output_data:
                f.write(json.dumps(entry) + "\n")
        mtb_logger.info("All tasks completed successfully.")
    except Exception as e:
        mtb_logger.error(f"An error occurred for model {model_name}: {e}")