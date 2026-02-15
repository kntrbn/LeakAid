"""
LeakAid FastAPI サーバー

フロントエンド（WeWeb）と Temporal ワークフローをつなぐ API ゲートウェイ。
Temporal への接続は文字列ベース参照で行い、ワークフローコードに依存しない。
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from temporalio.client import Client

from routers import intake


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に Temporal Client を接続し、アプリ全体で共有する。"""
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = os.getenv("TEMPORAL_PORT", "7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    use_tls = os.getenv("TEMPORAL_USE_TLS", "false").lower() == "true"
    api_key = os.getenv("TEMPORAL_API_KEY")

    connect_kwargs = {
        "target_host": f"{host}:{port}",
        "namespace": namespace,
        "tls": use_tls,
    }
    if api_key:
        connect_kwargs["api_key"] = api_key

    app.state.temporal = await Client.connect(**connect_kwargs)
    yield


app = FastAPI(
    title="LeakAid API",
    description="削除依頼管理 API",
    lifespan=lifespan,
)

# CORS（WeWeb など外部フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
