from rest_framework import serializers

from .models import AgentRun, AgentStep, Customer, KnowledgeArticle, Ticket


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "email", "name", "plan", "account_status", "signed_up_at"]


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = ["id", "title", "body", "tags"]


class TicketSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source="customer.email", read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "customer", "customer_email", "subject", "body", "status", "created_at"]


class AgentStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentStep
        fields = ["id", "step_number", "thought", "tool_name", "tool_args", "observation"]


class AgentRunSerializer(serializers.ModelSerializer):
    steps = AgentStepSerializer(many=True, read_only=True)
    ticket_subject = serializers.CharField(source="ticket.subject", read_only=True)

    class Meta:
        model = AgentRun
        fields = [
            "id", "ticket", "ticket_subject", "status", "proposed_reply",
            "escalation_reason", "started_at", "decided_at", "steps",
        ]
