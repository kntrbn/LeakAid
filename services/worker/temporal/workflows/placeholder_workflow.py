"""
シンプルなワークフロー（GitHub API呼び出しアクティビティを含む4つのタスクをシーケンシャルに実行）
"""
from datetime import timedelta
from temporalio import workflow
from temporal.activities import get_github_repo_info


@workflow.defn
class PlaceholderWorkflow:
    """4つのタスクを順番に実行するワークフロー（GitHub API呼び出しを含む）"""

    @workflow.run
    async def run(self, name: str) -> str:
        """
        4つのタスクをシーケンシャルに実行
        
        Args:
            name: 名前
            
        Returns:
            最終結果（名前とGitHubリポジトリ情報を含む）
        """
        # タスク1: 挨拶メッセージを作成
        task1_result = f"Hello, {name}!"
        workflow.logger.info(f"Task 1 completed: {task1_result}")
        await workflow.sleep(60)  # 1分待機
        
        # タスク2: メッセージを大文字に変換
        task2_result = task1_result.upper()
        workflow.logger.info(f"Task 2 completed: {task2_result}")
        await workflow.sleep(60)  # 1分待機
        
        # タスク3: GitHubリポジトリ情報を取得（アクティビティ呼び出し）
        github_result = await workflow.execute_activity(
            get_github_repo_info,
            "temporalio/temporal",
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Task 3 completed: {github_result}")
        await workflow.sleep(60)  # 1分待機
        
        # タスク4: 最終メッセージを作成（名前とGitHub情報を含む）
        task4_result = f"Final: {task2_result}\n\nGitHub Info:\n{github_result}"
        workflow.logger.info(f"Task 4 completed: {task4_result}")
        
        return task4_result
