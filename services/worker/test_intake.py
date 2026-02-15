"""
ヒアリングエージェント対話テスト

Temporal を介さず、エージェントと直接 stdin/stdout で対話するテストスクリプト。
Docker コンテナ内で実行:
  docker compose run -it worker-dev python test_intake.py
"""

import asyncio
import sys
from pathlib import Path

# .env から環境変数を読み込む（Docker 内では env_file で設定済み）
try:
    from dotenv import load_dotenv

    for parent in Path(__file__).resolve().parents:
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

# temporal パッケージを import できるように PYTHONPATH を設定
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))


async def main():
    from temporal.activities._intake_agent import IntakeDeps, agent

    deps = IntakeDeps()

    # 初回ターン: エージェントが挨拶と最初の質問を生成
    result = await agent.run("ヒアリングを開始してください。", deps=deps)
    print(f"\nエージェント: {result.output}\n")
    history = result.all_messages()

    while not deps.is_complete:
        try:
            user_input = input("あなた: ")
        except (EOFError, KeyboardInterrupt):
            print("\n中断しました。")
            break

        if not user_input.strip():
            continue

        result = await agent.run(user_input, deps=deps, message_history=history)
        print(f"\nエージェント: {result.output}\n")
        history = result.all_messages()

    if deps.is_complete:
        print("=== 収集完了 ===")
        for k, v in deps.collected.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
