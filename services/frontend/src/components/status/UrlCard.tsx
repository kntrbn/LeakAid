"use client";

import { useState } from "react";
import type { TargetUrlWithLogs } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";
import { UrlTimeline } from "./UrlTimeline";

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

function getSourceBadge(status: string): {
  variant: "success" | "waiting" | "error";
  label: string;
} {
  switch (status) {
    case "removed_404":
      return { variant: "success", label: "削除確認済" };
    case "failed":
      return { variant: "error", label: "対応不可" };
    default:
      return { variant: "waiting", label: "掲載中" };
  }
}

function getSearchBadge(status: string): {
  variant: "success" | "waiting" | "error";
  label: string;
} {
  switch (status) {
    case "deindexed":
      return { variant: "success", label: "検索ブロック済" };
    case "not_applicable":
      return { variant: "waiting", label: "対象外" };
    default:
      return { variant: "waiting", label: "検索表示中" };
  }
}

export function UrlCard({ data }: { data: TargetUrlWithLogs }) {
  const [open, setOpen] = useState(false);
  const sourceBadge = getSourceBadge(data.source_status);
  const searchBadge = getSearchBadge(data.search_status);

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-start gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900">
            {data.website_name || extractDomain(data.url)}
          </p>
          <p className="mt-0.5 truncate text-xs text-gray-400">{data.url}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <StatusBadge variant={searchBadge.variant} label={searchBadge.label} />
            <StatusBadge variant={sourceBadge.variant} label={sourceBadge.label} />
          </div>
        </div>

        {/* Chevron */}
        <svg
          className={`mt-1 h-4 w-4 flex-shrink-0 text-gray-400 transition-transform ${
            open ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 8.25l-7.5 7.5-7.5-7.5"
          />
        </svg>
      </button>

      {/* 展開エリア */}
      {open && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3">
          <UrlTimeline logs={data.workflow_logs} detectedAt={data.created_at} />
        </div>
      )}
    </div>
  );
}
