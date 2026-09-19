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
