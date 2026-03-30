"""
LeakAid FastAPI サーバー

フロントエンド（WeWeb）と Temporal ワークフローをつなぐ API ゲートウェイ。
Temporal への接続は文字列ベース参照で行い、ワークフローコードに依存しない。
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client as create_supabase_client
from temporalio.client import Client

from routers import intake, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に Temporal Client と Supabase Client を接続し、アプリ全体で共有する。"""
    # Temporal
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

    # Supabase
    supabase_url = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if supabase_url and supabase_key:
        app.state.supabase = create_supabase_client(supabase_url, supabase_key)
    else:
        app.state.supabase = None

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
app.include_router(status.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
