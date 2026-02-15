"use client";

import { useState } from "react";

type Props = {
  onSend: (message: string) => void;
  disabled: boolean;
};

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <div className="border-t border-gray-200 bg-white p-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder={disabled ? "回答を待っています..." : "メッセージを入力"}
          disabled={disabled}
          className="flex-1 rounded-full border border-gray-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          className="rounded-full bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
        >
          送信
        </button>
      </div>
    </div>
  );
}
