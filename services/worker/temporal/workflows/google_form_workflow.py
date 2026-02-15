"""
Google フォーム自動送信ワークフロー
"""
from datetime import timedelta

from temporalio import workflow
from temporal.activities import submit_google_form
from temporal.activities.google_form_activity import GoogleFormInput


@workflow.defn
class GoogleFormWorkflow:
    """Google フォームを自動入力・送信するワークフロー"""

    @workflow.run
    async def run(self, input: GoogleFormInput) -> str:
        """
        Google フォームに自動入力して送信する。

        Args:
            input: フォーム URL と入力データ

        Returns:
            送信結果の文字列
        """
        workflow.logger.info(f"Google Form ワークフロー開始: {input.form_url}")

        result = await workflow.execute_activity(
            submit_google_form,
            input,
            start_to_close_timeout=timedelta(minutes=10),
        )

        workflow.logger.info(f"Google Form ワークフロー完了: {result}")
        return result
