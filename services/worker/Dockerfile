# LeakAid Temporal Worker 用コンテナ
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium とシステム依存パッケージをインストール
RUN playwright install --with-deps chromium

COPY connect.py .
COPY temporal/ ./temporal/

ENV PYTHONPATH=/app
CMD ["python", "connect.py"]
