import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from config.database import engine
from config.mongo import create_mongo_client
from init import init_city_info
from scrap.weather_info import get_weather_info


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
