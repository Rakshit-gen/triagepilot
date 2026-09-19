from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import run_agent
from .models import AgentRun, Customer, KnowledgeArticle, Ticket
from .serializers import (
    AgentRunSerializer,
    CustomerSerializer,
    KnowledgeArticleSerializer,
    TicketSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("email")
    serializer_class = CustomerSerializer


class KnowledgeArticleViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeArticle.objects.all().order_by("title")
    serializer_class = KnowledgeArticleSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("customer").all().order_by("-created_at")
    serializer_class = TicketSerializer


class AgentRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentRun.objects.select_related("ticket").prefetch_related("steps").order_by("-started_at")
    serializer_class = AgentRunSerializer


class TriageTicketView(APIView):
    """Kick off an agent run for a ticket."""

    def post(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        run = run_agent(ticket)
        ticket.status = {
            AgentRun.Status.ESCALATED: Ticket.Status.ESCALATED,
        }.get(run.status, Ticket.Status.AWAITING_APPROVAL)
        ticket.save()
        return Response(AgentRunSerializer(run).data, status=status.HTTP_201_CREATED)


class ApproveRunView(APIView):
    """Human approves the agent's proposed reply; ticket is marked resolved."""

    def post(self, request, run_id):
        try:
            run = AgentRun.objects.select_related("ticket").get(id=run_id)
        except AgentRun.DoesNotExist:
            return Response({"detail": "Run not found."}, status=status.HTTP_404_NOT_FOUND)

        edited_reply = request.data.get("reply")
        if edited_reply:
            run.proposed_reply = edited_reply
        run.status = AgentRun.Status.APPROVED
        run.decided_at = timezone.now()
        run.save()

        run.ticket.status = Ticket.Status.RESOLVED
        run.ticket.save()
        return Response(AgentRunSerializer(run).data)


class RejectRunView(APIView):
    """Human rejects the agent's proposed reply; ticket goes back to open."""

    def post(self, request, run_id):
        try:
            run = AgentRun.objects.select_related("ticket").get(id=run_id)
        except AgentRun.DoesNotExist:
            return Response({"detail": "Run not found."}, status=status.HTTP_404_NOT_FOUND)

        run.status = AgentRun.Status.REJECTED
        run.decided_at = timezone.now()
        run.save()

        run.ticket.status = Ticket.Status.OPEN
        run.ticket.save()
        return Response(AgentRunSerializer(run).data)
