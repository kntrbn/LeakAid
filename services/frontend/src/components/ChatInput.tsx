"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  onSend: (message: string) => void;
  onImageUpload?: (file: File) => void;
  disabled: boolean;
};

export function ChatInput({ onSend, onImageUpload, disabled }: Props) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onImageUpload) {
      onImageUpload(file);
    }
    // リセットして同じファイルを再選択可能にする
    e.target.value = "";
  };

  return (
    <div className="border-t border-gray-200 bg-white p-3">
      <div className="flex gap-2">
        {/* 画像アップロードボタン */}
        {onImageUpload && (
          <>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={disabled}
              title="画像をアップロード"
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-gray-300 text-gray-500 transition-colors hover:bg-gray-100 disabled:bg-gray-100 disabled:text-gray-300"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                <path fillRule="evenodd" d="M15.621 4.379a3 3 0 0 0-4.242 0l-7 7a3 3 0 0 0 4.241 4.243h.001l.497-.5a.75.75 0 0 1 1.064 1.057l-.498.501a4.5 4.5 0 0 1-6.364-6.364l7-7a4.5 4.5 0 0 1 6.368 6.36l-3.455 3.553A2.625 2.625 0 1 1 9.52 9.52l3.45-3.451a.75.75 0 1 1 1.061 1.06l-3.45 3.451a1.125 1.125 0 0 0 1.587 1.595l3.454-3.553a3 3 0 0 0 0-4.242Z" clipRule="evenodd" />
              </svg>
            </button>
          </>
        )}
        <input
          ref={inputRef}
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
