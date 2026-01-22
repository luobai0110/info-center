FROM ghcr.io/astral-sh/uv:0.9.26-python3.13-alpine AS uv_builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --format requirements-txt --output-file requirements.txt

FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY --from=uv_builder /app/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
