# LeakAid Temporal Worker 用コンテナ
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main_worker.py .
COPY leakaid-backend/temporal ./leakaid-backend/temporal

ENV PYTHONPATH=/app
CMD ["python", "main_worker.py"]
