"""
ヒアリングワークフロー API

IntakeWorkflow の開始・メッセージ送信・応答取得を REST API で提供する。
Temporal ワークフローへは文字列ベースで参照（ワークフローコード不要）。
"""

import os
import uuid

import jwt
from jwt import PyJWKClient
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter(prefix="/intake", tags=["intake"])

TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "default")
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))

# Supabase JWKS（公開鍵）の取得クライアント
_jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
_security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    """JWT を検証し user_id (sub) を返す。"""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# リクエスト / レスポンス モデル
# ---------------------------------------------------------------------------
class StartResponse(BaseModel):
    workflow_id: str


class MessageRequest(BaseModel):
    message: str


class ResponseResult(BaseModel):
    response: str


class StatusResult(BaseModel):
    is_complete: bool


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
@router.post("/start", response_model=StartResponse)
async def start_intake(request: Request, user_id: str = Depends(get_current_user)):
    """IntakeWorkflow を開始し、workflow_id を返す。"""
    client = request.app.state.temporal
    workflow_id = f"intake-{uuid.uuid4().hex[:8]}"

    await client.start_workflow(
        "IntakeWorkflow",
        workflow_id,  # request_id 引数
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return StartResponse(workflow_id=workflow_id)


@router.post("/{workflow_id}/message")
async def send_message(
    workflow_id: str, body: MessageRequest, request: Request,
    user_id: str = Depends(get_current_user),
):
    """ユーザーメッセージをワークフローにシグナル送信する。"""
    client = request.app.state.temporal
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("user_message", body.message)
    return {"status": "sent"}


@router.get("/{workflow_id}/response", response_model=ResponseResult)
async def get_response(workflow_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """エージェントの最新応答をクエリで取得する。"""
    client = request.app.state.temporal
    handle = client.get_workflow_handle(workflow_id)
    response = await handle.query("current_response")
    return ResponseResult(response=response)


@router.get("/{workflow_id}/status", response_model=StatusResult)
async def get_status(workflow_id: str, request: Request, user_id: str = Depends(get_current_user)):
    """ヒアリングの完了状態をクエリで取得する。"""
    client = request.app.state.temporal
    handle = client.get_workflow_handle(workflow_id)
    is_complete = await handle.query("is_complete")
    return StatusResult(is_complete=is_complete)
