"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  approveRun,
  fetchRunsForTicket,
  fetchTicket,
  rejectRun,
  triageTicket,
  type AgentRun,
  type Ticket,
} from "@/lib/api";

export default function TicketDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const ticketId = Number(id);

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [editedReply, setEditedReply] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reload() {
    fetchTicket(ticketId).then(setTicket).catch((err) => setError(err.message));
    fetchRunsForTicket(ticketId).then(setRuns).catch((err) => setError(err.message));
  }

  useEffect(reload, [ticketId]);

  const latestRun = runs[0];

  useEffect(() => {
    if (latestRun?.proposed_reply) setEditedReply(latestRun.proposed_reply);
  }, [latestRun?.id, latestRun?.proposed_reply]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!ticket) return <main className="mx-auto max-w-3xl px-5 py-10">Loading…</main>;

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to queue
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">{ticket.subject}</h1>
      <p className="text-zinc-500">
        {ticket.customer_email} · status: {ticket.status.replace("_", " ")}
      </p>
      <p className="mt-4 whitespace-pre-wrap rounded border border-zinc-200 p-4 dark:border-zinc-800">
        {ticket.body}
      </p>

      {error && <p className="mt-4 text-red-600 dark:text-red-400">{error}</p>}

      {ticket.status === "open" && (
        <button
          onClick={() => run(() => triageTicket(ticketId))}
          disabled={busy}
          className="mt-6 rounded border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          Run agent
        </button>
      )}

      {latestRun && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">Agent trace</h2>
          <ol className="space-y-3">
            {latestRun.steps.map((step) => (
              <li key={step.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                <p className="font-medium">
                  Step {step.step_number}
                  {step.tool_name && ` · ${step.tool_name}`}
                </p>
                <p className="text-zinc-600 dark:text-zinc-400">{step.thought}</p>
                {step.tool_name && (
                  <pre className="mt-2 overflow-x-auto rounded bg-zinc-100 p-2 text-xs dark:bg-zinc-900">
                    {JSON.stringify(step.observation, null, 2)}
                  </pre>
                )}
              </li>
            ))}
          </ol>

          {latestRun.status === "escalated" && (
            <p className="mt-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
              Escalated: {latestRun.escalation_reason}
            </p>
          )}

          {latestRun.status === "awaiting_approval" && (
            <div className="mt-4">
              <label className="mb-1 block text-sm font-medium">Proposed reply</label>
              <textarea
                value={editedReply}
                onChange={(e) => setEditedReply(e.target.value)}
                rows={6}
                className="w-full rounded border border-zinc-300 p-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              />
              <div className="mt-3 flex gap-3">
                <button
                  onClick={() => run(() => approveRun(latestRun.id, editedReply))}
                  disabled={busy}
                  className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  Approve & send
                </button>
                <button
                  onClick={() => run(() => rejectRun(latestRun.id))}
                  disabled={busy}
                  className="rounded border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  Reject
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
