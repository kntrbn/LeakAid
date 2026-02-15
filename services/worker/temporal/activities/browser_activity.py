"""
ブラウザ操作を行うアクティビティ (browser-use)
"""
from temporalio import activity
import os


@activity.defn
async def ai_browser_form_fill(instruction: str, url: str) -> str:
    """
    AIエージェントがブラウザでフォームを自動操作

    Args:
        instruction: AIへの指示（例: "フォームに名前とメールアドレスを入力して送信"）
        url: 操作対象のURL

    Returns:
        操作結果の文字列
    """
    activity.logger.info(f"Starting browser task: {instruction}")
    activity.logger.info(f"Target URL: {url}")

    try:
        # アクティビティ内でインポート（Temporalのワークフローサンドボックス制限を回避）
        from browser_use import Agent

        # OpenAI API キーを取得
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "エラー: OPENAI_API_KEY が設定されていません"

        # browser-use エージェントを作成（LLMパラメータなしで自動的にOpenAIを使用）
        # OpenAI API キーは環境変数から自動的に読み取られる
        full_task = f"{instruction}\n\n操作対象URL: {url}"

        agent = Agent(
            task=full_task,
            # llm パラメータを省略すると、自動的にOpenAI (gpt-4o) を使用
        )

        activity.logger.info("Browser agent initialized, starting execution...")

        # タスクを実行
        result = await agent.run()

        activity.logger.info(f"Browser task completed successfully")
        activity.logger.info(f"Result: {result}")

        # 結果を文字列として返す
        result_str = str(result)
        return f"ブラウザ操作完了:\n{result_str}"

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"ブラウザ操作に失敗しました: {str(e)}\n{error_details}"
        activity.logger.error(error_msg)
        return error_msg
