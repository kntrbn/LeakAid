import type { WorkflowLog } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

/** ワークフロータイプの表示名とカテゴリ */
const WORKFLOW_DISPLAY: Record<
  string,
  { label: string; waitingMessage?: string }
> = {
  search_deindex_google: {
    label: "Google検索ブロック申請",
    waitingMessage: "Google側の審査・反映待ちです（通常1〜2日）",
  },
  search_deindex_bing: {
    label: "Bing検索ブロック申請",
    waitingMessage: "Bing側の審査・反映待ちです（通常1〜3日）",
  },
  cache_removal: {
    label: "検索キャッシュ削除申請",
    waitingMessage: "Google側の審査・反映待ちです（通常1〜2日）",
  },
  hosting_removal: {
    label: "大元への削除要請",
    waitingMessage: "サイト運営者の対応待ちです",
  },
  dmca_takedown: {
    label: "DMCA テイクダウン申請",
    waitingMessage: "プラットフォーム側の審査待ちです",
  },
  evidence_capture: {
    label: "証拠保全",
  },
  url_detection: {
    label: "URL検知",
  },
};

function getDisplay(workflowType: string) {
  return WORKFLOW_DISPLAY[workflowType] ?? { label: workflowType };
}

function formatElapsed(from: string, to: string): string {
  const diffMs = new Date(to).getTime() - new Date(from).getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return "1分未満";
  if (diffMin < 60) return `${diffMin}分`;
  const hours = Math.floor(diffMin / 60);
  const mins = diffMin % 60;
  return mins > 0 ? `${hours}時間${mins}分` : `${hours}時間`;
}

function formatTime(iso: string): string {
  return new Intl.DateTimeFormat("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function dotColor(status: string): string {
  if (status === "completed") return "bg-green-500";
  if (status === "failed") return "bg-red-400";
  return "bg-gray-400";
}

export function UrlTimeline({
  logs,
  detectedAt,
}: {
  logs: WorkflowLog[];
  detectedAt: string;
}) {
  if (logs.length === 0) {
    return (
      <p className="text-xs text-gray-400">ワークフロー履歴はまだありません</p>
    );
  }

  return (
    <ol className="relative space-y-4 border-l-2 border-gray-200 pl-6">
      {logs.map((log) => {
        const display = getDisplay(log.workflow_type);
        const isCompleted = log.status === "completed";
        const isFailed = log.status === "failed";

        return (
          <li key={log.id} className="relative">
            {/* タイムラインドット */}
            <div
              className={`absolute -left-[25px] top-1 h-3 w-3 rounded-full ${dotColor(log.status)}`}
            />

            {/* ステータスバッジ + ラベル */}
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge
                variant={isCompleted ? "success" : isFailed ? "error" : "waiting"}
                label={
                  isCompleted
                    ? "送信完了"
                    : isFailed
                      ? "エラー"
                      : "処理中"
                }
              />
              <span className="text-sm font-medium text-gray-900">
                {display.label}
              </span>
              {log.started_at && (
                <span className="text-xs text-gray-400">
                  {formatTime(log.started_at)}
                </span>
              )}
            </div>

            {/* 完了時：爆速アピール */}
            {isCompleted && log.finished_at && (
              <p className="mt-1 text-xs text-green-600">
                検知から{formatElapsed(detectedAt, log.finished_at)}で送信済
              </p>
            )}

            {/* 実行中：相手待ちメッセージ */}
            {log.status === "running" && display.waitingMessage && (
              <p className="mt-1 text-xs text-gray-500">
                {display.waitingMessage}
              </p>
            )}

            {/* 失敗時 */}
            {isFailed && (
              <p className="mt-1 text-xs text-red-500">
                処理中にエラーが発生しました。再試行を準備中です。
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
