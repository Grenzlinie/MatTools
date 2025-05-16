import sys
sys.path.append('../')
import os
import json
import re
import argparse
from typing_extensions import List, TypedDict
from mtb_logger import MatToolBenLogger
from src.call_llms import load_chat_llm, load_embedding_model
from langchain_chroma import Chroma
from src.docker_sandbox import DockerSandbox
from src.utils import ComplexDictParser
from typing import List, Dict, Union, Optional
from typing_extensions import TypedDict
from prompts import SYSTEM_PROMPT, USER_PROMPT, USER_PROMPT_DOC, USER_PROMPT_LLM_DOC, FORMAT_CHECKER_PROMPT, CRITICAL_FEEDBACK_PROMPT, CRITICAL_FEEDBACK_FORMART_CHECKER_PROMPT

class RAGPipeline:
    SYSTEM_PROMPT = SYSTEM_PROMPT
    USER_PROMPT = USER_PROMPT
    USER_PROMPT_DOC = USER_PROMPT_DOC
    USER_PROMPT_LLM_DOC = USER_PROMPT_LLM_DOC
    FORMAT_CHECKER_PROMPT = FORMAT_CHECKER_PROMPT
    CRITICAL_FEEDBACK_PROMPT = CRITICAL_FEEDBACK_PROMPT
    CRITICAL_FEEDBACK_FORMART_CHECKER_PROMPT = CRITICAL_FEEDBACK_FORMART_CHECKER_PROMPT
    
    # 内部状态定义
    class State(TypedDict):
        question: str
        retriever_type: str
        context: Optional[str]
        answer: Optional[str]
        memory: Optional[List[Dict]]
        code_check_result: Optional[Dict]
        suggestions: Optional[Union[str, Dict]]       
            
    def __init__(self, model_name: str, temperature: float, retriever_type: str):
        """
        Initialize RAGPipeline with logging, LLM model, embedding model, and vector store.
        """
        # Validate retriever_type
        VALID_RETRIEVER_TYPES = ['code', 'doc', 'llm-doc', 'llm-doc-full']
        if retriever_type not in VALID_RETRIEVER_TYPES:
            raise ValueError(f"Invalid retriever_type: {retriever_type}. Expected one of {VALID_RETRIEVER_TYPES}.")
        
        # Set store path based on retriever type
        store_path = f"mtr_rag_test/{model_name}_{VALID_RETRIEVER_TYPES.index(retriever_type) + 1}/"
        
        self.model_name = model_name
        self.temperature = temperature
        self.retriever_type = retriever_type
        self.base_directory = 'question_segments/pymatgen_analysis_defects/'
        self.store_path = store_path

        # Initialize logger
        self.mtb_logger = MatToolBenLogger()
        self.mtb_logger.set_logger(file_path=self.store_path, filename='mtr_RAG_generation.log')
        
        try:
            # Load LLM model
            self.llm = load_chat_llm(model_name, temperature)
            self.mtb_logger.info(f"Loaded LLM client: {model_name}")
            self.mtb_logger.info(f"Model args: model_name={model_name}, temperature={temperature}")
            
            # Load embedding model
            self.embedding_model = load_embedding_model("text-embedding-3-large")
            self.mtb_logger.info("Loaded embedding model: text-embedding-3-large")
            
            # Initialize vector store
            vector_store_paths = {
                'code': ("pymatgen", "vector_store/vs_method1/"),
                'doc': ("pymatgen-doc", "vector_store/vs_method2/"),
                'llm-doc': ("pymatgen_llm_doc", "vector_store/vs_method3/"),
                'llm-doc-full': ("pymatgen_llm_doc_full", "vector_store/vs_method4/")
            }
            
            collection_name, persist_directory = vector_store_paths[retriever_type]
            self.vector_store = Chroma(
                collection_name=collection_name, 
                embedding_function=self.embedding_model, 
                persist_directory=persist_directory
            )
            
        except Exception as e:
            self.mtb_logger.error(f"Initialization error: {e}")
            raise
    
    def extract_response(self, response: str) -> List[str]:
        """
        Extract code segments and function names from LLM output.
        """
        try:
            code_match = re.search(r"<code>\s*```python\s*(.*?)```\s*</code>", response, re.DOTALL)
            name_match = re.search(r"<name>(.*?)</name>", response, re.DOTALL)
            
            if not code_match or not name_match:
                self.mtb_logger.warning(f"Failed to extract response from: {response}")
                return ["", ""]
            
            return [code_match.group(1).strip(), name_match.group(1).strip()]
        
        except Exception as e:
            self.mtb_logger.error(f"Error in extract_response: {e}")
            return ["", ""]
        
    def extract_reponse_from_critics(self, response: str) -> dict:
        """
        从批评性建议中提取信息。
        """
        feedback_match = re.search(r"<feedback>(.*?)</feedback>", response, re.DOTALL)
        next_rag_retrieval_match = re.search(r"<next_rag_retrieval>(.*?)</next_rag_retrieval>", response, re.DOTALL)
        if not feedback_match or not next_rag_retrieval_match:
            self.mtb_logger.info(f"Failed to extract response from: {response}")
            return {"suggestions": response}
        else:
            return {"suggestions": {"feedback": feedback_match.group(1).strip(), "next_rag_retrieval": next_rag_retrieval_match.group(1).strip()}}
        

    def load_questions_path_from_directories(self) -> List[str]:
        """
        加载 base_directory 下所有 question.txt 文件的路径。
        """
        questions_files_path = [
            os.path.join(root, 'question.txt')
            for root, _, files in os.walk(self.base_directory) if 'question.txt' in files
        ]
        return questions_files_path

    def retrieve(self, state: Dict) -> Dict:
        """
        Retrieve relevant code snippets and build context.
        """
        try:
            retrieved_docs = self.vector_store.similarity_search(state["question"], k=5)
            
            if not retrieved_docs:
                self.mtb_logger.warning(f"No documents retrieved for question: {state['question']}")
                return {"context": "", "retriever_type": "code"}
            
            source = ["This code belongs to the module: " + doc.metadata["source"] for doc in retrieved_docs]
            first_function_or_class = [
                "The top-level function or class of this code: " + doc.metadata.get("first_function_or_class", "None")
                for doc in retrieved_docs
            ]
            
            contexts = []
            for i in range(len(retrieved_docs)):
                context = "\n".join([source[i], first_function_or_class[i], retrieved_docs[i].page_content])
                contexts.append(context)
            
            contexts = "\n\n---------------------------------\n\n".join(contexts)
            self.mtb_logger.info(f"Retrieved {len(retrieved_docs)} documents")
            return {"context": contexts, "retriever_type": "code"}
        
        except Exception as e:
            self.mtb_logger.error(f"Error in retrieve method: {e}")
            return {"context": "", "retriever_type": "code"}

    def retrieve_doc(self, state: State|dict) -> dict:
        """
        检索文档，构建上下文。
        """
        try:
            retrieved_docs = self.vector_store.similarity_search(state["question"], k=5)
            source = ["Source of this document: " + doc.metadata["title"] for doc in retrieved_docs]
            contexts = []
            for i in range(len(retrieved_docs)):
                context = "\n".join([source[i], retrieved_docs[i].page_content])
                contexts.append(context)
            contexts = "\n\n---------------------------------\n\n".join(contexts)
            self.mtb_logger.info(f"Contexts: {contexts}")
            return {"context": contexts, "retriever_type": "doc"}
        except Exception as e:
            self.mtb_logger.error(f"Error in retrieve method: {e}")
            return {"context": "", "retriever_type": "doc"}

    def retrieve_llm_doc(self, state: State|dict) -> dict:
        """
        检索 llm-doc 类型的文档，构建上下文。
        """
        try:
            retrieved_docs = self.vector_store.similarity_search(state["question"], k=5)
            code_source_file = [
                "Source of this document: " + doc.metadata["code_source_file"]
                for doc in retrieved_docs
            ]
            contexts = []
            for i in range(len(retrieved_docs)):
                context = "\n".join([code_source_file[i], retrieved_docs[i].page_content])
                contexts.append(context)
            contexts = "\n\n---------------------------------\n\n".join(contexts)
            self.mtb_logger.info(f"Contexts: {contexts}")
            return {"context": contexts, "retriever_type": "llm-doc"}
        except Exception as e:
            self.mtb_logger.error(f"Error in retrieve method: {e}")
            return {"context": "", "retriever_type": "llm-doc"}

    def generate(self, state: State, extra_info: str|None) -> dict:
        """
        根据检索结果和问题调用 LLM 生成答案。
        """
        retrieved_content = state['context']
        if extra_info == None:
            if state['retriever_type'] == 'code':
                messages = [
                    {'role': 'system', 'content': self.SYSTEM_PROMPT},
                    {'role': 'user', 'content': self.USER_PROMPT.format(question=state["question"], retrieved_code_segments=retrieved_content)}
                ]
            elif state['retriever_type'] == 'doc':
                messages = [
                    {'role': 'system', 'content': self.SYSTEM_PROMPT},
                    {'role': 'user', 'content': self.USER_PROMPT_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}
                ]
            else:
                messages = [
                    {'role': 'system', 'content': self.SYSTEM_PROMPT},
                    {'role': 'user', 'content': self.USER_PROMPT_LLM_DOC.format(question=state["question"], retrieved_code_documents=retrieved_content)}
                ]
        else:
            if state['retriever_type'] == 'code':
                messages = state.memory.extend([
                    {'role': 'user', 'content': extra_info}
                ])
            elif state['retriever_type'] == 'doc':
                messages = state.memory.extend([
                    {'role': 'user', 'content': extra_info}
                ])
            else:
                messages = state.memory.extend([
                    {'role': 'user', 'content': extra_info}
                ])
        response = self.llm.invoke(messages)
        self.mtb_logger.info("Received response from LLM: {}".format(response.content.replace('\n', ' ')))
        self.mtb_logger.info(
            f"Response metadata: {response.response_metadata} | Additional kwargs: {response.additional_kwargs} | ID: {response.id} | model_config: {response.model_config}"
        )
        return {"answer": response.content, "memory": messages.append({"assistant": response.content})}

    def format_checker(self, state: State) -> dict:
        """
        检查生成的代码是否符合格式要求。
        """
        messages = [{'role': 'user', 'content': self.FORMAT_CHECKER_PROMPT.format(generated_code=state["answer"])}]
        response = self.llm.invoke(messages)
        return {"answer": response.content}
    
    def critics_format_checker(self, message: str) -> str:
        """
        检查批评性建议的格式。
        """
        messages = [{'role': 'user', 'content': self.CRITICAL_FEEDBACK_FORMART_CHECKER_PROMPT.format(content=message)}]
        response = self.llm.invoke(messages)
        return response.content
        
    def rag_pipeline(self, state: dict) -> dict:
        """
        执行完整工作流：检索 -> 生成，返回最终状态。
        """
        # 选择相应的检索函数
        if self.retriever_type == 'code':
            retriever = self.retrieve
        elif self.retriever_type == 'doc':
            retriever = self.retrieve_doc
        elif self.retriever_type in ['llm-doc', 'llm-doc-full']:
            retriever = self.retrieve_llm_doc
        else:
            raise ValueError(f"Invalid retriever_type: {self.retriever_type}")
        
        # 检索阶段
        if "suggestions" in state and type(state["suggestions"]) == dict and "next_rag_retrieval" in state["suggestions"]:
            tmp_query = {"question": state['suggestions']['next_rag_retrieval']}
            state_update = retriever(tmp_query)
            state.update(state_update)
        elif "suggestions" in state and type(state["suggestions"]) == str:
            tmp_query = {"question": state["suggestions"]}
            state_update = retriever(tmp_query)
            state.update(state_update)
        elif "suggestions" not in state:
            state_update = retriever(state)
            state.update(state_update)
        
        # 生成阶段
        if "code_check_result" in state and "suggestions" in state and type(state["suggestions"]) == dict and "next_rag_retrieval" in state["suggestions"]:
            info_from_critic_agent = json.dumps(state["suggestions"], ensure_ascii=False, indent=2)
            self.mtb_logger.info(f"Info from critic agent: {info_from_critic_agent}")
            extra_info = f"Runtime output of the code:\n{state['code_check_result']}\n\nSuggestions from critic agent:\n{info_from_critic_agent}\n\nNew retrieved content from critic agent:\n{state['context']}\n\nNow, please generate a new python function based on the above information."
        elif "code_check_result" in state and "fail_result" in state["code_check_result"]:
            fail_result = state["code_check_result"]["fail_result"]
            extra_info = f"Runtime output of the code:\n{fail_result}\n\nNow, please generate a new python function based on the above information."
        elif "code_check_result" in state and "fail_result" not in state["code_check_result"]:
            info_from_critic_agent = state["suggestions"]
            extra_info = f"Runtime output of the code:\n{state['code_check_result']}\n\nSuggestions from critic agent:\n{info_from_critic_agent}\n\nNew retrieved content from critic agent:\n{state['context']}\n\nNow, please generate a new python function based on the above information."
        else:
            extra_info = None
        gen_result = self.generate(state, extra_info)
        self.mtb_logger.info(f"Generated response: {gen_result['answer']}")
        state.update(gen_result)
        gen_result = self.format_checker(gen_result)
        self.mtb_logger.info(f"Format checker result: {gen_result['answer']}")
        state.update(gen_result)
        
        return state
    
    def parse_complex_string(self, input_str: str):
        parser = ComplexDictParser()
        return parser.parse(input_str)
    
    def code_check(self, state: State) -> dict:
        sandbox = DockerSandbox()
        tmp = self.extract_response(state['answer'])
        func = tmp[0]
        func_name = tmp[1]
        if func == "" or func_name == "":
            fail_result = "The response format is incorrect.\nThe response format should be as follows:\n<answer>\n<code>\n```python\n# The generated function code\ndef example_function():\n    pass\n```\n</code>\n<name>name_of_generated_function</name>\n</answer>"
            self.mtb_logger.info(fail_result)
            return {"fail_result": fail_result}
        else:
            func_name = f"print({func_name}())"
            execution_code = "\n".join([func, func_name])
            result = sandbox.execute_code(execution_code)
            if type(result) == str:
                return {"fail_result": result}
            return result
    
    def critic_agent(self, state: State, code_check_result) -> dict:
        """
        生成批评性建议。
        """
        suggestions = {"suggestions": ""}
        if "fail_result" in code_check_result:
            suggestions = {"suggestions": code_check_result}
        else:
            # if state['retriever_type'] == 'code':
            #     question = "\n".join(self.SYSTEM_PROMPT, self.USER_PROMPT.format(question=state["question"], retrieved_code_segments=state["context"]))
            # elif state['retriever_type'] == 'doc':
            #     question = "\n".join(self.SYSTEM_PROMPT, self.USER_PROMPT_DOC.format(question=state["question"], retrieved_code_documents=state["context"]))
            # else:
            #     question = "\n".join(self.SYSTEM_PROMPT, self.USER_PROMPT_LLM_DOC.format(question=state["question"], retrieved_code_documents=state["context"]))
            prompt = self.CRITICAL_FEEDBACK_PROMPT.format(
                question=state['question'],
                generated_code=state["answer"],
                runtime_output=json.dumps(code_check_result, ensure_ascii=False, indent=2)
            )
            messages = [{'role': 'user', 'content': prompt}]
            response = self.llm.invoke(messages)
            self.mtb_logger.info("Received response from LLM: {}".format(response.content.replace('\n', ' ')))
            response = self.critics_format_checker(response.content)
            extracted_response = self.extract_reponse_from_critics(response)
            suggestions = extracted_response
        return suggestions
            
    
    def pipeline(self, state: dict) -> dict:
        iteration_limit = 5
        iteration = 0
        while iteration < iteration_limit:
            iteration += 1
            self.mtb_logger.info(f"----------------Iteration: {iteration}----------------")
            state = self.rag_pipeline(state)
            self.mtb_logger.info(f"State after rag_pipeline of iteration {iteration}: {state}")
            code_check_result = self.code_check(state)
            self.mtb_logger.info(f"Code check result: {code_check_result}")
            state.update(code_check_result)
            if type(code_check_result) == dict and "stdout" in code_check_result and code_check_result["stdout"] != "":
                self.mtb_logger.info(f"Input to parser: {code_check_result}")
                parsed_dict = self.parse_complex_string(code_check_result["stdout"])
                self.mtb_logger.info(f"Parsed result: {parsed_dict}")
                if isinstance(parsed_dict, dict) and all(value is not None for value in parsed_dict.values()):
                    self.mtb_logger.info(f"Final state of iteration {iteration}: {state}")
                    self.mtb_logger.info("Finished all iterations with demanded answer. Go to the next question.")
                    return state
            if iteration < iteration_limit:
                suggestions = self.critic_agent(state, code_check_result)
                self.mtb_logger.info(f"Suggestions: {suggestions}")
                state.update(suggestions)
        self.mtb_logger.info(f"Final state of iteration {iteration}: {state}")
        self.mtb_logger.info("Failed to complete all subtasks. Go to the next question.")
        return state

    def run(self) -> None:
        """
        加载所有问题文件，依次执行工作流，并将结果保存到 JSONL 文件中。
        """
        questions_files_path = self.load_questions_path_from_directories()
        results = []
        for index, question_file_path in enumerate(questions_files_path, start=1):
            self.mtb_logger.info(f"Processing question {index}/{len(questions_files_path)}")
            self.mtb_logger.info(f"Path to question file: {question_file_path}")
            with open(question_file_path, 'r', encoding="utf-8") as file:
                message = file.read().strip()
            self.mtb_logger.info("Question: {}".format(message.replace('\n', ' ')))
            state = {"question": message}
            final_state = self.pipeline(state)
            results.append(final_state['answer'])
        
        # 提取 LLM 返回中的代码和函数名称，并保存结果
        extracted_results = [self.extract_response(r) for r in results]
        output_data = [
            {
                "question_file_path": os.path.basename(os.path.dirname(q)),
                "function": r[0],
                "function_name": r[1]
            }
            for q, r in zip(questions_files_path, extracted_results)
        ]
        os.makedirs(self.store_path, exist_ok=True)
        output_file = os.path.join(self.store_path, "function_generation_results.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in output_data:
                f.write(json.dumps(entry) + "\n")
        self.mtb_logger.info("All tasks completed successfully.")

    @classmethod
    def main(cls):
        """
        Parse command-line arguments, create RAGPipeline instance, and run.
        Added more robust argument parsing and error handling.
        """
        parser = argparse.ArgumentParser(
            description='Run LLM evaluation with specified model.'
        )
        parser.add_argument('--model_name', 
                             default='gpt-4o-mini-2024-07-18', 
                             type=str,
                             help='Name of models to evaluate.')
        parser.add_argument('--temperature', 
                             type=float, 
                             default=0.7,
                             help='Temperature setting for the model (0-1).')
        parser.add_argument('--retriever_type', 
                             type=str, 
                             default='code',
                             choices=['code', 'doc', 'llm-doc', 'llm-doc-full'],
                             help='Type of retriever to use.')
        
        try:
            args = parser.parse_args()
            
            # Validate temperature is between 0 and 1
            if not 0 <= args.temperature <= 1:
                raise ValueError("Temperature must be between 0 and 1")
            
            pipeline_instance = cls(
                model_name=args.model_name,
                temperature=args.temperature,
                retriever_type=args.retriever_type,
            )
            pipeline_instance.run()
        
        except Exception as e:
            print(f"Error in main execution: {e}")
            sys.exit(1)

if __name__ == "__main__":
    RAGPipeline.main()