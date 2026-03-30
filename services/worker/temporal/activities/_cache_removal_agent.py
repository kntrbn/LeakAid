"""
Google Search キャッシュ削除申請エージェント (PydanticAI + Playwright)

_ プレフィックスにより activities/__init__.py の自動検出対象外。
アクティビティ関数内から遅延インポートされる。
ツール実装は temporal/tools/browser.py に定義。
"""
import os

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from temporal.tools import (
    BrowserDeps,
    auto_fill_all_fields,
    click_element,
    fill_date,
    fill_field,
    get_form_data,
    get_page_elements,
    get_page_text,
    scroll_down,
    select_dropdown_option,
    select_option_in_question,
    solve_recaptcha,
    take_screenshot,
)

# レート制限対策: リトライ付きクライアント
_openai_client = AsyncOpenAI(max_retries=5)
_model_name = os.getenv("CACHE_REMOVAL_MODEL", "gpt-4.1")
_provider = OpenAIProvider(openai_client=_openai_client)
_model = OpenAIModel(_model_name, provider=_provider)

# click_submit_button は意図的に除外 — 送信手前で停止するため
agent = Agent(
    _model,
    deps_type=BrowserDeps,
    tools=[
        get_page_elements,
        get_page_text,
        get_form_data,
        auto_fill_all_fields,
        fill_field,
        click_element,
        select_option_in_question,
        select_dropdown_option,
        fill_date,
        take_screenshot,
        scroll_down,
        solve_recaptcha,
    ],
    system_prompt=(
        "あなたは Google の検索結果からコンテンツ削除を申請するエージェントです。\n"
        "\n"
        "目標：提供されたフォームデータ（get_form_data で確認可能）を基に、\n"
        "フォームの全ステップを入力し、最終送信の直前まで進めてください。\n"
        "\n"
        "ルール：\n"
        "- 「次へ」等の中間ボタンは押してOK\n"
        "- 「送信」「Submit」等の最終送信ボタンは絶対に押さない\n"
        "- 入力完了後「入力完了。送信待ち状態です。」と報告する\n"
    ),
)
