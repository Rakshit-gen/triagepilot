from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentRunViewSet,
    ApproveRunView,
    CustomerViewSet,
    KnowledgeArticleViewSet,
    RejectRunView,
    TicketViewSet,
    TriageTicketView,
)

router = DefaultRouter()
router.register("customers", CustomerViewSet)
router.register("articles", KnowledgeArticleViewSet)
router.register("tickets", TicketViewSet)
router.register("runs", AgentRunViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("tickets/<int:ticket_id>/triage/", TriageTicketView.as_view()),
    path("runs/<int:run_id>/approve/", ApproveRunView.as_view()),
    path("runs/<int:run_id>/reject/", RejectRunView.as_view()),
]
