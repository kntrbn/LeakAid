"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import {
  getStatusSummary,
  getStatusUrls,
  type StatusSummary,
  type TargetUrlWithLogs,
} from "@/lib/api";
import { StatusSummaryCards } from "@/components/status/StatusSummaryCards";
import { UrlCard } from "@/components/status/UrlCard";

export default function StatusPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<StatusSummary | null>(null);
  const [urls, setUrls] = useState<TargetUrlWithLogs[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    (async () => {
      try {
        const [s, u] = await Promise.all([
          getStatusSummary(token),
          getStatusUrls(token),
        ]);
        if (cancelled) return;
        setSummary(s);
        setUrls(u);
      } catch {
        if (!cancelled) setError("データの取得に失敗しました。再読み込みしてください。");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-gray-500">
        読み込み中...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-red-600">
        {error}
      </div>
    );
  }

  // 空の状態
  if (!summary || summary.detected_url_count === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="text-sm text-gray-500">
          まだ削除依頼がありません
        </p>
        <Link
          href="/"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          チャットから依頼を開始
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {/* サマリーカード */}
        <StatusSummaryCards summary={summary} />

        {/* URL リスト */}
        <div className="space-y-3">
          {urls.map((url) => (
            <UrlCard key={url.id} data={url} />
          ))}
        </div>
      </div>
    </div>
  );
}
