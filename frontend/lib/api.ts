const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api";

export type Ticket = {
  id: number;
  customer: number;
  customer_email: string;
  subject: string;
  body: string;
  status: "open" | "awaiting_approval" | "resolved" | "escalated";
  created_at: string;
};

export type AgentStep = {
  id: number;
  step_number: number;
  thought: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  observation: Record<string, unknown>;
};

export type AgentRun = {
  id: number;
  ticket: number;
  ticket_subject: string;
  status: "running" | "awaiting_approval" | "escalated" | "approved" | "rejected";
  proposed_reply: string;
  escalation_reason: string;
  started_at: string;
  decided_at: string | null;
  steps: AgentStep[];
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export const fetchTickets = () =>
  getJson<{ results: Ticket[] }>("/tickets/").then((data) => data.results);

export const fetchTicket = (id: number) => getJson<Ticket>(`/tickets/${id}/`);

export const fetchRunsForTicket = (ticketId: number) =>
  getJson<{ results: AgentRun[] }>("/runs/").then((data) =>
    data.results.filter((r) => r.ticket === ticketId)
  );

export const triageTicket = (ticketId: number) =>
  postJson<AgentRun>(`/tickets/${ticketId}/triage/`);

export const approveRun = (runId: number, reply?: string) =>
  postJson<AgentRun>(`/runs/${runId}/approve/`, reply ? { reply } : undefined);

export const rejectRun = (runId: number) => postJson<AgentRun>(`/runs/${runId}/reject/`);

export const runsExportUrl = () => `${API_BASE}/runs/export/`;
