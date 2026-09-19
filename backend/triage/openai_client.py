"""Optional real LLM-backed planner.

Not used unless OPENAI_API_KEY is set — the engine falls back to
MockLLMClient otherwise, so the project runs and tests fully offline.
Talks to any OpenAI-compatible chat completions endpoint using JSON mode
to pick the next tool call.
"""

from __future__ import annotations

import json
import os
import urllib.request

from .llm import AgentAction

SYSTEM_PROMPT = (
    "You are a support ticket triage agent. Given a ticket and the results of "
    "tools already called, respond with JSON describing the next step: "
    '{"thought": str, "tool_name": str | null, "tool_args": object, '
    '"final_status": "resolved" | "awaiting_approval" | "escalated" | null, '
    '"final_reply": str | null}. Set tool_name to null only when finishing. '
    "Prefer checking the account, then searching the knowledge base, before "
    "drafting a reply. Escalate anything involving refunds, cancellations, or "
    "legal risk instead of replying yourself."
)


class OpenAIClient:
    """Real LLM-backed planner. Requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]

    def next_action(self, *, ticket_subject, ticket_body, customer_email, history) -> AgentAction:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({
                    "ticket_subject": ticket_subject,
                    "ticket_body": ticket_body,
                    "customer_email": customer_email,
                    "history": history,
                })},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())
        content = json.loads(body["choices"][0]["message"]["content"])
        return AgentAction(
            thought=content.get("thought", ""),
            tool_name=content.get("tool_name"),
            tool_args=content.get("tool_args") or {},
            final_status=content.get("final_status"),
            final_reply=content.get("final_reply"),
        )


def get_llm_client():
    """Real client if OPENAI_API_KEY is set, else the deterministic mock."""
    from .llm import MockLLMClient

    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIClient()
    return MockLLMClient()
