import os
from langchain_openai import ChatOpenAI


def create_deepseek(model: str = "deepseek-chat") -> ChatOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com"
    return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=0)
