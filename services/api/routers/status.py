"""
ステータスダッシュボード API

ユーザーの削除依頼の進捗状況をフロントエンドに提供する。
Supabase からデータを取得し、サマリーと URL 一覧を返す。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from routers.auth import get_current_user

router = APIRouter(prefix="/status", tags=["status"])


# ---------------------------------------------------------------------------
# レスポンスモデル
# ---------------------------------------------------------------------------
class StatusSummary(BaseModel):
    detected_url_count: int
    search_block_submitted: int
    hosting_removal_submitted: int


class WorkflowLog(BaseModel):
    id: str
    workflow_type: str
    status: str
    started_at: str
    finished_at: str | None


class TargetUrlWithLogs(BaseModel):
    id: str
    url: str
    website_name: str | None
    source_status: str
    search_status: str
    created_at: str
    workflow_logs: list[WorkflowLog]


# ---------------------------------------------------------------------------
# ワークフロータイプのカテゴリ分類
# ---------------------------------------------------------------------------
SEARCH_BLOCK_TYPES = {"search_deindex_google", "search_deindex_bing", "cache_removal"}
HOSTING_REMOVAL_TYPES = {"hosting_removal", "dmca_takedown"}


def _get_supabase(request: Request):
    """app.state から Supabase クライアントを取得する。"""
    sb = getattr(request.app.state, "supabase", None)
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    return sb


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
@router.get("/summary", response_model=StatusSummary)
async def get_summary(
    request: Request, user_id: str = Depends(get_current_user)
):
    """サマリーメトリクスを返す。"""
    sb = _get_supabase(request)

    # ユーザーの removal_requests を取得
    req_resp = sb.table("removal_requests").select("id").eq("user_id", user_id).execute()
    request_ids = [r["id"] for r in req_resp.data] if req_resp.data else []

    if not request_ids:
        return StatusSummary(
            detected_url_count=0,
            search_block_submitted=0,
            hosting_removal_submitted=0,
        )

    # target_urls を取得
    url_resp = (
        sb.table("target_urls")
        .select("id")
        .in_("request_id", request_ids)
        .execute()
    )
    url_ids = [u["id"] for u in url_resp.data] if url_resp.data else []
    detected_url_count = len(url_ids)

    if not url_ids:
        return StatusSummary(
            detected_url_count=0,
            search_block_submitted=0,
            hosting_removal_submitted=0,
        )

    # workflow_logs で完了済みをカウント
    log_resp = (
        sb.table("url_workflow_logs")
        .select("workflow_type")
        .in_("target_url_id", url_ids)
        .eq("status", "completed")
        .execute()
    )

    search_block = 0
    hosting_removal = 0
    for log in log_resp.data or []:
        wt = log["workflow_type"]
        if wt in SEARCH_BLOCK_TYPES:
            search_block += 1
        elif wt in HOSTING_REMOVAL_TYPES:
            hosting_removal += 1

    return StatusSummary(
        detected_url_count=detected_url_count,
        search_block_submitted=search_block,
        hosting_removal_submitted=hosting_removal,
    )


@router.get("/urls", response_model=list[TargetUrlWithLogs])
async def get_urls(
    request: Request, user_id: str = Depends(get_current_user)
):
    """ユーザーの全 target_urls をワークフローログ付きで返す。"""
    sb = _get_supabase(request)

    # ユーザーの removal_requests を取得
    req_resp = sb.table("removal_requests").select("id").eq("user_id", user_id).execute()
    request_ids = [r["id"] for r in req_resp.data] if req_resp.data else []

    if not request_ids:
        return []

    # target_urls を取得
    url_resp = (
        sb.table("target_urls")
        .select("id, url, website_name, source_status, search_status, created_at")
        .in_("request_id", request_ids)
        .order("created_at", desc=False)
        .execute()
    )

    urls = url_resp.data or []
    if not urls:
        return []

    # workflow_logs を一括取得
    url_ids = [u["id"] for u in urls]
    log_resp = (
        sb.table("url_workflow_logs")
        .select("id, target_url_id, workflow_type, status, started_at, finished_at")
        .in_("target_url_id", url_ids)
        .order("started_at", desc=False)
        .execute()
    )

    # URL ごとにグルーピング
    logs_by_url: dict[str, list[dict]] = {}
    for log in log_resp.data or []:
        tid = log["target_url_id"]
        logs_by_url.setdefault(tid, []).append(log)

    result = []
    for u in urls:
        url_logs = logs_by_url.get(u["id"], [])
        result.append(
            TargetUrlWithLogs(
                id=u["id"],
                url=u["url"],
                website_name=u.get("website_name"),
                source_status=u["source_status"],
                search_status=u["search_status"],
                created_at=u["created_at"],
                workflow_logs=[
                    WorkflowLog(
                        id=l["id"],
                        workflow_type=l["workflow_type"],
                        status=l["status"],
                        started_at=l["started_at"],
                        finished_at=l.get("finished_at"),
                    )
                    for l in url_logs
                ],
            )
        )

    return result
