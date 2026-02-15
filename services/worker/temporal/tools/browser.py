"""
共用ブラウザ操作ツール (PydanticAI + Playwright)

複数のエージェントから再利用可能なツール群。
Agent(tools=[...]) で必要なツールを選んで登録する。
"""
import asyncio
import concurrent.futures
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import RunContext


# ---------------------------------------------------------------------------
# 共通 Deps
# ---------------------------------------------------------------------------


@dataclass
class BrowserDeps:
    """ブラウザ操作ツールの依存データ"""

    page: Any  # Playwright Page
    form_data: dict[str, str]
    screenshot_dir: str = "/app/logs"
    _screenshot_count: int = field(default=0, repr=False)


# ---------------------------------------------------------------------------
# ヘルパー関数（ツールから共通で使う内部ユーティリティ）
# ---------------------------------------------------------------------------


async def _find_question_block(page: Any, question_text: str):
    """質問テキストを含むフォームブロックを探す"""
    escaped = re.escape(question_text)
    for selector in [
        f'div[role="listitem"]:has(span:text-matches("{escaped}", "i"))',
        f'div[data-params]:has(span:text-matches("{escaped}", "i"))',
    ]:
        block = page.locator(selector)
        if await block.count() > 0:
            return block.first
    return None


async def _fill_text_field(page: Any, label: str, value: str) -> str:
    """テキスト入力フィールドに値を入力"""
    locator = page.locator(
        f'input[aria-label*="{label}"], textarea[aria-label*="{label}"]'
    )
    if await locator.count() > 0:
        await locator.first.click()
        await locator.first.fill(value)
        return "OK"

    label_loc = page.get_by_label(label)
    if await label_loc.count() > 0:
        await label_loc.first.click()
        await label_loc.first.fill(value)
        return "OK"

    return "not_found"


async def _select_radio_or_checkbox(page: Any, question: str, option: str) -> str:
    """質問ブロック内のラジオボタンまたはチェックボックスを選択"""
    block = await _find_question_block(page, question)
    if block:
        opt = block.get_by_text(option, exact=False)
        if await opt.count() > 0:
            await opt.first.click()
            await asyncio.sleep(0.3)
            return "OK"
        return "option_not_found"
    opt = page.get_by_text(option, exact=False)
    if await opt.count() > 0:
        await opt.first.click()
        await asyncio.sleep(0.3)
        return "OK(fallback)"
    return "not_found"


