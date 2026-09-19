# triagepilot

An agentic support-ticket triage assistant that drafts replies and decides
when to escalate — with a human approving every reply before it goes out.

## The problem

Small support teams (2-5 people at an early SaaS company) spend most of
their day on the same handful of ticket types: password resets, "how do I
export this," billing questions. Full AI-support platforms like Intercom
Fin, Ada, or Forethought solve this, but they're priced and scoped for
teams already running Intercom or Zendesk at scale, and they hand you a
black box: a reply appears with no visible reasoning for why the bot
decided it was safe to answer automatically.

`triagepilot` is a smaller, auditable version of the same idea. Every
ticket goes through a visible reasoning trace — which tools the agent
called, what it found, why it drafted the reply it did — and nothing is
sent to a customer without a human clicking approve. Tickets touching
refunds, cancellations, or anything with legal/financial risk are
escalated straight to a human instead of drafted at all, by design, not
as a fallback.

## How the agent works

This isn't a single prompt-and-response call. Each ticket runs through an
observe → plan → act loop with up to 6 steps, and every step is persisted:

1. **Observe**: read the ticket and the customer's account.
2. **Plan**: decide the next tool call, or that it's ready to finish.
3. **Act**: call a tool — `get_customer_account`, `search_kb`,
   `draft_reply`, or `escalate` — and record its output.
4. Repeat until the planner finishes with a proposed reply, an escalation,
   or the step budget runs out.

The planner (`LLMClient`) is a protocol, not a hardcoded call. By default
it's `MockLLMClient` — a deterministic, rule-based planner with no network
calls and no API key, so the project runs and its test suite passes with
zero setup. Set `OPENAI_API_KEY` and the engine automatically switches to
`OpenAIClient`, which asks a real model for the same JSON-shaped decision
at each step. Nothing else about the loop, the tools, or the audit trail
changes — the planner is the only thing being swapped.

## Stack

- **Backend**: Django + Django REST Framework, SQLite for local/demo use.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind.

## Running locally

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# frontend
cd frontend
npm install
npm run dev
```

Open the frontend, click "Run agent" on an open ticket, and read the
step-by-step trace before approving or rejecting the draft. Set
`OPENAI_API_KEY` in the backend's environment to use a real model instead
of the deterministic mock planner.

## What's not built

No real email/helpdesk integration (Zendesk, Intercom, Gmail) — tickets
are created directly in the app, not pulled from a live inbox. No
multi-turn conversation handling; each run triages one ticket in
isolation. No fine-tuning or retrieval embeddings for the knowledge base
search — it's keyword matching, which is honest about what it is and easy
to audit, but won't scale past a few dozen articles.
