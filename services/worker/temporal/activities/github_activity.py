"""
GitHub リポジトリ情報を取得するアクティビティ
"""
from temporalio import activity
import urllib.request
import json


@activity.defn
async def get_github_repo_info(repo: str) -> str:
    """
    指定されたGitHubリポジトリの情報を取得
    
    Args:
        repo: リポジトリ名（例: "temporalio/temporal"）
        
    Returns:
        リポジトリ情報の文字列
    """
    activity.logger.info(f"Fetching GitHub repo info for: {repo}")
    
    try:
        # GitHub API を使用（認証不要、レート制限あり）
        url = f"https://api.github.com/repos/{repo}"
        
        # GitHub API requires User-Agent header
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'LeakAid-Temporal-Demo')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            # リポジトリ情報を抽出
            name = data["full_name"]
            description = data["description"] or "説明なし"
            stars = data["stargazers_count"]
            forks = data["forks_count"]
            language = data["language"] or "不明"
            
            result = (
                f"📦 {name}\n"
                f"📝 {description}\n"
                f"⭐ Stars: {stars:,} | 🔱 Forks: {forks:,} | 💻 Language: {language}"
            )
            
            activity.logger.info(f"GitHub repo data fetched: {name}")
            return result
            
    except Exception as e:
        activity.logger.error(f"Failed to fetch GitHub repo info: {e}")
        return f"GitHubリポジトリ情報の取得に失敗しました: {str(e)}"
