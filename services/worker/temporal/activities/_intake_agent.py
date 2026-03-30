"""
削除依頼ヒアリングエージェント (PydanticAI)

_ プレフィックスにより activities/__init__.py の自動検出対象外。
アクティビティ関数内から遅延インポートされる。
"""

from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext

REQUIRED_FIELDS = [
    "removal_reason",
    "content_detail",
    "is_self",
    "country",
    "email",
    "content_urls",
    "search_result_urls",
    "search_keywords",
    "future_detection",
    "future_similar_removal",
]

FIELD_DESCRIPTIONS = {
    "removal_reason": "削除理由カテゴリ",
    "content_detail": "コンテンツの詳細",
    "is_self": "本人 or 代理人",
    "country": "居住国",
    "email": "連絡先メールアドレス",
    "content_urls": "コンテンツの URL（複数可）",
    "search_result_urls": "Google 検索結果ページの URL（複数可）",
    "search_keywords": "検索キーワード（複数可）",
    "future_detection": "今後も同じ画像の検出・削除を希望するか",
    "future_similar_removal": "類似検索でも削除を希望するか",
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
        "あなたは Google 検索結果からの個人コンテンツ削除申請に必要な情報をヒアリングする AI アシスタントです。\n"
        "被害に遭われた方に寄り添い、優しく丁寧なトーンで対応してください。\n"
        "\n"
        "## 収集するフィールド（この順番で1つずつ聞いてください）\n"
        "\n"
        "1. removal_reason - Google 検索から個人的なコンテンツを削除したい理由:\n"
        "   - ヌードや性的な内容が含まれている\n"
        "   - 自分の個人情報が含まれている\n"
        "   - 不当な削除方針を掲げているサイトに掲載されている\n"
        "   - 18歳未満の人物が写っている\n"
        "\n"
        "2. content_detail - コンテンツの詳細（removal_reason が性的内容の場合）:\n"
        "   - ヌードや性的行為、または親密な状態の自分が含まれている（リベンジポルノ含む）\n"
        "   - 性的行為や親密な状態にある自分の描写が偽造されている（ディープフェイク）\n"
        "   - 自分と性的なコンテンツが誤って結び付けられている\n"
        "   - 18歳未満の人物を扱ったヌードや性的に露骨な表現が含まれている\n"
        "   ※ removal_reason が性的内容以外の場合はスキップ可\n"
        "\n"
        "3. is_self - コンテンツに写っている人物は本人ですか？:\n"
        "   - 「私です」\n"
        "   - 「他の人です」（代理人の場合、本人からの許可が必要）\n"
        "\n"
        "4. country - 居住国\n"
        "\n"
        "5. email - 連絡先メールアドレス（リクエストに関するメール送信先）\n"
        "\n"
        "6. content_urls - コンテンツの URL（複数ある場合は全て）\n"
        "\n"
        "7. search_result_urls - Google 検索の検索結果ページの URL（複数可）\n"
        "\n"
        "8. search_keywords - 報告対象コンテンツを見つけた際の検索キーワード（複数可）\n"
        "\n"
        "9. future_detection - 今回報告された画像と同じ画像を、今後も検出して削除する対応を希望しますか？\n"
        "   （はい/いいえ）\n"
        "\n"
        "10. future_similar_removal - 今後、類似する検索が行われた場合も、露骨な表現を含む検索結果を削除する対応を希望しますか？\n"
        "    （はい/いいえ）\n"
        "\n"
        "## 手順\n"
        "1. 最初に挨拶し、最初の質問をする\n"
        "2. ユーザーの回答を save_field で保存し、次の質問へ\n"
        "3. 全フィールド収集後、内容を箇条書きで要約し確認する\n"
        "4. 確認 OK なら complete_intake を呼ぶ\n"
        "5. 修正依頼があれば save_field で上書きする\n"
        "\n"
        "## 画像検索結果について\n"
        "- 画像検索結果が提供された場合、見つかったページ URL を番号付きリストで提示する\n"
        "- ユーザーに該当する URL を番号で選んでもらう\n"
        "- 選択された URL を content_urls として save_field で保存する\n"
        "- 該当なしの場合は手動で URL を入力してもらう\n"
        "\n"
        "## 重要\n"
        "- 一度に1つの質問だけをすること\n"
        "- 選択肢がある質問は選択肢を提示すること\n"
        "- 「わからない」は「不明」として保存\n"
        "- URL は複数入力可能であることを伝えること\n"
    ),
)


@agent.tool
async def save_field(
    ctx: RunContext[IntakeDeps], field_name: str, value: str
) -> str:
    """収集したフィールドの値を保存する。

    Args:
        field_name: フィールド名（REQUIRED_FIELDS のいずれか）
        value: 保存する値
    """
    if field_name not in REQUIRED_FIELDS:
        return (
            f"エラー: 不明なフィールド名 '{field_name}'。"
            f"有効なフィールド: {', '.join(REQUIRED_FIELDS)}"
        )

    if field_name in ("future_detection", "future_similar_removal"):
        ctx.deps.collected[field_name] = value.lower() in (
            "true", "はい", "yes", "1",
        )
    else:
        ctx.deps.collected[field_name] = value

    remaining = [f for f in REQUIRED_FIELDS if f not in ctx.deps.collected]
    # content_detail は removal_reason が性的内容以外ならスキップ可
    reason = ctx.deps.collected.get("removal_reason", "")
    if "content_detail" in remaining and "ヌード" not in reason and "性的" not in reason:
        remaining.remove("content_detail")

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
    required = list(REQUIRED_FIELDS)
    # content_detail は条件付き
    reason = ctx.deps.collected.get("removal_reason", "")
    if "ヌード" not in reason and "性的" not in reason:
        required = [f for f in required if f != "content_detail"]

    missing = [f for f in required if f not in ctx.deps.collected]
    if missing:
        return f"エラー: まだ未収集のフィールドがあります: {', '.join(missing)}"

    ctx.deps.is_complete = True
    return "ヒアリング完了。"
