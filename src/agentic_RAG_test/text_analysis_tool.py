import sys
sys.path.append("..")
from src.json_handler import JsonFileProcessor
from openai import OpenAI

class TextAnalysisTool:
    def __init__(self, llm: OpenAI, db_path, model_args):
        self.jsonsearch = JsonFileProcessor(db_path)
        self.llm = llm
        self.db_path = db_path
        self.model_args = model_args

    def keyword(self, query):
        prompt = f"Please provide a list of Code keywords according to the following query, please output no more than 3 keywords, Input: {query}, Output:"
        response = self.llm.chat.completions.create(messages=[{"role": "user", "content": prompt}], **self.model_args)
        return response.choices[0].message.content

    def format_chat_prompt(self, message, instruction):
        if instruction is None or instruction == "":
            prompt = f"User: {message}\nAssistant: "
        else:
            prompt = f"System:{instruction}\nUser: {message}\nAssistant: "
        return prompt

    def queryblock(self, message):
        code_results, md_results = self.jsonsearch.search_code_contents_by_name(
            self.db_path, message
        )
        return code_results, md_results

    def list_to_markdown(self, search_result):
        markdown_str = ""
        # 遍历列表，将每个元素转换为Markdown格式的项
        for index, content in enumerate(search_result, start=1):
            # 添加到Markdown字符串中，每个项后跟一个换行符
            markdown_str += f"{index}. {content}\n\n"

        return markdown_str

    def nerquery(self, message):
        instruction = """
Extract the most relevant Pymatgen class or function based on the following instruction:

The output must strictly be a pure function name or class name, without any additional characters.
Class or function names need to exist in Pymatgen, rather than being broadly defined or user-defined.
For example:
Pure function names: calculateSum, processData
Pure class names: MyClass, DataProcessor
The output function name or class name should be only one.

Please ensure the output follows this JSON format:
{
"type": "function" or "class",
"name": "name_of_the_function_or_class"
}
    """
        query = f"The input is shown as below:\n{message}\n\nAnd now directly give your Output:"
        if self.model_args['model'] == "gemini-2.0-flash-thinking-exp-01-21":
            response = self.llm.chat.completions.create(
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": query}
                ],
                **self.model_args
            )
        else:
            response = self.llm.chat.completions.create(
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                **self.model_args
            )
        return response.choices[0].message.content

