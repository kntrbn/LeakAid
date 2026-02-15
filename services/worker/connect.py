"""
Temporal Worker 起動スクリプト（エントリーポイント）。
docker-compose から渡される環境変数を読み込み、Temporal Server に接続する。
"""
import asyncio
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue

# temporal を import できるように PYTHONPATH を設定
# コンテナ内では /app/temporal にある
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))


# ---------------------------------------------------------------------------
# Datadog ログハンドラー
# ---------------------------------------------------------------------------
class DatadogLogHandler(logging.Handler):
    """Datadog Logs HTTP API にログをバッチ送信するハンドラー"""

    INTAKE_URL = "https://http-intake.logs.{site}/api/v2/logs"
    FLUSH_INTERVAL = 5  # 秒
    BATCH_SIZE = 50

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("DD_API_KEY", "")
        self.site = os.getenv("DD_SITE", "datadoghq.com")
        self.service = os.getenv("DD_SERVICE", "leakaid-worker")
        self.env = os.getenv("DD_ENV", "dev")
        self._queue: Queue = Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "message": self.format(record),
            "ddsource": "python",
            "ddtags": f"env:{self.env},service:{self.service}",
            "service": self.service,
            "hostname": os.getenv("HOSTNAME", "worker"),
            "level": record.levelname.lower(),
            "logger.name": record.name,
            "timestamp": int(record.created * 1000),
        }
        # ログレコードに追加属性があれば含める
        if hasattr(record, "workflow_id"):
            entry["workflow_id"] = record.workflow_id
        if hasattr(record, "activity_type"):
            entry["activity_type"] = record.activity_type
        self._queue.put(entry)

    def _flush_loop(self) -> None:
        url = self.INTAKE_URL.format(site=self.site)
        while not self._stop.is_set():
            time.sleep(self.FLUSH_INTERVAL)
            self._send_batch(url)
        # 終了時に残りを送信
        self._send_batch(url)

    def _send_batch(self, url: str) -> None:
        import urllib.request

        batch = []
        while len(batch) < self.BATCH_SIZE:
            try:
                batch.append(self._queue.get_nowait())
            except Empty:
                break
        if not batch:
            return
        try:
            body = json.dumps(batch, ensure_ascii=False, separators=(",", ":")).encode()
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "DD-API-KEY": self.api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception:
            return  # ログ送信失敗はサイレントに無視（無限ループ防止）

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=10)
        super().close()


def _setup_logging() -> None:
    """ロギングを設定（コンソール + Datadog）"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # コンソール出力
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root_logger.addHandler(console)

    # Datadog（DD_API_KEY が設定されている場合のみ）
    if os.getenv("DD_API_KEY"):
        dd = DatadogLogHandler()
        dd.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(dd)
        root_logger.info("Datadog logging enabled (site=%s, service=%s)", dd.site, dd.service)


_setup_logging()
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
    
    # Temporal に接続（Client として）
    from temporalio.client import Client
    from temporalio.worker import Worker
    
    # 全てのワークフローとアクティビティを import
    from temporal import activities, workflows  # activities を先に import（workflows が activities を参照するため）
    
    # 全てのワークフローとアクティビティを取得
    all_workflows = [getattr(workflows, name) for name in workflows.__all__]
    all_activities = [getattr(activities, name) for name in activities.__all__]
    
    logger.info(f"Loaded {len(all_workflows)} workflows and {len(all_activities)} activities")
    
    connect_kwargs = {
        "target_host": address,
        "namespace": namespace,
        "tls": use_tls,
    }
    if api_key:
        connect_kwargs["api_key"] = api_key
    
    client = await Client.connect(**connect_kwargs)
    logger.info("Connected to Temporal: %s", address)
    
    # Worker を作成して起動
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=all_workflows,
        activities=all_activities,
    )
    
    logger.info("Worker started on task_queue: %s", task_queue)
    logger.info("Waiting for workflows and activities...")
    
    # Worker を実行（常駐）
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
