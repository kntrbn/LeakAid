"""
キャッシュ削除申請ワークフローのテストスクリプト（Temporal 経由で実行）
"""
import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

# プロジェクトルートを sys.path に追加
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from dotenv import load_dotenv

# .env を探して読み込む
env_path = root / ".env"
if not env_path.exists():
    env_path = root.parent.parent / ".env"
load_dotenv(env_path)


async def main():
    from temporalio.client import Client

    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = os.getenv("TEMPORAL_PORT", "7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "default")
    use_tls = os.getenv("TEMPORAL_USE_TLS", "false").lower() == "true"
    api_key = os.getenv("TEMPORAL_API_KEY")

    connect_kwargs = {
        "target_host": f"{host}:{port}",
        "namespace": namespace,
        "tls": use_tls,
    }
    if api_key:
        connect_kwargs["api_key"] = api_key

    client = await Client.connect(**connect_kwargs)

    form_url = os.getenv(
        "GOOGLE_REMOVAL_URL",
        "https://support.google.com/websearch/contact/content_removal_form?hl=ja",
    )

    # ダミーデータ（エージェントがフォーム構造を解析して適切に入力する）
    form_data = {
        # ステップ1: Google Support フォーム
        "削除理由カテゴリ": "自分の個人情報が含まれている",
        "居住国": "日本",
        # ステップ2以降: 詳細入力
        "名前": "テスト太郎",
        "メールアドレス": "test@example.com",
        "削除対象URL": "https://example.com/test-content",
        "Google検索結果URL": "https://www.google.com/search?q=test+content",
        "削除理由": "テスト用のダミー申請です。実際の削除は行いません。",
    }

    workflow_id = f"cache-removal-test-{uuid4().hex[:8]}"

    print(f"ワークフロー起動中... (ID: {workflow_id})")
    print(f"フォームURL: {form_url}")
    print(f"データ: {form_data}")
    print()

    from temporal.activities.cache_removal_activity import CacheRemovalInput

    input_data = CacheRemovalInput(form_url=form_url, form_data=form_data)

    result = await client.execute_workflow(
        "CacheRemovalWorkflow",
        input_data,
        id=workflow_id,
        task_queue=task_queue,
    )

    print("=" * 60)
    print("結果:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
