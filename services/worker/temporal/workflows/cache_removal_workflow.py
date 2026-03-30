"""
Google Search キャッシュ削除申請ワークフロー

削除申請フォームに自動入力し、送信手前で停止する。
"""
from datetime import timedelta

from temporalio import workflow
from temporal.activities import fill_cache_removal_form
from temporal.activities.cache_removal_activity import CacheRemovalInput


@workflow.defn
class CacheRemovalWorkflow:
    """キャッシュ削除申請フォームに自動入力するワークフロー（送信はしない）"""

    @workflow.run
    async def run(self, input: CacheRemovalInput) -> str:
        workflow.logger.info(f"キャッシュ削除ワークフロー開始: {input.form_url}")

        result = await workflow.execute_activity(
            fill_cache_removal_form,
            input,
            start_to_close_timeout=timedelta(minutes=10),
        )

        workflow.logger.info(f"キャッシュ削除ワークフロー完了: {result}")
        return result
