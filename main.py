import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from config.database import engine
from init import init_city_info

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    print("Creating database...")
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    if os.getenv("INIT_CITY") == "TRUE":
        init_city_info()
    yield
    print("Closing database...")


app = FastAPI(lifespan=lifespan)


@app.get("/api/info-center/health")
def root():
    return {"status": "ok"}
