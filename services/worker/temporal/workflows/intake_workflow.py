"""
削除依頼ヒアリングワークフロー

シグナルでユーザーメッセージを受け取り、
アクティビティでエージェントの1ターンを処理する。
クエリで現在のエージェント応答を取得可能。
"""

from datetime import timedelta

from temporalio import workflow

from temporal.activities import process_intake_turn
from temporal.activities.intake_activity import IntakeTurnInput


@workflow.defn
class IntakeWorkflow:
    """削除依頼の情報ヒアリングワークフロー"""

    def __init__(self):
        self._pending_messages: list[str] = []
        self._current_response: str = ""
        self._is_complete: bool = False

    @workflow.signal
    async def user_message(self, message: str) -> None:
        """ユーザーからのメッセージを受け取るシグナル"""
        self._pending_messages.append(message)

    @workflow.query
    def current_response(self) -> str:
        """エージェントの最新の応答を返すクエリ"""
        return self._current_response

    @workflow.query
    def is_complete(self) -> bool:
        """ヒアリングが完了したかどうかを返すクエリ"""
        return self._is_complete

    @workflow.run
    async def run(self, request_id: str) -> str:
        """
        ヒアリングワークフローを実行する。

        Args:
            request_id: 削除依頼の ID

        Returns:
            収集したフィールドの JSON 文字列
        """
        workflow.logger.info(f"ヒアリングワークフロー開始: {request_id}")

        conversation_json = "[]"
        collected_json = "{}"

        # 初回ターン: エージェントが最初の挨拶と質問を生成
        result = await workflow.execute_activity(
            process_intake_turn,
            IntakeTurnInput(conversation_json, None, collected_json),
            start_to_close_timeout=timedelta(minutes=2),
        )
        self._current_response = result.agent_response
        conversation_json = result.conversation_history_json
        collected_json = result.collected_fields_json

        # ユーザーメッセージを待ってターンを繰り返す
        while not result.is_complete:
            await workflow.wait_condition(
                lambda: len(self._pending_messages) > 0
            )
            msg = self._pending_messages.pop(0)

            result = await workflow.execute_activity(
                process_intake_turn,
                IntakeTurnInput(conversation_json, msg, collected_json),
                start_to_close_timeout=timedelta(minutes=2),
            )
            self._current_response = result.agent_response
            conversation_json = result.conversation_history_json
            collected_json = result.collected_fields_json

        self._is_complete = True
        workflow.logger.info(f"ヒアリング完了: {collected_json}")
        return collected_json
