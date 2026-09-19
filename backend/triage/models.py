from django.db import models


class Customer(models.Model):
    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    account_status = models.CharField(max_length=20, default="active")
    signed_up_at = models.DateTimeField()

    def __str__(self):
        return self.email


class KnowledgeArticle(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    tags = models.CharField(max_length=200, blank=True, help_text="comma-separated")

    def __str__(self):
        return self.title


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting approval"
        RESOLVED = "resolved", "Resolved"
        ESCALATED = "escalated", "Escalated"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"#{self.id} {self.subject}"


class AgentRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting approval"
        ESCALATED = "escalated", "Escalated"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="agent_runs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    proposed_reply = models.TextField(blank=True)
    escalation_reason = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Run #{self.id} for ticket #{self.ticket_id} ({self.status})"


class AgentStep(models.Model):
    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    thought = models.TextField()
    tool_name = models.CharField(max_length=100, blank=True)
    tool_args = models.JSONField(default=dict)
    observation = models.JSONField(default=dict)

    class Meta:
        ordering = ["step_number"]

    def __str__(self):
        return f"Step {self.step_number} of run #{self.run_id}: {self.tool_name or 'finish'}"
