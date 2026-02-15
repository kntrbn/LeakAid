"""
削除依頼ヒアリングアクティビティ (PydanticAI)

PydanticAI エージェントがユーザーとの対話1ターンを処理する。
Temporal ワークフローから繰り返し呼び出される。
"""

import json
from dataclasses import dataclass

from temporalio import activity


@dataclass
class IntakeTurnInput:
    """ヒアリング1ターンの入力"""

    conversation_history_json: str  # JSON 文字列: [{"role": "user"|"assistant", "content": "..."}]
    user_message: str | None  # None = 初回ターン
    collected_fields_json: str  # JSON 文字列: {field_name: value}


@dataclass
class IntakeTurnResult:
    """ヒアリング1ターンの出力"""

    agent_response: str
    conversation_history_json: str
    collected_fields_json: str
    is_complete: bool


@activity.defn
async def process_intake_turn(input: IntakeTurnInput) -> IntakeTurnResult:
    """
    ヒアリングエージェントの1ターンを処理する。

    会話履歴と収集済みフィールドを受け取り、
    エージェントの応答・更新された状態を返す。
    """
    from temporal.activities._intake_agent import IntakeDeps, agent

    collected = (
        json.loads(input.collected_fields_json)
        if input.collected_fields_json
        else {}
    )
    conversation = (
        json.loads(input.conversation_history_json)
        if input.conversation_history_json
        else []
    )

    deps = IntakeDeps(collected=collected)

    if input.user_message is None:
        # 初回ターン
        prompt = "ヒアリングを開始してください。"
    else:
        # 会話コンテキストを構築
        parts = []
        if conversation:
            parts.append("【これまでの会話】")
            for msg in conversation:
                role = "ユーザー" if msg["role"] == "user" else "あなた"
                parts.append(f"{role}: {msg['content']}")

        if collected:
            parts.append(
                f"\n【収集済み情報】: {json.dumps(collected, ensure_ascii=False)}"
            )

        parts.append(f"\n【ユーザーの最新の発言】: {input.user_message}")
        parts.append(
            "\n上記の文脈を踏まえて適切に対応してください。"
        )
        prompt = "\n".join(parts)

    activity.logger.info(f"ヒアリングターン開始: user_message={input.user_message}")

    result = await agent.run(prompt, deps=deps)

    # 会話履歴を更新
    if input.user_message is not None:
        conversation.append({"role": "user", "content": input.user_message})
    conversation.append({"role": "assistant", "content": result.output})

    activity.logger.info(
        f"ヒアリングターン完了: collected={deps.collected}, is_complete={deps.is_complete}"
    )

    return IntakeTurnResult(
        agent_response=result.output,
        conversation_history_json=json.dumps(conversation, ensure_ascii=False),
        collected_fields_json=json.dumps(deps.collected, ensure_ascii=False),
        is_complete=deps.is_complete,
    )
