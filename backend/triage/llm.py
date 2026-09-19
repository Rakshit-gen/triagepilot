from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class AgentAction:
    """One reasoning step: either call a tool, or finish the run."""

    thought: str
    tool_name: str | None  # None means the agent is finishing
    tool_args: dict = field(default_factory=dict)
    final_status: str | None = None  # "resolved" | "awaiting_approval" | "escalated"
    final_reply: str | None = None


class LLMClient(Protocol):
    def next_action(
        self, *, ticket_subject: str, ticket_body: str, customer_email: str, history: list[dict]
    ) -> AgentAction: ...


ESCALATION_KEYWORDS = ("refund", "cancel my account", "lawsuit", "chargeback", "data breach")


class MockLLMClient:
    """Deterministic rule-based planner used for local dev, tests, and CI.

    No network calls and no API key required, so the agent is fully runnable
    out of the box. Swap in a real client (see `openai_client.py`) that
    implements the same `LLMClient` protocol when an API key is available.
    """

    def next_action(self, *, ticket_subject, ticket_body, customer_email, history):
        done = {h["tool_name"] for h in history}

        if "get_customer_account" not in done:
            return AgentAction(
                thought="Check who this customer is and whether their account is in good standing.",
                tool_name="get_customer_account",
                tool_args={"email": customer_email},
            )

        text = f"{ticket_subject} {ticket_body}".lower()
        if "escalate" in done:
            return AgentAction(thought="Escalated. Nothing more to do.", tool_name=None, final_status="escalated")

        if any(kw in text for kw in ESCALATION_KEYWORDS):
            return AgentAction(
                thought="This mentions billing/cancellation risk, which needs a human's judgment call.",
                tool_name="escalate",
                tool_args={"reason": "Ticket mentions billing/cancellation risk requiring human judgment."},
            )

        if "search_kb" not in done:
            return AgentAction(
                thought="Search the knowledge base for a relevant help article before drafting a reply.",
                tool_name="search_kb",
                tool_args={"query": ticket_subject},
            )

        if "draft_reply" not in done:
            kb_result = next((h["observation"] for h in history if h["tool_name"] == "search_kb"), {})
            matches = kb_result.get("matches") or []
            snippet = matches[0]["body"] if matches else None
            return AgentAction(
                thought="Draft a reply using the best knowledge base match, if any.",
                tool_name="draft_reply",
                tool_args={"ticket_subject": ticket_subject, "kb_snippet": snippet},
            )

        reply = next((h["observation"]["reply"] for h in history if h["tool_name"] == "draft_reply"), "")
        return AgentAction(
            thought="Draft is ready for a human to review before it goes out.",
            tool_name=None,
            final_status="awaiting_approval",
            final_reply=reply,
        )
