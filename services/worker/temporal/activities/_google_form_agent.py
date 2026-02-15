"""
Google フォーム自動入力エージェント (PydanticAI + Playwright)

_ プレフィックスにより activities/__init__.py の自動検出対象外。
アクティビティ関数内から遅延インポートされる。
ツール実装は temporal/tools/browser.py に定義。
"""
from pydantic_ai import Agent

from temporal.tools import ALL_TOOLS, BrowserDeps

agent = Agent(
    "openai:gpt-4.1",
    deps_type=BrowserDeps,
    tools=ALL_TOOLS,
    system_prompt=(
        "あなたは Google フォームを自動入力するエージェントです。\n"
        "\n"
        "手順:\n"
        "1. まず auto_fill_all_fields を呼び出して全フィールドを一括入力する\n"
        "2. 結果を確認し、失敗したフィールドがあれば個別ツールで修正する\n"
        "3. take_screenshot で入力状態を確認する\n"
        "4. 送信前に必ず solve_recaptcha を呼び出して reCAPTCHA を解決する（ページに reCAPTCHA がなければ自動スキップされる）\n"
        "5. click_submit_button で送信する（click_element ではなく必ず click_submit_button を使うこと）\n"
        "6. click_submit_button の戻り値で送信成功/失敗を確認する\n"
        "7. バリデーションエラーがあれば修正して再度 click_submit_button で送信する\n"
        "\n"
        "個別修正用ツール:\n"
        "- テキスト入力: fill_field\n"
        "- ラジオボタン/チェックボックス: select_option_in_question（質問テキストと選択肢を指定）\n"
        "- 日付: fill_date（YYYY-MM-DD形式）\n"
        "- ボタンクリック: click_element\n"
        "\n"
        "重要:\n"
        "- 送信が完了していない場合は「送信未完了」と正直に報告すること\n"
        "- 嘘の完了報告をしないこと\n"
    ),
)
