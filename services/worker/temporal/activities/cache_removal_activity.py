"""
Google Search キャッシュ削除申請アクティビティ (PydanticAI + Playwright)

PydanticAI エージェントが Playwright ブラウザを操作して
削除申請フォームに自動入力する。送信は行わない（手前で停止）。
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path

from temporalio import activity


@dataclass
class CacheRemovalInput:
    """キャッシュ削除申請の入力データ"""

    form_url: str  # 削除申請フォーム URL
    form_data: dict[str, str]  # フィールド名 → 値のマッピング


def _get_gcs_client():
    """GCS_SA_KEY_BASE64 環境変数からクレデンシャルを生成して Storage Client を返す。"""
    import base64
    import json as _json

    from google.cloud import storage
    from google.oauth2 import service_account

    key_b64 = os.getenv("GCS_SA_KEY_BASE64", "")
    if key_b64:
        decoded = base64.b64decode(key_b64)
        info = _json.loads(decoded.decode("utf-8"))
        credentials = service_account.Credentials.from_service_account_info(info)
        return storage.Client(credentials=credentials, project=credentials.project_id)
    return storage.Client()


def _upload_to_gcs(local_path: str) -> str | None:
    """ファイルを GCS バケットにアップロードする。環境変数未設定ならスキップ。"""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        return None
    try:
        client = _get_gcs_client()
        bucket = client.bucket(bucket_name)
        prefix = os.getenv("GCS_PREFIX", "logs/")
        blob_name = f"{prefix}{Path(local_path).name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        return f"gs://{bucket_name}/{blob_name}"
    except Exception as e:
        activity.logger.warning(f"GCS アップロード失敗 ({local_path}): {e}")
        return None


@activity.defn
async def fill_cache_removal_form(input: CacheRemovalInput) -> str:
    """
    PydanticAI + Playwright で削除申請フォームに自動入力する（送信はしない）。

    Args:
        input: フォーム URL と入力データ

    Returns:
        入力結果の文字列
    """
    activity.logger.info(f"キャッシュ削除申請開始: {input.form_url}")
    activity.logger.info(
        f"入力データ: {json.dumps(input.form_data, ensure_ascii=False)}"
    )

    try:
        from playwright.async_api import async_playwright
        from temporal.activities._cache_removal_agent import agent
        from temporal.tools import BrowserDeps

        log_dir = os.getenv("LOG_DIR", "/app/logs")
        video_dir = os.path.join(log_dir, "videos")
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)

        from playwright_stealth import Stealth

        stealth = Stealth()

        async with stealth.use_async(async_playwright()) as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                locale="ja-JP",
                record_video_dir=video_dir,
                record_video_size={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            activity.logger.info("ブラウザ起動完了、フォームに遷移中...")
            await page.goto(input.form_url, wait_until="networkidle")
            # フォーム要素が完全にインタラクティブになるまで待機
            import asyncio as _asyncio

            await _asyncio.sleep(2)
            activity.logger.info(f"フォーム読み込み完了: {page.url}")

            deps = BrowserDeps(
                page=page, form_data=input.form_data, screenshot_dir=log_dir
            )

            result = await agent.run(
                "フォームデータを確認し、削除申請フォームの全ステップを入力してください。"
                "「次へ」ボタンは押して先に進み、最終送信ボタンの直前で停止してください。",
                deps=deps,
            )

            final_url = page.url
            video_path = await page.video.path()
            await context.close()
            await browser.close()
            activity.logger.info(f"ビデオ保存先: {video_path}")

            # GCS にアップロード
            gcs_uri = _upload_to_gcs(str(video_path))
            if gcs_uri:
                activity.logger.info(f"GCS アップロード完了（動画）: {gcs_uri}")

            for png in Path(log_dir).glob("*.png"):
                png_uri = _upload_to_gcs(str(png))
                if png_uri:
                    activity.logger.info(f"GCS アップロード完了（スクショ）: {png_uri}")

        activity.logger.info(f"エージェント完了: {result.output}")
        return f"入力完了（送信未実行）\n最終URL: {final_url}\n結果: {result.output}"

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        error_msg = f"キャッシュ削除申請フォーム入力に失敗しました: {str(e)}\n{error_details}"
        activity.logger.error(error_msg)
        return error_msg
