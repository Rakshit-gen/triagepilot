# triagepilot

A support ticket assistant for small teams. For each ticket it looks up the customer, searches your help articles and drafts a reply, or hands the ticket to a person when it touches refunds, cancellations or legal risk. Nothing goes out until a human approves it, and you can read every step the agent took to get there.

## Why

A 2 to 5 person support team at an early SaaS company spends most of the day on the same few ticket types: password resets, "how do I export this", billing questions. Tools like Intercom Fin, Ada and Forethought handle this, but they are priced for teams already running Intercom or Zendesk at scale, and they show you a reply without showing why the bot thought it was safe to send.

triagepilot is the small version: a visible step-by-step trace for every ticket, and a human approval on every reply.

## How the agent works

Each ticket runs through a loop of up to 6 steps. In each step the planner looks at the ticket and everything found so far, then either calls a tool or finishes.

| Tool | What it does |
|---|---|
| `get_customer_account` | Plan (free, pro, enterprise) and account status for the sender's email |
| `search_kb` | Keyword search over help articles, top 3 matches |
| `draft_reply` | Builds a reply around the best article snippet |
| `escalate` | Marks the ticket for a human, with a reason |

A run ends in one of three ways: a draft waiting for approval, an escalation, or the step budget running out (which also goes to approval, with whatever it has). Every step is saved as a row with the planner's thought, the tool, its arguments and its output.

### Two planners, one loop

The planner is an interface (`LLMClient` in `backend/triage/llm.py`) with two versions:

- **`MockLLMClient`** (default). Fixed rules, no network, no key. It checks the account, escalates if the ticket mentions `refund`, `cancel my account`, `lawsuit`, `chargeback` or `data breach`, otherwise searches the knowledge base and drafts a reply. The project runs and its tests pass with zero setup.
- **`OpenAIClient`**. Used automatically when `OPENAI_API_KEY` is set. It sends the ticket and step history to `gpt-4o-mini` and asks for the next action as JSON.

The loop, the tools and the saved trace are the same either way. Only the decision maker changes.

### What approval does

- **Approve** marks the run approved and the ticket resolved. You can send an edited reply in the same call and it replaces the draft.
- **Reject** marks the run rejected and puts the ticket back to open.

## Quickstart

Backend (Python 3.12):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Frontend (Node 20), in another terminal:

```bash
cd frontend
cp env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000, pick an open ticket, click **Run agent**, read the trace, then approve or reject.

To use a real model, start the backend with `OPENAI_API_KEY` set.

## Configuration

| Variable | Where | What it does |
|---|---|---|
| `OPENAI_API_KEY` | backend | Switches the planner from the rule-based mock to OpenAI |
| `NEXT_PUBLIC_API_BASE` | frontend | Backend URL, default `http://127.0.0.1:8000/api` |

## API

All under `/api/`.

| Method | Path | What it does |
|---|---|---|
| `POST` | `/tickets/{id}/triage/` | Run the agent on a ticket, returns the run with its steps |
| `POST` | `/runs/{id}/approve/` | Approve, optional `{"reply": "..."}` to send an edited version |
| `POST` | `/runs/{id}/reject/` | Reject and reopen the ticket |
| `GET` | `/runs/export/` | All runs as CSV |
| CRUD | `/customers/`, `/articles/`, `/tickets/` | Manage the data |
| `GET` | `/runs/`, `/runs/{id}/` | Read runs and their steps |

## Layout

```
backend/triage/engine.py         the observe, plan, act loop
backend/triage/llm.py            planner interface and the rule-based mock
backend/triage/openai_client.py  OpenAI planner
backend/triage/tools.py          the four tools and their registry
backend/triage/models.py         Customer, KnowledgeArticle, Ticket, AgentRun, AgentStep
backend/triage/tests.py          engine and API tests
frontend/app/                    ticket list, ticket detail with trace, articles
```

Tests: `cd backend && python manage.py test`. CI runs them plus a frontend build.

## Limits

- No helpdesk or email integration. Tickets are created in the app, and approving a reply does not send it anywhere.
- Each run looks at one ticket on its own, with no thread history.
- Knowledge base search is keyword matching. Easy to audit, fine for a few dozen articles, not for hundreds.
- With the mock planner, the escalation keywords are enforced in code. With the OpenAI planner, escalation depends on the model following its prompt.
- SQLite and no auth. Meant for local use and demos.
