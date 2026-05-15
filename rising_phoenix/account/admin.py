from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'reviews_given', 'reviews_received', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviews_given__username', 'reviews_received__username', 'comment']
    readonly_fields = ['created_at']