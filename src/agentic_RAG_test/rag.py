import sys
sys.path.append("..")

from text_analysis_tool import TextAnalysisTool
from prompt import query_generation_prompt_str, relevance_ranking_instruction, relevance_ranking_guideline, rag_prompt_str, rag_ar_prompt_str
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing_extensions import List
import json
import time
from openai import OpenAI
from mtb_logger import MatToolBenLogger

class PymatgenRepoAssistant:
    def __init__(self, llm: OpenAI, db_path: str, logger: MatToolBenLogger, vectorstore: Chroma, model_args):
        self.llm = llm
        self.logger = logger
        self.vectorstore = vectorstore
        self.textanslys = TextAnalysisTool(self.llm, db_path, model_args)
        self.model_args = model_args


    def rerank(self, query, docs):
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                messages = [
                    {"role": "system", "content": relevance_ranking_instruction},
                    {"role": "user", "content": relevance_ranking_guideline.format(query=query, docs=docs)}
                ]
                if self.model_args['model'] == "gemini-2.0-flash-thinking-exp-01-21":
                    response = self.llm.chat.completions.create(messages=messages, **self.model_args)
                else:
                    response = self.llm.chat.completions.create(messages=messages, response_format={"type": "json_object"}, **self.model_args)
                # 尝试解析 JSON
                scores = json.loads(response.choices[0].message.content)['documents']

                if not isinstance(scores, list):
                    raise ValueError("Response is not a valid list of documents")

                # 确保 JSON 数据格式正确
                for doc in scores:
                    if not isinstance(doc, dict) or "content" not in doc or "relevance_score" not in doc:
                        raise ValueError("Invalid document format in JSON response")

                self.logger.info(f"Scores: {scores}")

                # 按相关性得分排序
                sorted_data = sorted(scores, key=lambda x: x["relevance_score"], reverse=True)

                # 取前5个文档的内容
                top_5_contents = [doc["content"] for doc in sorted_data[:5]] if len(sorted_data) >= 5 else [doc["content"] for doc in sorted_data]

                return top_5_contents

            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"JSON 解析失败，尝试第 {retry_count + 1} 次: {e}")
                retry_count += 1
                time.sleep(1)  # 等待 1 秒后重试

        # 如果重试 5 次仍然失败，则返回整个文档列表
        self.logger.error("无法解析 JSON 数据，返回原始文档列表")
        return docs

    def rag(self, query, retrieved_documents):
        rag_prompt = rag_prompt_str.format(
            query=query, information="\n\n".join(retrieved_documents)
        )
        response = self.llm.chat.completions.create(messages=[{"role": "user", "content": rag_prompt}], **self.model_args)
        return response.choices[0].message.content
    
    def list_to_markdown(self, list_items):
        markdown_content = ""

        # 对于列表中的每个项目，添加一个带数字的列表项
        for index, item in enumerate(list_items, start=1):
            markdown_content += f"{index}. {item}\n"

        return markdown_content
    
    def rag_ar(self, query, related_code, embedding_recall):
        rag_ar_prompt = rag_ar_prompt_str.format(
            query=query,
            related_code=related_code,
            embedding_recall=embedding_recall,
        )
        if self.model_args['model'] == "gemini-2.0-flash-thinking-exp-01-21":
            response = self.llm.chat.completions.create(messages=[{"role": "user", "content": rag_ar_prompt}], **self.model_args)
        else:
            response = self.llm.chat.completions.create(messages=[{"role": "user", "content": rag_ar_prompt}], response_format={"type": "json_object"}, **self.model_args)
        return response.choices[0].message.content
    
    def generate_queries(self, query_str: str, num_queries: int = 4):
        fmt_prompt = query_generation_prompt_str.format(
            num_queries=num_queries, query=query_str
        )
        response = self.llm.chat.completions.create(messages=[{"role": "user", "content": fmt_prompt}], **self.model_args)
        queries = response.choices[0].message.content.split("\n")
        return [query for query in queries if query != "```" and query != ""]

    def extract_response(self, response: str) -> str:
        """
        Extract the response from the LLM output.

        Args:
            response (str): The response from the LLM.

        Returns:
            str: The extracted response.
        """
        try:
            json_response = json.loads(response)
            if isinstance(json_response, dict):
                function_name = json_response.get("function_name", "")
                function = json_response.get("function", "")
                return [function.strip(), function_name.strip()]
            else:
                self.logger.info(f"Failed to extract response from: {response}")
                return ["", ""]
        except json.JSONDecodeError as e:
            self.logger.info(f"Failed to extract response from: {response}")
            return ["", ""]
    
    def attempt_rag_ar(self, prompt, uni_code, retrieved_documents, max_attempts=10):
        attempt = 0
        final_results = ["", ""]
        while attempt < max_attempts:
            bot_message = self.rag_ar(prompt, uni_code, retrieved_documents)
            final_results = self.extract_response(bot_message)
            if final_results[0] != "" and final_results[1] != "":
                break
            attempt += 1
            self.logger.info(f"Retrying RAG_AR, attempt {attempt}")
            if attempt == max_attempts:
                final_results = ["", ""]
                break
        self.logger.info(f"Final bot_message after RAG_AR: {bot_message}")
        return final_results
    
    def respond(self, message, instruction=None):
        """
        Respond to a user query by the following steps:
        Query generation → Keyword extraction → Document retrieval → Reranking → Code retrieval → Response generation
        """
        self.logger.info("Starting response generation.")
        
        # Step 1: Format the chat prompt
        prompt = self.textanslys.format_chat_prompt(message, instruction)
        self.logger.info(f"Formatted prompt: {prompt}")
        
        questions = self.textanslys.keyword(prompt)
        self.logger.info(f"Generated keywords from prompt: {questions}")
        
        # Step 2: Generate additional queries
        prompt_queries = self.generate_queries(prompt, 4)
        self.logger.info(f"Generated queries: {prompt_queries}")
        
        all_results: List[Document] = []
        
        # Step 3: Query the VectorStoreManager for each query
        for query in prompt_queries:
            self.logger.info(f"Querying vector store with: {query}")
            query_results = self.vectorstore.similarity_search(query, k=5)
            for result in query_results:
                self.logger.info(f"Results for query '{query}': {result.page_content}")
            all_results.extend(query_results)

        # Step 4: Deduplicate results by content
        unique_results = {result.page_content: result for result in all_results}.values()
        unique_documents = [result.page_content for result in unique_results]
        self.logger.info(f"Unique documents: {unique_documents}")
        
        unique_code = [
            "--------------\n\n" + result.metadata['code_source_file'] + "\n\n" + result.metadata['code_content'] + "--------------\n\n" for result in unique_results
        ]
        self.logger.info(f"Unique code content: {unique_code}")
        
        # Step 5: Rerank documents based on relevance
        retrieved_documents = self.rerank(message, unique_documents)
        self.logger.info(f"Reranked documents: {retrieved_documents}")
        
        # Step 6: Generate a response using RAG (Retrieve and Generate)
        response = self.rag(prompt, retrieved_documents)
        chunkrecall = self.list_to_markdown(retrieved_documents)
        self.logger.info(f"RAG-generated response: {response}")
        self.logger.info(f"Markdown chunk recall: {chunkrecall}")
        
        bot_message = str(response)
        self.logger.info(f"Initial bot_message: {bot_message}")
        
        # Step 7: Perform NER and queryblock processing
        try:
            keyword = str(json.loads(self.textanslys.nerquery(bot_message))['name'])
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse JSON for bot_message: {e}")
            keyword = ""

        try:
            keywords = str(json.loads(self.textanslys.nerquery(str(prompt) + str(questions)))['name'])
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse JSON for prompt and questions: {e}")
            keywords = ""

        self.logger.info(f"Extracted keywords: {keyword}, {keywords}")
        
        codez, mdz = self.textanslys.queryblock(keyword)
        codey, mdy = self.textanslys.queryblock(keywords)
        self.logger.info(f"Z: {codez}, {mdz}")
        self.logger.info(f"Y: {codey}, {mdy}")
        
        # Ensure all returned items are lists
        codez = codez if isinstance(codez, list) else [codez]
        mdz = mdz if isinstance(mdz, list) else [mdz]
        codey = codey if isinstance(codey, list) else [codey]
        mdy = mdy if isinstance(mdy, list) else [mdy]
        
        # Step 8: Merge and deduplicate results
        codex = list(dict.fromkeys(codez + codey))
        md = list(dict.fromkeys(mdz + mdy))
        ## Ensure md is a flat list
        flat_md = []
        for item in md:
            if isinstance(item, list):
                flat_md.extend(item)
            else:
                flat_md.append(item)
        unique_mdx = list(set(flat_md))
        uni_codex = list(dict.fromkeys(codex))
        uni_md = list(dict.fromkeys(unique_mdx))
        self.logger.info(f"Unique markdown: {uni_md}")
        
        # Convert to Markdown format
        codex_md = self.textanslys.list_to_markdown(uni_codex)
        self.logger.info(f"Unique code: {codex_md}")
        retrieved_documents = list(dict.fromkeys(retrieved_documents + uni_md))
        
        # Final rerank and response generation
        retrieved_documents = self.rerank(message, retrieved_documents)
        self.logger.info(f"Final retrieved documents after rerank: {retrieved_documents}")
        
        uni_code = self.rerank(
            message, list(dict.fromkeys(uni_codex + unique_code))
        )
        self.logger.info(f"Final unique code after rerank: {uni_code}")
        
        unique_code_md = self.textanslys.list_to_markdown(unique_code)
        self.logger.info(f"Unique code in Markdown: {unique_code_md}")
        
        # Generate final response using RAG_AR
        final_results = self.attempt_rag_ar(prompt, uni_code, retrieved_documents)

        return final_results