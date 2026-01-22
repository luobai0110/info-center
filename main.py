import os
from contextlib import asynccontextmanager

import requests
from dotenv import load_dotenv
from fastapi import FastAPI

from config.database import engine
from config.mongo import create_mongo_client
from config.redis import create_redis_client
from init import init_city_info
from service.scrap.weather_info import get_weather_info, clean_future_weather_info
from service.ai.agent_runner import run_one
from pydantic import BaseModel

load_dotenv()


class WeatherNoticeRequest(BaseModel):
    city_code: str
    weather_type: int = 0
    agent_id: int = 1
    notice_type: int = 1


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
    app.state.redis = create_redis_client(os.getenv("REDIS_HOST", "192.168.1.4"), int(os.getenv("REDIS_PORT", "6379")))

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


@app.post("/api/info-center/weather/notice")
def send_weather_notice(req: WeatherNoticeRequest):
    data = get_weather_info(req.city_code, getattr(app.state, "mongo_db", None))
    print(f"原始数据: {data}")
    # 如果 weather_type 为 1，则进行数据精简
    ai_input_data = data
    if req.weather_type == 1:
        ai_input_data = clean_future_weather_info(data)
    print(f"数据清理后的数据{ai_input_data}")
    # agent_id: 1 -> markdown (agent_id=1), 2 -> html (agent_id=2)
    content = run_one(ai_input_data, getattr(app.state, "mongo_db", None), getattr(app.state, "redis", None),
                      req.agent_id)
    # notice_type=4 => dingding ，notice_type=2 ==> email
    if req.notice_type == 4:
        ding_url = os.getenv("HTTP_NOTICE_URL") + "/notice/dingding"
        params = {
            "message": content,
            "from": "@system",
            "to": "@doomer",
            "type": req.notice_type,
            "title": "天气预报"
        }
        resp = requests.post(ding_url, json=params)
        return {"resp": resp.text, "params": params}
    elif req.notice_type == 2:
        mail_url = os.getenv("HTTP_NOTICE_URL") + "/notice/email"
        params = {
            "message": content,
            "from": "doomer@yuanzhou.site",
            "to": "yuanzhou0110@qq.com",
            "type": req.notice_type,
            "title": "今日天气",
            "subject": "天气预报",
            "mailType": 1
        }
        resp = requests.post(mail_url, json=params)
        return {"resp": resp.text, "params": params}
    elif req.notice_type == 3:
        other_url = os.getenv("HTTP_NOTICE_URL") + "/notice/gotify"
        params = {
            "message": content,
            "from": "@system",
            "to": "@doomer",
            "type": req.notice_type,
            "title": "天气预报",
            "priority": 10
        }
        resp = requests.post(other_url, json=params)
        return {"resp": resp.text, "parmas": params}
    else:
        return {"status": "error", "message": "未知通知类型"}
