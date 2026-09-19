from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import Customer, KnowledgeArticle


@dataclass
class ToolResult:
    tool_name: str
    args: dict
    output: dict


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., dict]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def specs(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def call(self, name: str, args: dict) -> ToolResult:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        output = self._tools[name].fn(**args)
        return ToolResult(tool_name=name, args=args, output=output)


def get_customer_account(email: str) -> dict:
    try:
        customer = Customer.objects.get(email=email)
    except Customer.DoesNotExist:
        return {"found": False}
    return {"found": True, "plan": customer.plan, "account_status": customer.account_status}


def search_kb(query: str) -> dict:
    terms = [t.lower() for t in query.split() if len(t) > 3]
    matches = []
    for article in KnowledgeArticle.objects.all():
        haystack = f"{article.title} {article.body} {article.tags}".lower()
        if any(term in haystack for term in terms):
            matches.append({"id": article.id, "title": article.title, "body": article.body})
    return {"matches": matches[:3]}


def draft_reply(ticket_subject: str, kb_snippet: str | None) -> dict:
    if kb_snippet:
        reply = (
            f'Hi, thanks for reaching out about "{ticket_subject}".\n\n'
            f"{kb_snippet}\n\nLet us know if that resolves it."
        )
    else:
        reply = (
            f'Hi, thanks for reaching out about "{ticket_subject}". '
            "We're looking into this and will follow up shortly."
        )
    return {"reply": reply}


def escalate(reason: str) -> dict:
    return {"escalated": True, "reason": reason}


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool(
        "get_customer_account",
        "Look up a customer's plan and account status by email.",
        get_customer_account,
    ))
    registry.register(Tool(
        "search_kb",
        "Search the knowledge base for articles relevant to a query.",
        search_kb,
    ))
    registry.register(Tool(
        "draft_reply",
        "Draft a reply to the customer given the ticket subject and an optional KB snippet.",
        draft_reply,
    ))
    registry.register(Tool(
        "escalate",
        "Escalate the ticket to a human agent with a reason.",
        escalate,
    ))
    return registry
