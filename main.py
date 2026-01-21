import logging
import os
from contextlib import asynccontextmanager

import requests
from dotenv import load_dotenv
from fastapi import FastAPI

from config.database import engine
from config.mongo import create_mongo_client
from config.redis import create_redis_client
from init import init_city_info
from scrap.weather_info import get_weather_info
from ai.agent_runner import run_all, run_one


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    print("Creating database...")
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    mongo_uri = os.getenv("MONGO_URL")
    mongo_db = os.getenv("MONGO_DB")
    print(f"Creating mongo client: {mongo_uri}")
    app.state.mongo_client = None
    app.state.mongo_db = None
    if mongo_uri and mongo_db:
        try:
            client, db = create_mongo_client(mongo_uri, mongo_db)
            app.state.mongo_client = client
            app.state.mongo_db = db
        except Exception as e:
            print(f"Mongo init failed: {e}")
    app.state.redis = create_redis_client("192.168.1.4", 6380)

    if os.getenv("INIT_CITY", "").lower() == "true":
        init_city_info()
    yield
    print("Closing database...")
    if app.state.mongo_client:
        app.state.mongo_client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/api/info-center/health")
def root():
    return {"status": "ok"}


@app.get("/api/info-center/weather/{city_code}")
def get_city_info(city_code: str):
    return get_weather_info(city_code, getattr(app.state, "mongo_db", None))


@app.get("/api/info-center/weather/{city_code}/ai")
def get_city_ai(city_code: str):
    data = get_weather_info(city_code, getattr(app.state, "mongo_db", None))
    ai_res = run_all(data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None))
    return {"data": data, "ai": ai_res}


@app.get("/api/info-center/weather/{city_code}/ai/markdown")
def get_city_ai_markdown(city_code: str):
    data = get_weather_info(city_code, getattr(app.state, "mongo_db", None))
    content = run_one(data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None), 1)
    return content


@app.get("/api/info-center/weather/inner/{city_code}/ai/markdown")
def get_city_ai_markdown(city_code: str):
    data = get_weather_info(city_code, getattr(app.state, "mongo_db", None))
    content = run_one(data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None), 1)
    ding_url = os.getenv("HTTP_NOTICE_URL") + "/notice/dingding"
    parmas = {
        "message": content,
        "from": "@system",
        "to": "@doomer",
        "type": 4,
        "title": "天气预报"
    }
    resp = requests.post(ding_url, json=parmas)
    return resp.json()


@app.get("/api/info-center/weather/{city_code}/ai/html")
def get_city_ai_html(city_code: str):
    data = get_weather_info(city_code, getattr(app.state, "mongo_db", None))
    content = run_one(data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None), 2)
    return content


@app.get("/api/info-center/weather/inner/{city_code}/ai/html")
def get_city_ai_html(city_code: str):
    data = get_weather_info(city_code, getattr(app.state, "mongo_db", None))
    content = run_one(data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None), 2)
    parmas = {
        "message": content,
        "from": "doomer@yuanzhou.site",
        "to": "yuanzhou0110@qq.com",
        "type": 1,
        "title": "今日天气",
        "subject": "天气预报",
        "mailType": 1
    }
    mail_url = os.getenv("HTTP_NOTICE_URL") + "/notice/email"
    resp = requests.post(mail_url, json=parmas)
    print(resp.text)
    return resp.json()
