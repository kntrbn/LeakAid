"""
Temporal クライアント
コマンドライン引数でワークフローを実行
使い方: python client.py <ワークフロー名> <JSON引数>
例: python client.py PlaceholderWorkflow '"World"'
例: python client.py GoogleFormWorkflow '{"form_url": "https://...", "form_data": {"質問": "回答"}}'
"""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# backend の workflow を import できるようにする
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root / "backend"))

from temporalio.client import Client


async def run_workflow(workflow_name: str, arg) -> str:
    """
    指定されたワークフローを実行（Fire-and-forget）

    Args:
        workflow_name: ワークフロー名（例: PlaceholderWorkflow）
        arg: ワークフローに渡す引数（単一）

    Returns:
        ワークフロー ID
    """
    # 環境変数から Temporal 設定を取得
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = os.getenv("TEMPORAL_PORT", "7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "default")
    use_tls = os.getenv("TEMPORAL_USE_TLS", "false").lower() == "true"
    api_key = os.getenv("TEMPORAL_API_KEY")

    address = f"{host}:{port}"

    # Temporal に接続
    connect_kwargs = {
        "target_host": address,
        "namespace": namespace,
        "tls": use_tls,
    }
    if api_key:
        connect_kwargs["api_key"] = api_key

    client = await Client.connect(**connect_kwargs)
    print(f"Connected to Temporal: {address}")

    # ワークフローを動的に import
    import importlib
    workflows_module = importlib.import_module("temporal.workflows")
    workflow_class = getattr(workflows_module, workflow_name)

    print(f"Starting workflow: {workflow_name}")
    print(f"Argument: {arg}")

    workflow_id = f"{workflow_name.lower()}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        workflow_class.run,
        arg,
        id=workflow_id,
        task_queue=task_queue,
    )

    print(f"Workflow started successfully!")
    print(f"Workflow ID: {handle.id}")
    print(f"You can check the status in Temporal UI or get the result later using this ID.")

    return handle.id


async def main():
    """メイン関数"""
    # コマンドライン引数をチェック
    if len(sys.argv) < 3:
        print("Usage: python client.py <WorkflowName> <JSON引数>")
        print('Example: python client.py PlaceholderWorkflow \'"World"\'')
        print('Example: python client.py GoogleFormWorkflow \'{"form_url": "https://...", "form_data": {"質問": "回答"}}\'')
        sys.exit(1)

    # .env ファイルを読み込む
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    # コマンドライン引数を解析
    workflow_name = sys.argv[1]
    arg = json.loads(sys.argv[2])

    # ワークフローを実行（Fire-and-forget）
    workflow_id = await run_workflow(workflow_name, arg)
    print(f"\n✅ Workflow queued: {workflow_id}")
    print(f"The workflow will be processed by a Worker when available.")


if __name__ == "__main__":
    asyncio.run(main())
