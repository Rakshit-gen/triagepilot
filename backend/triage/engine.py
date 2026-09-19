from django.utils import timezone

from .llm import LLMClient, MockLLMClient
from .models import AgentRun, AgentStep, Ticket
from .tools import build_default_registry

MAX_STEPS = 6


def run_agent(ticket: Ticket, llm: LLMClient | None = None) -> AgentRun:
    """Drive one ticket through the observe -> plan -> act loop until the
    planner finishes (proposes a reply, escalates, or hits the step budget).
    """
    llm = llm or MockLLMClient()
    registry = build_default_registry()
    run = AgentRun.objects.create(ticket=ticket)
    history: list[dict] = []

    for step_number in range(1, MAX_STEPS + 1):
        action = llm.next_action(
            ticket_subject=ticket.subject,
            ticket_body=ticket.body,
            customer_email=ticket.customer.email,
            history=history,
        )

        if action.tool_name is None:
            _finish(run, action, history)
            AgentStep.objects.create(
                run=run, step_number=step_number, thought=action.thought,
                tool_name="", tool_args={}, observation={},
            )
            return run

        result = registry.call(action.tool_name, action.tool_args)
        AgentStep.objects.create(
            run=run, step_number=step_number, thought=action.thought,
            tool_name=action.tool_name, tool_args=action.tool_args, observation=result.output,
        )
        history.append({"tool_name": action.tool_name, "observation": result.output})

    run.status = AgentRun.Status.AWAITING_APPROVAL
    run.decided_at = timezone.now()
    run.save()
    return run


def _finish(run: AgentRun, action, history: list[dict]) -> None:
    run.status = action.final_status or AgentRun.Status.AWAITING_APPROVAL
    run.proposed_reply = action.final_reply or ""
    if run.status == AgentRun.Status.ESCALATED:
        run.escalation_reason = next(
            (h["observation"].get("reason", "") for h in history if h["tool_name"] == "escalate"), ""
        )
    run.decided_at = timezone.now()
    run.save()
