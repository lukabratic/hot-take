FROM python:3.11-slim

WORKDIR /app

# libstdc++6 is required by pandas/numpy wheels (mirrors backend/nixpacks.toml)
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
