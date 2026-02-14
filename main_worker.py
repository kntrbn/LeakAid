"""
Temporal Worker 起動スクリプト（エントリーポイント）。
docker-compose から渡される環境変数を読み込み、Temporal Server に接続する。
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# temporal を import できるように PYTHONPATH を設定
# コンテナ内では /app/leakaid-backend/temporal にある
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "leakaid-backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker() -> None:
    # 環境変数から Temporal 設定を取得
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = os.getenv("TEMPORAL_PORT", "7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "default")
    use_tls = os.getenv("TEMPORAL_USE_TLS", "false").lower() == "true"
    api_key = os.getenv("TEMPORAL_API_KEY")
    
    address = f"{host}:{port}"
    
    logger.info(
        "Temporal: address=%s namespace=%s task_queue=%s",
        address,
        namespace,
        task_queue,
    )
    
    # Temporal に接続
    from temporalio.client import Client
    
    connect_kwargs = {
        "target_host": address,
        "namespace": namespace,
        "tls": use_tls,
    }
    if api_key:
        connect_kwargs["api_key"] = api_key
    
    client = await Client.connect(**connect_kwargs)
    logger.info("Connected to Temporal: %s", address)
    
    # TODO: ワークフローとアクティビティを追加
    logger.warning("No workflows or activities registered. Worker will not process any tasks.")
    logger.info("Temporal connection verified. Add workflows to start processing.")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
