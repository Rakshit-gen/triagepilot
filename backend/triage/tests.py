from django.test import TestCase
from django.utils import timezone

from .engine import run_agent
from .models import AgentRun, Customer, KnowledgeArticle, Ticket
from .tools import ToolRegistry, Tool, build_default_registry


class RunAgentTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.customer = Customer.objects.create(
            email="dana@acme.com", name="Dana", account_status="active", signed_up_at=self.now,
        )

    def test_finds_kb_article_and_drafts_reply(self):
        KnowledgeArticle.objects.create(
            title="Resetting your password",
            body="Go to Settings > Security > Reset password.",
            tags="password,login",
        )
        ticket = Ticket.objects.create(
            customer=self.customer, subject="password reset help", body="I can't log in",
            created_at=self.now,
        )
        run = run_agent(ticket)
        self.assertEqual(run.status, AgentRun.Status.AWAITING_APPROVAL)
        self.assertIn("Settings > Security", run.proposed_reply)

    def test_drafts_generic_reply_when_no_kb_match(self):
        ticket = Ticket.objects.create(
            customer=self.customer, subject="weird rendering glitch", body="the dashboard looks off",
            created_at=self.now,
        )
        run = run_agent(ticket)
        self.assertEqual(run.status, AgentRun.Status.AWAITING_APPROVAL)
        self.assertIn("looking into this", run.proposed_reply)

    def test_billing_risk_ticket_is_escalated_not_auto_replied(self):
        ticket = Ticket.objects.create(
            customer=self.customer, subject="I want a refund", body="please cancel my account and refund me",
            created_at=self.now,
        )
        run = run_agent(ticket)
        self.assertEqual(run.status, AgentRun.Status.ESCALATED)
        self.assertEqual(run.proposed_reply, "")
        self.assertTrue(run.escalation_reason)

    def test_every_step_is_recorded_for_audit(self):
        ticket = Ticket.objects.create(
            customer=self.customer, subject="how do I export data", body="need a CSV export",
            created_at=self.now,
        )
        run = run_agent(ticket)
        tool_sequence = [s.tool_name for s in run.steps.all()]
        self.assertEqual(tool_sequence, ["get_customer_account", "search_kb", "draft_reply", ""])

    def test_unknown_customer_is_still_handled(self):
        Customer.objects.all().delete()
        orphan_customer = Customer.objects.create(
            email="ghost@nowhere.com", name="Ghost", signed_up_at=self.now,
        )
        ticket = Ticket.objects.create(
            customer=orphan_customer, subject="hello", body="anyone there", created_at=self.now,
        )
        run = run_agent(ticket)
        self.assertEqual(run.status, AgentRun.Status.AWAITING_APPROVAL)


class ToolRegistryTests(TestCase):
    def test_unknown_tool_raises(self):
        registry = ToolRegistry()
        with self.assertRaises(KeyError):
            registry.call("nope", {})

    def test_default_registry_has_expected_tools(self):
        registry = build_default_registry()
        names = {spec["name"] for spec in registry.specs()}
        self.assertEqual(names, {"get_customer_account", "search_kb", "draft_reply", "escalate"})

    def test_registered_tool_is_callable(self):
        registry = ToolRegistry()
        registry.register(Tool("echo", "echoes back", lambda value: {"value": value}))
        result = registry.call("echo", {"value": "hi"})
        self.assertEqual(result.output, {"value": "hi"})


class TriageApiTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.customer = Customer.objects.create(
            email="dana@acme.com", name="Dana", signed_up_at=self.now,
        )
        self.ticket = Ticket.objects.create(
            customer=self.customer, subject="dashboard export", body="need a CSV export",
            created_at=self.now,
        )

    def test_triage_endpoint_creates_a_run_and_updates_ticket_status(self):
        response = self.client.post(f"/api/tickets/{self.ticket.id}/triage/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "awaiting_approval")
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_APPROVAL)

    def test_triage_endpoint_404s_for_missing_ticket(self):
        response = self.client.post("/api/tickets/999/triage/")
        self.assertEqual(response.status_code, 404)

    def test_approve_marks_run_approved_and_ticket_resolved(self):
        run = run_agent(self.ticket)
        response = self.client.post(f"/api/runs/{run.id}/approve/", data={"reply": "edited reply"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        run.refresh_from_db()
        self.ticket.refresh_from_db()
        self.assertEqual(run.status, AgentRun.Status.APPROVED)
        self.assertEqual(run.proposed_reply, "edited reply")
        self.assertEqual(self.ticket.status, Ticket.Status.RESOLVED)

    def test_reject_reopens_ticket(self):
        run = run_agent(self.ticket)
        response = self.client.post(f"/api/runs/{run.id}/reject/")
        self.assertEqual(response.status_code, 200)
        run.refresh_from_db()
        self.ticket.refresh_from_db()
        self.assertEqual(run.status, AgentRun.Status.REJECTED)
        self.assertEqual(self.ticket.status, Ticket.Status.OPEN)
