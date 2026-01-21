FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /app/pyproject.toml
RUN python -m pip install --upgrade pip
RUN pip install fastapi uvicorn sqlmodel SQLAlchemy psycopg2-binary python-dotenv requests pymongo redis langchain langchain-openai
COPY . /app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
