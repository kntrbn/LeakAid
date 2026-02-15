# 共用ツールボックス
# 各エージェントから Agent(tools=[...]) で利用する

from temporal.tools.browser import (
    BrowserDeps,
    auto_fill_all_fields,
    click_element,
    click_submit_button,
    fill_date,
    fill_field,
    get_form_data,
    get_page_text,
    scroll_down,
    select_option_in_question,
    solve_recaptcha,
    take_screenshot,
)

# 全ツールのリスト（Agent(tools=ALL_TOOLS) で一括登録用）
ALL_TOOLS = [
    auto_fill_all_fields,
    get_page_text,
    get_form_data,
    fill_field,
    click_element,
    click_submit_button,
    select_option_in_question,
    fill_date,
    take_screenshot,
    scroll_down,
    solve_recaptcha,
]
