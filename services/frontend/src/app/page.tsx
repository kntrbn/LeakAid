"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { useAuth } from "@/components/AuthProvider";
import { getResponse, getStatus, sendMessage, startIntake, uploadImage } from "@/lib/api";

type Message = { role: "agent" | "user"; content: string };

export default function ChatPage() {
  const { token, user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [waiting, setWaiting] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastResponseRef = useRef("");

  // 自動スクロール
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ワークフロー開始 + 初回応答ポーリング
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    (async () => {
      try {
        const fullName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "";
        const userName = fullName.split(" ")[0];
        const { workflow_id } = await startIntake(token, userName);
        if (cancelled) return;
        setWorkflowId(workflow_id);

        // 初回応答を待つ
        setWaiting(true);
        const response = await pollForNewResponse(workflow_id, "", token);
        if (cancelled) return;
        lastResponseRef.current = response;
        setMessages([{ role: "agent", content: response }]);
        setWaiting(false);
      } catch {
        if (!cancelled) setError("接続に失敗しました。再読み込みしてください。");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token]);

  // メッセージ送信
  const handleSend = useCallback(
    async (text: string) => {
      if (!workflowId || !token || waiting) return;

      setMessages((prev) => [...prev, { role: "user", content: text }]);
      setWaiting(true);

      try {
        await sendMessage(workflowId, text, token);

        // エージェントの応答を待つ
        const response = await pollForNewResponse(
          workflowId,
          lastResponseRef.current,
          token
        );
        lastResponseRef.current = response;
        setMessages((prev) => [...prev, { role: "agent", content: response }]);

        // 完了チェック
        const { is_complete } = await getStatus(workflowId, token);
        if (is_complete) setComplete(true);
      } catch {
        setError("エラーが発生しました。再読み込みしてください。");
      } finally {
        setWaiting(false);
      }
    },
    [workflowId, token, waiting]
  );

  // 画像アップロード
  const handleImageUpload = useCallback(
    async (file: File) => {
      if (!workflowId || !token || waiting) return;

      setMessages((prev) => [...prev, { role: "user", content: `[画像: ${file.name}]` }]);
      setWaiting(true);

      try {
        await uploadImage(workflowId, token, file);

        // Cloud Vision の検索結果を含むエージェント応答を待つ
        const response = await pollForNewResponse(
          workflowId,
          lastResponseRef.current,
          token
        );
        lastResponseRef.current = response;
        setMessages((prev) => [...prev, { role: "agent", content: response }]);

        const { is_complete } = await getStatus(workflowId, token);
        if (is_complete) setComplete(true);
      } catch {
        setError("画像のアップロードに失敗しました。再読み込みしてください。");
      } finally {
        setWaiting(false);
      }
    },
    [workflowId, token, waiting]
  );

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* メッセージ一覧 */}
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}

        {waiting && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md bg-gray-200 px-4 py-2.5 text-sm text-gray-500">
              ...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* 入力欄 or 完了メッセージ */}
      {complete ? (
        <div className="border-t border-gray-200 bg-green-50 p-4 text-center text-sm text-green-700">
          ヒアリングが完了しました。ありがとうございました。
        </div>
      ) : (
        <ChatInput onSend={handleSend} onImageUpload={handleImageUpload} disabled={waiting || !workflowId} />
      )}
    </div>
  );
}

/** 応答が更新されるまでポーリングする（最大60秒） */
async function pollForNewResponse(
  workflowId: string,
  previousResponse: string,
  token: string
): Promise<string> {
  for (let i = 0; i < 120; i++) {
    await sleep(500);
    const { response } = await getResponse(workflowId, token);
    if (response && response !== previousResponse) return response;
  }
  throw new Error("Response timeout");
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
