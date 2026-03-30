"""
ヒアリングワークフロー API

IntakeWorkflow の開始・メッセージ送信・応答取得を REST API で提供する。
Temporal ワークフローへは文字列ベースで参照（ワークフローコード不要）。
"""

import base64
import json as _json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel

from routers.auth import get_current_user

router = APIRouter(prefix="/intake", tags=["intake"])

TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "default")


# ---------------------------------------------------------------------------
# リクエスト / レスポンス モデル
# ---------------------------------------------------------------------------
class StartRequest(BaseModel):
    user_name: str = ""


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
async def start_intake(
    request: Request, body: StartRequest, user_id: str = Depends(get_current_user),
):
    """IntakeWorkflow を開始し、workflow_id を返す。"""
    client = request.app.state.temporal
    workflow_id = f"intake-{uuid.uuid4().hex[:8]}"

    await client.start_workflow(
        "IntakeWorkflow",
        args=[workflow_id, user_id, body.user_name],
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


# ---------------------------------------------------------------------------
# 画像アップロード
# ---------------------------------------------------------------------------
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadResult(BaseModel):
    status: str
    gcs_uri: str


def _get_gcs_client():
    """GCS_SA_KEY_BASE64 環境変数からクレデンシャルを生成して Storage Client を返す。"""
    from google.cloud import storage
    from google.oauth2 import service_account

    key_b64 = os.getenv("GCS_SA_KEY_BASE64", "")
    if key_b64:
        decoded = base64.b64decode(key_b64)
        info = _json.loads(decoded.decode("utf-8"))
        credentials = service_account.Credentials.from_service_account_info(info)
        return storage.Client(credentials=credentials, project=credentials.project_id)
    return None


@router.post("/{workflow_id}/upload-image", response_model=UploadResult)
async def upload_image(
    workflow_id: str,
    file: UploadFile,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """画像を GCS にアップロードし、ワークフローに通知する。"""
    # バリデーション
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="画像ファイルのみアップロード可能です")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="ファイルサイズが 10MB を超えています")

    # GCS にアップロード
    gcs_client = _get_gcs_client()
    if gcs_client is None:
        raise HTTPException(status_code=500, detail="GCS が設定されていません")

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME が未設定です")

    ext = (file.filename or "image").rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    blob_name = f"uploads/{uuid.uuid4().hex}.{ext}"
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type=file.content_type)
    gcs_uri = f"gs://{bucket_name}/{blob_name}"

    # ワークフローに画像アップロードシグナルを送信
    client = request.app.state.temporal
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("image_uploaded", gcs_uri)

    return UploadResult(status="uploaded", gcs_uri=gcs_uri)
