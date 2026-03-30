"""
削除依頼ヒアリングワークフロー

シグナルでユーザーメッセージを受け取り、
アクティビティでエージェントの1ターンを処理する。
クエリで現在のエージェント応答を取得可能。
画像アップロード時は Cloud Vision で類似画像を検索する。
"""

from datetime import timedelta

from temporalio import workflow

from temporal.activities import (
    process_intake_turn,
    save_intake_result,
    search_similar_images,
)
from temporal.activities.image_search_activity import ImageSearchInput
from temporal.activities.intake_activity import IntakeTurnInput, SaveIntakeInput


@workflow.defn
class IntakeWorkflow:
    """削除依頼の情報ヒアリングワークフロー"""

    def __init__(self):
        self._pending_messages: list[str] = []
        self._pending_image: str | None = None
        self._current_response: str = ""
        self._is_complete: bool = False

    @workflow.signal
    async def user_message(self, message: str) -> None:
        """ユーザーからのメッセージを受け取るシグナル"""
        self._pending_messages.append(message)

    @workflow.signal
    async def image_uploaded(self, gcs_uri: str) -> None:
        """画像アップロード通知を受け取るシグナル"""
        self._pending_image = gcs_uri

    @workflow.query
    def current_response(self) -> str:
        """エージェントの最新の応答を返すクエリ"""
        return self._current_response

    @workflow.query
    def is_complete(self) -> bool:
        """ヒアリングが完了したかどうかを返すクエリ"""
        return self._is_complete

    @workflow.run
    async def run(self, request_id: str, user_id: str = "", user_name: str = "") -> str:
        """
        ヒアリングワークフローを実行する。

        Args:
            request_id: 削除依頼の ID
            user_id: ユーザー ID (Supabase auth UUID)
            user_name: ユーザー表示名

        Returns:
            収集したフィールドの JSON 文字列
        """
        workflow.logger.info(f"ヒアリングワークフロー開始: {request_id} (user={user_id})")

        conversation_json = "[]"
        collected_json = "{}"

        # 初回ターン: エージェントが最初の挨拶と質問を生成
        result = await workflow.execute_activity(
            process_intake_turn,
            IntakeTurnInput(conversation_json, None, collected_json, user_name),
            start_to_close_timeout=timedelta(minutes=2),
        )
        self._current_response = result.agent_response
        conversation_json = result.conversation_history_json
        collected_json = result.collected_fields_json

        # ユーザーメッセージまたは画像アップロードを待ってターンを繰り返す
        while not result.is_complete:
            await workflow.wait_condition(
                lambda: len(self._pending_messages) > 0 or self._pending_image is not None
            )

            image_search_json = ""

            # 画像アップロードがあれば Cloud Vision で検索
            if self._pending_image is not None:
                gcs_uri = self._pending_image
                self._pending_image = None
                workflow.logger.info(f"画像検索開始: {gcs_uri}")

                search_result = await workflow.execute_activity(
                    search_similar_images,
                    ImageSearchInput(gcs_uri=gcs_uri),
                    start_to_close_timeout=timedelta(minutes=5),
                )
                image_search_json = search_result.results_json

                # 画像検索結果をエージェントに渡す
                result = await workflow.execute_activity(
                    process_intake_turn,
                    IntakeTurnInput(
                        conversation_json, None, collected_json,
                        image_search_results_json=image_search_json,
                    ),
                    start_to_close_timeout=timedelta(minutes=2),
                )
            else:
                # 通常のテキストメッセージ
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

        # 収集データを Supabase に保存
        if user_id:
            await workflow.execute_activity(
                save_intake_result,
                SaveIntakeInput(user_id=user_id, collected_fields_json=collected_json),
                start_to_close_timeout=timedelta(seconds=30),
            )

        return collected_json
