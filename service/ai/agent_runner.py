import json
import re
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pymongo.database import Database
from redis import Redis

from .deepseek import create_deepseek


def load_prompts(db: Database) -> Dict[int, str]:
    col = db.get_collection("agent")
    p1 = col.find_one({"_id": 1}) or {}
    p2 = col.find_one({"_id": 2}) or {}
    return {
        1: p1.get("prompt") or p1.get("content") or "",
        2: p2.get("prompt") or p2.get("content") or "",
    }


def load_prompt(db: Database, agent_id: int) -> str:
    col = db.get_collection("agent")
    p = col.find_one({"_id": agent_id}) or {}
    return p.get("prompt") or p.get("content") or ""


def cache_prompts(redis: Optional[Redis], prompts: Dict[int, str]):
    if redis:
        if prompts.get(1) is not None:
            redis.set("agent:1:prompt", prompts[1])
        if prompts.get(2) is not None:
            redis.set("agent:2:prompt", prompts[2])


def cache_prompt(redis: Optional[Redis], agent_id: int, prompt: str):
    if redis:
        redis.set(f"agent:{agent_id}:prompt", prompt)


def run_agent(weather: Dict[str, Any], prompt: str, fmt: str, model: Optional[ChatOpenAI] = None) -> str:
    chat = model or create_deepseek()
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"根据以下天气数据生成{fmt}内容：\n{json.dumps(weather, ensure_ascii=False)}"),
    ]
    res = chat.invoke(messages)
    content = res.content
    if fmt == "html":
        m = re.search(r"^```(?:\s*html)?\s*\n([\s\S]*?)\n```$", content.strip(), re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1)
        if content.strip().startswith("```") and content.strip().endswith("```"):
            return content.strip().strip("`").strip()
    return content


def run_one(weather: Dict[str, Any], db: Optional[Database], redis: Optional[Redis], agent_id: int) -> str:
    fmt = "markdown" if agent_id == 1 else "html"
    prompt = load_prompt(db, agent_id) if db is not None else ""
    cache_prompt(redis, agent_id, prompt)
    return run_agent(weather, prompt, fmt)
