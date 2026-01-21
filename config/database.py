import os

from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
database = os.getenv("DB_DATABASE")
port = os.getenv("DB_PORT") or "5432"

if username and password and host and database:
    # 打印环境变量
    print(f"DB_USERNAME: {username}")
    print(f"DB_PASSWORD: {password}")
    print(f"DB_HOST: {host}")
    print(f"DB_DATABASE: {database}")
    print(f"DB_PORT: {port}")
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database,
    )
    engine = create_engine(db_url, echo=True)
else:
    engine = create_engine("sqlite:///./info.db", echo=True)
