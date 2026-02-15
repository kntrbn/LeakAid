"""
Google フォーム自動入力アクティビティ (PydanticAI + Playwright)

PydanticAI エージェントが Playwright ブラウザを操作して
Google フォームに自動入力・送信を行う。
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path

from temporalio import activity


@dataclass
class GoogleFormInput:
    """Google フォーム送信のための入力データ"""

    form_url: str  # Google フォーム URL
    form_data: dict[str, str]  # 質問テキスト → 回答のマッピング


def _get_gcs_client():
    """GCS_SA_KEY_BASE64 環境変数からクレデンシャルを生成して Storage Client を返す。"""
    import base64
    import json as _json

    from google.cloud import storage
    from google.oauth2 import service_account

    key_b64 = os.getenv("GCS_SA_KEY_BASE64", "")
    if key_b64:
        info = _json.loads(base64.b64decode(key_b64))
        credentials = service_account.Credentials.from_service_account_info(info)
        return storage.Client(credentials=credentials, project=credentials.project_id)
    # フォールバック: ADC（Application Default Credentials）
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
async def submit_google_form(input: GoogleFormInput) -> str:
    """
    PydanticAI + Playwright で Google フォームを自動入力・送信する。

    Args:
        input: フォーム URL と入力データ

    Returns:
        送信結果の文字列
    """
    activity.logger.info(f"Google Form 送信開始: {input.form_url}")
    activity.logger.info(
        f"入力データ: {json.dumps(input.form_data, ensure_ascii=False)}"
    )

    try:
        # Temporal サンドボックス制限を回避するためアクティビティ内で遅延インポート
        from playwright.async_api import async_playwright
        from temporal.activities._google_form_agent import agent
        from temporal.tools import BrowserDeps

        log_dir = os.getenv("LOG_DIR", "/app/logs")
        os.makedirs(log_dir, exist_ok=True)

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
                record_video_dir=log_dir,
                record_video_size={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            activity.logger.info("ブラウザ起動完了、フォームに遷移中...")
            await page.goto(input.form_url, wait_until="networkidle")
            activity.logger.info(f"フォーム読み込み完了: {page.url}")

            deps = BrowserDeps(
                page=page, form_data=input.form_data, screenshot_dir=log_dir
            )

            result = await agent.run(
                "フォームデータを確認し、Google フォームに入力して送信してください。",
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
                activity.logger.info(f"GCS アップロード完了: {gcs_uri}")

            # スクリーンショットも GCS にアップロード
            for png in Path(log_dir).glob("*.png"):
                png_uri = _upload_to_gcs(str(png))
                if png_uri:
                    activity.logger.info(f"GCS アップロード完了: {png_uri}")

        activity.logger.info(f"エージェント完了: {result.output}")
        return f"送信完了\n最終URL: {final_url}\n結果: {result.output}"

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        error_msg = f"Google Form 送信に失敗しました: {str(e)}\n{error_details}"
        activity.logger.error(error_msg)
        return error_msg
