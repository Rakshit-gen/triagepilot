"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchTickets, runsExportUrl, triageTicket, type Ticket } from "@/lib/api";

const STATUS_STYLES: Record<Ticket["status"], string> = {
  open: "bg-zinc-200 text-zinc-800 dark:bg-zinc-700 dark:text-zinc-100",
  awaiting_approval: "bg-amber-200 text-amber-900 dark:bg-amber-800 dark:text-amber-100",
  resolved: "bg-emerald-200 text-emerald-900 dark:bg-emerald-800 dark:text-emerald-100",
  escalated: "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100",
};

const FILTERS: Array<{ label: string; value: Ticket["status"] | "all" }> = [
  { label: "All", value: "all" },
  { label: "Open", value: "open" },
  { label: "Awaiting approval", value: "awaiting_approval" },
  { label: "Escalated", value: "escalated" },
  { label: "Resolved", value: "resolved" },
];

export default function Home() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [triaging, setTriaging] = useState<number | null>(null);
  const [filter, setFilter] = useState<Ticket["status"] | "all">("all");

  function reload() {
    fetchTickets().then(setTickets).catch((err) => setError(err.message));
  }

  useEffect(reload, []);

  const visibleTickets = filter === "all" ? tickets : tickets.filter((t) => t.status === filter);

  async function handleTriage(id: number) {
    setTriaging(id);
    try {
      await triageTicket(id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setTriaging(null);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold">triagepilot</h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Agent drafts replies and decides when to escalate. A human approves every send.
        </p>
        <div className="mt-2 flex gap-4 text-sm">
          <a href={runsExportUrl()} className="underline">
            Export agent run audit trail (CSV)
          </a>
          <Link href="/articles" className="underline">
            Knowledge base
          </Link>
        </div>
      </header>

      {error && <p className="mb-4 text-red-600 dark:text-red-400">{error}</p>}

      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-full px-3 py-1 text-sm ${
              filter === f.value
                ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                : "border border-zinc-300 dark:border-zinc-700"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
        {visibleTickets.map((t) => (
          <div key={t.id} className="flex items-center justify-between gap-4 py-4">
            <div>
              <Link href={`/tickets/${t.id}`} className="font-medium hover:underline">
                {t.subject}
              </Link>
              <p className="text-sm text-zinc-500">{t.customer_email}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[t.status]}`}>
                {t.status.replace("_", " ")}
              </span>
              {t.status === "open" && (
                <button
                  onClick={() => handleTriage(t.id)}
                  disabled={triaging === t.id}
                  className="rounded border border-zinc-300 px-3 py-1 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  {triaging === t.id ? "Running agent..." : "Run agent"}
                </button>
              )}
            </div>
          </div>
        ))}
        {visibleTickets.length === 0 && <p className="py-8 text-zinc-500">No tickets in this view.</p>}
      </div>
    </main>
  );
}
