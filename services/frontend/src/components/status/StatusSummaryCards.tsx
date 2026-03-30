import type { StatusSummary } from "@/lib/api";

function SummaryCard({
  count,
  label,
  emoji,
}: {
  count: number;
  label: string;
  emoji: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 text-center">
      <div className="text-2xl font-bold text-gray-900">{count}</div>
      <div className="mt-1 text-xs text-gray-500">
        {emoji} {label}
      </div>
    </div>
  );
}

export function StatusSummaryCards({ summary }: { summary: StatusSummary }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <SummaryCard
        count={summary.detected_url_count}
        label="検知された流出URL"
        emoji=""
      />
      <SummaryCard
        count={summary.search_block_submitted}
        label="検索ブロック申請済"
        emoji=""
      />
      <SummaryCard
        count={summary.hosting_removal_submitted}
        label="大元への削除要請済"
        emoji=""
      />
    </div>
  );
}
