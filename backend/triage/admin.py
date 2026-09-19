from django.contrib import admin

from .models import AgentRun, AgentStep, Customer, KnowledgeArticle, Ticket

admin.site.register(Customer)
admin.site.register(KnowledgeArticle)
admin.site.register(Ticket)
admin.site.register(AgentRun)
admin.site.register(AgentStep)
