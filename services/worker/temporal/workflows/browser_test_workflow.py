"""
ブラウザテスト用ワークフロー
"""
from datetime import timedelta
from temporalio import workflow
from temporal.activities import ai_browser_form_fill


@workflow.defn
class BrowserTestWorkflow:
    """ブラウザ操作アクティビティをテストするワークフロー"""

    @workflow.run
    async def run(self, instruction: str, url: str) -> str:
        """
        ブラウザ操作を実行
        
        Args:
            instruction: AIへの指示
            url: 操作対象のURL
            
        Returns:
            ブラウザ操作の結果
        """
        workflow.logger.info(f"Starting browser test: {instruction}")
        
        # ブラウザアクティビティを実行（タイムアウト5分）
        result = await workflow.execute_activity(
            ai_browser_form_fill,
            args=(instruction, url),  # 複数の引数はタプルで渡す
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        workflow.logger.info(f"Browser test completed: {result}")
        
        return result
