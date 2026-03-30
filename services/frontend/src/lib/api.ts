const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

export async function startIntake(
  token: string,
  userName?: string
): Promise<{ workflow_id: string }> {
  const res = await fetch(`${API_BASE}/intake/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ user_name: userName || "" }),
  });
  if (!res.ok) throw new Error("Failed to start intake");
  return res.json();
}

export async function sendMessage(
  workflowId: string,
  message: string,
  token: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/intake/${workflowId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send message");
}

export async function getResponse(
  workflowId: string,
  token: string
): Promise<{ response: string }> {
  const res = await fetch(`${API_BASE}/intake/${workflowId}/response`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to get response");
  return res.json();
}

export async function getStatus(
  workflowId: string,
  token: string
): Promise<{ is_complete: boolean }> {
  const res = await fetch(`${API_BASE}/intake/${workflowId}/status`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to get status");
  return res.json();
}

export async function uploadImage(
  workflowId: string,
  token: string,
  file: File
): Promise<{ status: string; gcs_uri: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/intake/${workflowId}/upload-image`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  if (!res.ok) throw new Error("Failed to upload image");
  return res.json();
}

// ---------------------------------------------------------------------------
// ステータスダッシュボード
// ---------------------------------------------------------------------------
export type StatusSummary = {
  detected_url_count: number;
  search_block_submitted: number;
  hosting_removal_submitted: number;
};

export type WorkflowLog = {
  id: string;
  workflow_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
};

export type TargetUrlWithLogs = {
  id: string;
  url: string;
  website_name: string | null;
  source_status: string;
  search_status: string;
  created_at: string;
  workflow_logs: WorkflowLog[];
};

export async function getStatusSummary(
  token: string
): Promise<StatusSummary> {
  const res = await fetch(`${API_BASE}/status/summary`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to get status summary");
  return res.json();
}

export async function getStatusUrls(
  token: string
): Promise<TargetUrlWithLogs[]> {
  const res = await fetch(`${API_BASE}/status/urls`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to get status urls");
  return res.json();
}
