import json
import re
from typing import Dict, Any, Optional, Union

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pymongo.database import Database
from redis import Redis

from .deepseek import create_deepseek


def get_agent_prompt(agent_id: int, db: Optional[Database], redis: Optional[Redis]) -> str:
    """
    获取 Agent 提示词，优先读取 Redis 缓存，无缓存则查库并写入缓存
    """
    redis_key = f"agent:{agent_id}:prompt"

    # 1. Try Redis
    if redis is not None:
        cached = redis.get(redis_key)
        if cached:
            return cached.decode("utf-8") if isinstance(cached, bytes) else str(cached)

    # 2. Try MongoDB
    prompt = ""
    if db is not None:
        col = db.get_collection("agent")
        doc = col.find_one({"_id": agent_id})
        if doc:
            prompt = doc.get("prompt") or doc.get("content") or ""

    # 3. Update Redis (set even if empty to avoid cache penetration, or maybe not?)
    # 这里选择写入，哪怕是空字符串，避免重复查库
    if redis:
        # 设置一个过期时间，比如 1 小时，以便更新
        redis.set(redis_key, prompt, ex=3600)

    return prompt


def run_llm_chat(prompt: str, user_content: str, model: Optional[ChatOpenAI] = None) -> str:
    """
    基础 LLM 调用
    """
    chat = model or create_deepseek()
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_content),
    ]
    res = chat.invoke(messages)
    return res.content


def clean_html_content(content: str) -> str:
    """
    清理 HTML 输出中的 Markdown 代码块标记
    """
    content = content.strip()
    # 匹配 ```html ... ```
    m = re.search(r"^```(?:\s*html)?\s*\n([\s\S]*?)\n```$", content, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    # 匹配简单的 ``` ... ```
    if content.startswith("```") and content.endswith("```"):
        return content.strip("`").strip()
    return content


def run_one(input_data: Union[Dict[str, Any], str],
            db: Optional[Database],
            redis: Optional[Redis],
            agent_id: int) -> str:
    """
    通用 Agent 执行入口
    :param input_data: 输入数据，可以是字典（如天气信息）或字符串（如问题）
    :param db: Mongo连接
    :param redis: Redis连接
    :param agent_id: Agent ID
    """
    # 1. 获取提示词
    prompt = get_agent_prompt(agent_id, db, redis)
    print(f"Agent {agent_id} prompt: {prompt}")
    # 2. 构造用户输入内容
    if isinstance(input_data, (dict, list)):
        json_str = json.dumps(input_data, ensure_ascii=False)
        # 兼容旧逻辑：天气 Agent (1, 2) 需要特定的前缀说明
        # 未来如果 agent 增多，建议在数据库配置 agent_type 或 template
        if agent_id == 1:
            user_content = f"根据以下天气数据生成markdown内容：\n{json_str}"
        elif agent_id == 2:
            user_content = f"根据以下天气数据生成html内容：\n{json_str}"
        else:
            # 默认情况，直接给 JSON
            user_content = json_str
    else:
        # 字符串直接作为输入
        user_content = str(input_data)

    # 3. 调用 LLM
    content = run_llm_chat(prompt, user_content)

    # 4. 后处理（针对 HTML）
    # 假设 agent_id=2 总是输出 HTML，或者根据内容判断
    if agent_id == 2:
        content = clean_html_content(content)

    return content
