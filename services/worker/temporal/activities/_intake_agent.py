"""
削除依頼ヒアリングエージェント (PydanticAI)

_ プレフィックスにより activities/__init__.py の自動検出対象外。
アクティビティ関数内から遅延インポートされる。
"""

from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext

REQUIRED_FIELDS = [
    "is_self_shot",
    "filming_consent",
    "publishing_consent",
    "age_at_filming",
    "uploader_relationship",
    "uploader_account_url",
    "incident_context",
]

FIELD_DESCRIPTIONS = {
    "is_self_shot": "自撮りかどうか（true/false）",
    "filming_consent": "撮影への同意があったか（true/false）",
    "publishing_consent": "公開への同意があったか（true/false）",
    "age_at_filming": "撮影時の年齢（整数）",
    "uploader_relationship": "アップロード者との関係性（テキスト）",
    "uploader_account_url": "アップロード者のアカウントURL（URLまたは「不明」）",
    "incident_context": "被害の経緯詳細（テキスト）",
}


@dataclass
class IntakeDeps:
    """ヒアリングエージェントの依存関係"""

    collected: dict = field(default_factory=dict)
    is_complete: bool = False


agent = Agent(
    "openai:gpt-4.1",
    deps_type=IntakeDeps,
    system_prompt=(
        "あなたは画像・動画の削除依頼（リベンジポルノ等）に必要な情報をヒアリングするAIアシスタントです。\n"
        "被害に遭われた方に寄り添い、優しく丁寧なトーンで対応してください。\n"
        "\n"
        "## 収集するフィールド（この順番で1つずつ聞いてください）\n"
        "\n"
        "1. is_self_shot - その画像/動画は自撮りですか？（はい/いいえ）\n"
        "2. filming_consent - 撮影することに同意していましたか？（はい/いいえ）\n"
        "3. publishing_consent - インターネットへの公開に同意していましたか？（はい/いいえ）\n"
        "4. age_at_filming - 撮影された時の年齢は何歳でしたか？（数字）\n"
        "5. uploader_relationship - アップロードした人とあなたの関係を教えてください"
        "（例: 元交際相手、知人、不明など）\n"
        "6. uploader_account_url - アップロードした人のSNSアカウントや"
        "プロフィールのURLがわかれば教えてください（わからなければ「不明」で結構です）\n"
        "7. incident_context - 被害の経緯を詳しく教えてください（自由記述）\n"
        "\n"
        "## 手順\n"
        "1. 最初に「これから申請に必要な情報を教えてください。」と伝え、最初の質問をする\n"
        "2. ユーザーの回答を受け取ったら save_field ツールで値を保存する\n"
        "3. 次の未収集フィールドについて質問する\n"
        "4. 全フィールド収集後、内容を箇条書きで要約し「以上の内容でよろしいですか？」と確認する\n"
        "5. ユーザーが確認OKと言ったら complete_intake ツールを呼び出す\n"
        "6. 修正依頼があれば該当フィールドを save_field で上書きする\n"
        "\n"
        "## 質問への対応\n"
        "- ユーザーが質問の意味を聞いてきた場合: わかりやすく説明し、再度同じ質問をする\n"
        "- 申請に関係のない質問・雑談: "
        "「申請に必要な情報に関するご質問のみお答えできます。」と伝える\n"
        "- ユーザーが「わからない」と言った場合: 「不明」として保存する\n"
        "\n"
        "## 重要\n"
        "- 一度に1つの質問だけをすること\n"
        "- schema_version については聞かないこと\n"
    ),
)


@agent.tool
async def save_field(
    ctx: RunContext[IntakeDeps], field_name: str, value: str
) -> str:
    """収集したフィールドの値を保存する。

    Args:
        field_name: フィールド名（is_self_shot, filming_consent, publishing_consent,
                    age_at_filming, uploader_relationship, uploader_account_url,
                    incident_context のいずれか）
        value: 保存する値（ブール値は "true"/"false"、年齢は数字の文字列）
    """
    if field_name not in REQUIRED_FIELDS:
        return (
            f"エラー: 不明なフィールド名 '{field_name}'。"
            f"有効なフィールド: {', '.join(REQUIRED_FIELDS)}"
        )

    # 型変換
    if field_name in ("is_self_shot", "filming_consent", "publishing_consent"):
        ctx.deps.collected[field_name] = value.lower() in (
            "true",
            "はい",
            "yes",
            "1",
        )
    elif field_name == "age_at_filming":
        try:
            ctx.deps.collected[field_name] = int(value)
        except ValueError:
            return f"エラー: 年齢は数字で入力してください。受け取った値: {value}"
    else:
        ctx.deps.collected[field_name] = value

    remaining = [f for f in REQUIRED_FIELDS if f not in ctx.deps.collected]
    if remaining:
        desc = ", ".join(FIELD_DESCRIPTIONS[f] for f in remaining)
        return f"'{field_name}' を保存しました。残り: {desc}"
    return "全てのフィールドが収集されました。内容を要約してユーザーに確認してください。"


@agent.tool
async def get_progress(ctx: RunContext[IntakeDeps]) -> str:
    """現在の収集状況を確認する。"""
    collected_info = dict(ctx.deps.collected)
    remaining = [f for f in REQUIRED_FIELDS if f not in ctx.deps.collected]
    return (
        f"収集済み: {collected_info}\n"
        f"未収集: {[FIELD_DESCRIPTIONS[f] for f in remaining]}"
    )


@agent.tool
async def complete_intake(ctx: RunContext[IntakeDeps]) -> str:
    """全フィールド収集完了後、ユーザー確認を得てからヒアリングを完了させる。"""
    missing = [f for f in REQUIRED_FIELDS if f not in ctx.deps.collected]
    if missing:
        return f"エラー: まだ未収集のフィールドがあります: {', '.join(missing)}"

    ctx.deps.is_complete = True
    return "ヒアリング完了。"
