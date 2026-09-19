from django.contrib import admin

from .models import Customer, KnowledgeArticle, Ticket

admin.site.register(Customer)
admin.site.register(KnowledgeArticle)
admin.site.register(Ticket)