async def _fill_date_input(page: Any, date_str: str) -> str:
    """日付入力欄（input[type=date]）に値を設定"""
    parts = date_str.split("-")
    if len(parts) != 3:
        return "invalid_format"
    iso_date = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"

    date_input = page.locator('input[type="date"]')
    if await date_input.count() > 0:
        await date_input.first.evaluate(
            """(el, value) => {
                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(el, value);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            iso_date,
        )
        return "OK"
    return "not_found"


# ---------------------------------------------------------------------------
# ツール定義（Agent(tools=[...]) で登録して使う）
# ---------------------------------------------------------------------------


async def auto_fill_all_fields(ctx: RunContext[BrowserDeps]) -> str:
    """フォームデータを使って全フィールドを一括入力する。

    テキスト入力、ラジオボタン、チェックボックス、日付を自動判定して入力する。
    まずこのツールを呼び出し、結果を見て失敗したフィールドを個別に修正すること。
    """
    page = ctx.deps.page
    form_data = ctx.deps.form_data
    results = []

    questions_info = await page.evaluate("""() => {
        const questions = [];
        document.querySelectorAll('div[role="listitem"]').forEach(block => {
            const titleEl = block.querySelector('span[role="heading"], div[role="heading"]');
            const title = titleEl ? titleEl.innerText.trim() : '';

            const hasTextInput = block.querySelector('input[type="text"], textarea') !== null;
            const hasDateInput = block.querySelector('input[type="date"]') !== null;
            const hasRadio = block.querySelector('[role="radio"], input[type="radio"]') !== null;
            const hasCheckbox = block.querySelector('[role="checkbox"], input[type="checkbox"]') !== null;

            const options = [];
            block.querySelectorAll('[role="radio"] span, [role="checkbox"] span, label').forEach(el => {
                const t = el.innerText.trim();
                if (t && t.length < 200) options.push(t);
            });

            questions.push({
                title,
                hasTextInput,
                hasDateInput,
                hasRadio,
                hasCheckbox,
                options: [...new Set(options)].slice(0, 10),
            });
        });
        return questions;
    }""")

    for key, value in form_data.items():
        matched = False

        for q in questions_info:
            title = q.get("title", "")
            if not title:
                continue

            key_lower = key.lower()
            title_lower = title.lower()
            options_lower = [o.lower() for o in q.get("options", [])]
            title_match = key_lower in title_lower or title_lower in key_lower
            option_match = any(key_lower in o or o in key_lower for o in options_lower)

            if not title_match and not option_match:
                continue

            try:
                if q.get("hasDateInput"):
                    result = await _fill_date_input(page, value)
                    results.append(f"[日付] {key}: {result}")
                    matched = True
                    break
                elif q.get("hasRadio") or q.get("hasCheckbox"):
                    result = await _select_radio_or_checkbox(page, title, value)
                    results.append(f"[選択] {key} → {value}: {result}")
                    matched = True
                    break
                elif q.get("hasTextInput"):
                    result = await _fill_text_field(page, title, value)
                    if result == "not_found":
                        result = await _fill_text_field(page, key, value)
                    results.append(f"[テキスト] {key}: {result}")
                    matched = True
                    break
            except Exception as e:
                results.append(f"[エラー] {key}: {e}")
                matched = True
                break

        if not matched:
            try:
                result = await _fill_text_field(page, key, value)
                if result == "OK":
                    results.append(f"[直接入力] {key}: OK")
                else:
                    results.append(f"[未マッチ] {key}: フォーム上に対応する質問が見つかりません")
            except Exception as e:
                results.append(f"[エラー] {key}: {e}")

    return "\n".join(results)


async def get_page_text(ctx: RunContext[BrowserDeps]) -> str:
    """現在のページのテキスト内容を取得してフォームの構造を把握する"""
    page = ctx.deps.page
    text = await page.inner_text("body")
    return text[:8000]


async def get_form_data(ctx: RunContext[BrowserDeps]) -> str:
    """入力すべきフォームデータ（質問→回答のマッピング）を取得する"""
    return json.dumps(ctx.deps.form_data, ensure_ascii=False, indent=2)


async def fill_field(
    ctx: RunContext[BrowserDeps], label_text: str, value: str
) -> str:
    """テキスト入力フィールドに値を入力する。

    Args:
        label_text: 質問やラベルのテキスト（部分一致で検索）
        value: 入力する値
    """
    page = ctx.deps.page
    try:
        result = await _fill_text_field(page, label_text, value)
        if result == "OK":
            return f"入力完了: '{label_text}' に '{value}'"
        return f"フィールドが見つかりません: '{label_text}'"
    except Exception as e:
        return f"入力エラー ({label_text}): {e}"


async def click_element(ctx: RunContext[BrowserDeps], text: str) -> str:
    """指定テキストを含む要素をクリックする（ボタン等）。

    Args:
        text: クリック対象のテキスト（ボタンラベル等）
    """
    page = ctx.deps.page
    try:
        element = page.get_by_text(text, exact=False).first
        await element.click()
        await asyncio.sleep(1)
        return f"クリック完了: '{text}'"
    except Exception as e:
        return f"クリックエラー ({text}): {e}"


async def click_submit_button(ctx: RunContext[BrowserDeps]) -> str:
    """Google フォームの送信ボタンをクリックし、送信結果を確認する。

    送信ボタンをクリックした後、最大10秒待って送信完了を確認する。
    """
    page = ctx.deps.page
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

        click_info = "未クリック"

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

        try:
            btn = page.get_by_role("button", name="送信")
            count = await btn.count()
            if count > 0:
                await btn.last.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await btn.last.click()
                click_info = f"get_by_role('button', name='送信').click() ({count}個マッチ)"
            else:
                btn2 = page.get_by_role("button", name="Submit")
                count2 = await btn2.count()
                if count2 > 0:
                    await btn2.last.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await btn2.last.click()
                    click_info = "get_by_role('button', name='Submit').click()"
                else:
                    return "送信ボタンが見つかりません"
        except Exception as click_err:
            click_info = f"クリック例外: {click_err}"

        try:
            await page.wait_for_url("**/formResponse**", timeout=10000)
            text = await page.inner_text("body")
            return f"送信完了: {click_info}。URL が formResponse に遷移。ページ: {text[:500]}"
        except Exception:
            pass

        await asyncio.sleep(3)
        current_url = page.url
        text = await page.inner_text("body")
        if "回答を記録しました" in text or "Your response has been recorded" in text:
            return f"送信完了: {click_info}。完了メッセージを確認。"

        error_texts = await page.evaluate("""() => {
            const errors = [];
            document.querySelectorAll('[role="alert"]').forEach(el => {
                const t = el.innerText.trim();
                if (t) errors.push(t);
            });
            document.querySelectorAll('[class*="Error"], [class*="error"]').forEach(el => {
                const t = el.innerText.trim();
                if (t && t.length < 200) errors.push(t);
            });
            return [...new Set(errors)];
        }""")
        if error_texts:
            return f"送信失敗: {click_info}。バリデーションエラー: {'; '.join(error_texts)}"

        await page.screenshot(
            path=os.path.join(ctx.deps.screenshot_dir, "debug_after_submit.png"),
            full_page=True,
        )

        return f"{click_info}。完了メッセージ未確認。URL: {current_url}。ページ先頭: {text[:500]}"
    except Exception as e:
        return f"送信ボタンクリックエラー: {e}"


async def select_option_in_question(
    ctx: RunContext[BrowserDeps], question_text: str, option_text: str
) -> str:
    """特定の質問内にあるラジオボタンやチェックボックスの選択肢をクリックする。

    Args:
        question_text: 質問のテキスト（部分一致で検索）
        option_text: クリックする選択肢のテキスト（例: 「Yes」「No」「I agree」）
    """
    page = ctx.deps.page
    try:
        result = await _select_radio_or_checkbox(page, question_text, option_text)
        if "OK" in result:
            return f"選択完了: 質問「{question_text}」内の「{option_text}」"
        return f"選択失敗: {result}"
    except Exception as e:
        return f"選択エラー ({question_text} → {option_text}): {e}"


async def fill_date(
    ctx: RunContext[BrowserDeps], label_text: str, date_str: str
) -> str:
    """Google フォームの日付入力欄に日付を入力する。

    Args:
        label_text: 日付欄のラベルテキスト
        date_str: 日付文字列（YYYY-MM-DD 形式、例: 2026-02-14）
    """
    page = ctx.deps.page
    try:
        result = await _fill_date_input(page, date_str)
        if result == "OK":
            return f"日付入力完了: '{label_text}' に {date_str}"
        return f"日付入力失敗: {result}"
    except Exception as e:
        return f"日付入力エラー ({label_text}): {e}"


async def take_screenshot(ctx: RunContext[BrowserDeps], description: str) -> str:
    """現在のページのスクリーンショットを保存する。

    Args:
        description: スクリーンショットの説明（ファイル名に使用）
    """
    page = ctx.deps.page
    ctx.deps._screenshot_count += 1
    filename = f"step{ctx.deps._screenshot_count:02d}_{description}.png"
    filepath = os.path.join(ctx.deps.screenshot_dir, filename)
    await page.screenshot(path=filepath, full_page=True)
    return f"スクリーンショット保存: {filepath}"


async def scroll_down(ctx: RunContext[BrowserDeps]) -> str:
    """ページを下にスクロールする（隠れている要素を表示するため）"""
    page = ctx.deps.page
    await page.evaluate("window.scrollBy(0, 500)")
    await asyncio.sleep(0.5)
    return "500px 下にスクロールしました"


async def solve_recaptcha(ctx: RunContext[BrowserDeps]) -> str:
    """ページ上の reCAPTCHA を 2Captcha サービスで解決し、トークンを注入する。

    reCAPTCHA が表示されてフォーム送信がブロックされている場合に使用する。
    """
    page = ctx.deps.page
    try:
        from twocaptcha import TwoCaptcha

        api_key = os.getenv("TWO_CAPTCHA_API_KEY")
        if not api_key:
            return "エラー: TWO_CAPTCHA_API_KEY が設定されていません"

        sitekey = await page.evaluate("""() => {
            const v2 = document.querySelector('.g-recaptcha[data-sitekey]');
            if (v2) return v2.getAttribute('data-sitekey');
            const iframe = document.querySelector('iframe[src*="recaptcha"]');
            if (iframe) {
                const m = iframe.src.match(/[?&]k=([^&]+)/);
                if (m) return m[1];
            }
            return null;
        }""")

        if not sitekey:
            return "reCAPTCHA が見つかりません（sitekey を検出できませんでした）"

        page_url = page.url

        solver = TwoCaptcha(api_key)
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                lambda: solver.recaptcha(sitekey=sitekey, url=page_url),
            )

        token = result["code"]

        await page.evaluate("""(token) => {
            const textarea = document.querySelector('#g-recaptcha-response')
                || document.querySelector('[name="g-recaptcha-response"]');
            if (textarea) {
                textarea.style.display = 'block';
                textarea.value = token;
            }
            if (typeof ___grecaptcha_cfg !== 'undefined') {
                const clients = ___grecaptcha_cfg.clients;
                for (const key in clients) {
                    const client = clients[key];
                    for (const prop in client) {
                        const val = client[prop];
                        if (val && typeof val === 'object') {
                            for (const p in val) {
                                if (val[p] && typeof val[p].callback === 'function') {
                                    val[p].callback(token);
                                    return;
                                }
                            }
                        }
                    }
                }
            }
        }""", token)

        await asyncio.sleep(1)
        return f"reCAPTCHA 解決完了（sitekey: {sitekey[:16]}...）"

    except Exception as e:
        return f"reCAPTCHA 解決エラー: {e}"
