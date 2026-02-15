const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

export async function startIntake(
  token: string
): Promise<{ workflow_id: string }> {
  const res = await fetch(`${API_BASE}/intake/start`, {
    method: "POST",
    headers: authHeaders(token),
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
