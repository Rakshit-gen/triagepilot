from django.core.management.base import BaseCommand
from django.utils import timezone

from triage.models import Customer, KnowledgeArticle, Ticket


class Command(BaseCommand):
    help = "Seed a small, reproducible demo dataset for local development."

    def handle(self, *args, **options):
        now = timezone.now()

        dana, _ = Customer.objects.get_or_create(
            email="dana@acme.com",
            defaults={"name": "Dana Kapoor", "plan": Customer.Plan.PRO, "signed_up_at": now},
        )
        raj, _ = Customer.objects.get_or_create(
            email="raj@brightloop.io",
            defaults={"name": "Raj Mehta", "plan": Customer.Plan.FREE, "signed_up_at": now},
        )
        wren, _ = Customer.objects.get_or_create(
            email="wren@northfield.co",
            defaults={"name": "Wren Ostrowski", "plan": Customer.Plan.ENTERPRISE, "signed_up_at": now},
        )

        KnowledgeArticle.objects.get_or_create(
            title="Resetting your password",
            defaults={
                "body": "Go to Settings > Security > Reset password, then check your inbox for the reset link.",
                "tags": "password,login,security",
            },
        )
        KnowledgeArticle.objects.get_or_create(
            title="Exporting your data as CSV",
            defaults={
                "body": "Open any report and click Export > CSV in the top-right corner of the table.",
                "tags": "export,csv,data",
            },
        )
        KnowledgeArticle.objects.get_or_create(
            title="Inviting teammates",
            defaults={
                "body": "Go to Settings > Team > Invite, then enter their email address.",
                "tags": "team,invite,members",
            },
        )

        Ticket.objects.get_or_create(
            customer=dana, subject="Can't log in, password reset",
            defaults={"body": "I forgot my password and the reset email never showed up.", "created_at": now},
        )
        Ticket.objects.get_or_create(
            customer=raj, subject="How do I export my report",
            defaults={"body": "I need a CSV of last month's numbers for my accountant.", "created_at": now},
        )
        Ticket.objects.get_or_create(
            customer=wren, subject="I want a refund and want to cancel my account",
            defaults={"body": "We're not renewing, please refund the last invoice and cancel.", "created_at": now},
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo customers, KB articles, and tickets."))
