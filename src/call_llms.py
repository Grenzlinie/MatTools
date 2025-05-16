import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI

load_dotenv()

def load_llm(llm_name: str = None) -> OpenAI:
    """
    Load a large language model (LLM) based on the specified name and path.

    Args:
        llm_name (str, optional): The name of the LLM to load. Currently supports "OpenAI".
        llm_path (str, optional): The path to the LLM if it is not OpenAI.

    Returns:
        OpenAI: An instance of the OpenAI client if llm_name is "OpenAI".

    Raises:
        ValueError: If the provided llm_name is unsupported or if both llm_name and llm_path are not provided.
    """
    load_dotenv()
    if llm_name == "deepseek-reasoner" or llm_name == "deepseek-chat":
        deepseek_key = os.getenv("DEEPSEEK_OFFICIAL")
        if not deepseek_key:
            raise EnvironmentError("DeepSeek API key not set in environment.")
        return OpenAI(
            api_key=deepseek_key,
            base_url="https://api.deepseek.com/v1",
            timeout=600,
            max_retries=3,
        )
    elif llm_name == "gemini-2.0-flash-thinking-exp-01-21" or llm_name == "gemini-2.0-flash" or llm_name == "gemini-2.0-pro-exp-02-05":
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise EnvironmentError("Gemini API key not set in environment.")
        return OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=600,
            max_retries=3,
        )
    elif llm_name == "gpt-3.5-turbo-0125" or llm_name == "gpt-4o-2024-08-06" or llm_name == "gpt-4o-mini-2024-07-18" or llm_name == "gpt-4.5-preview-2025-02-27":
        return OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=600,
            max_retries=3,
        )
    else:
        raise ValueError(f"Unsupported LLM: {llm_name}")

def load_chat_llm(model_name:str, temperature:float|int = 0.7) -> ChatOpenAI:
    """
    Load a large language model (LLM) from OpenAI.
    
    Args:
        model_name (str): The name of the model to load. Example: 'gpt-4o-mini-2024-07-18'.
        
    Returns:
        ChatOpenAI: The loaded LLM.
    """
    if model_name == "deepseek-reasoner" or model_name == "deepseek-chat":
        deepseek_key = os.getenv("DEEPSEEK_OFFICIAL")
        if not deepseek_key:
            raise EnvironmentError("DeepSeek API key not set in environment.")
        llm = ChatOpenAI(model=model_name, api_key=deepseek_key, base_url="https://api.deepseek.com/v1", timeout=600, max_retries=3, temperature=temperature)
    elif model_name == "gemini-2.0-flash-thinking-exp-01-21" or model_name == "gemini-2.0-flash" or model_name == "gemini-2.0-pro-exp-02-05":
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise EnvironmentError("Gemini API key not set in environment.")
        llm = ChatOpenAI(model=model_name, api_key=gemini_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", timeout=600, max_retries=3, temperature=temperature)
    elif model_name == "gpt-3.5-turbo-0125" or model_name == "gpt-4o-2024-08-06" or model_name == "gpt-4o-mini-2024-07-18" or model_name == "gpt-4.5-preview-2025-02-27" :
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise EnvironmentError("OPENAI_KEY API key not set in environment.")
        llm = ChatOpenAI(model=model_name, api_key=openai_key, base_url="https://test-cloudflare-7nq.pages.dev/v1/", timeout=600, max_retries=3, temperature=temperature)
    else:
        raise ValueError("Unsupported model.")
    return llm

def load_embedding_model(model_name:str) -> OpenAIEmbeddings:
    """
    Load an embedding model from OpenAI.

    Args:
        model_name (str): The name of the embedding model to load. Example: "text-embedding-3-large".

    Returns:
        OpenAIEmbeddings: The loaded embedding model.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise EnvironmentError("OPENAI_KEY API key not set in environment.")
    embedding_model = OpenAIEmbeddings(model=model_name, api_key=openai_key, base_url="https://test-cloudflare-7nq.pages.dev/v1/", timeout=600, max_retries=3)
    return embedding_model

if __name__ == "__main__":
    llm = load_llm("gpt-4o-mini-2024-07-18")
