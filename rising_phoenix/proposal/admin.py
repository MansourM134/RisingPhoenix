from django.contrib import admin

from .models import Proposal, ProposalImage


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['artisan', 'request', 'price', 'estimated_days', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['artisan__username', 'request__title']
    ordering = ['-created_at']


@admin.register(ProposalImage)
class ProposalImageAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'caption', 'uploaded_at']
