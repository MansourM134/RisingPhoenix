from django.contrib import admin

from .models import AIRefineLog, Request, RequestImage


class RequestImageInline(admin.TabularInline):
    model = RequestImage
    extra = 1
    readonly_fields = ('uploaded_at',)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester', 'category', 'status', 'deadline', 'created_at')
    list_filter = ('category', 'status', 'deadline')
    search_fields = ('title', 'description', 'requester__username')
    inlines = [RequestImageInline]


@admin.register(AIRefineLog)
class AIRefineLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'success', 'was_flagged', 'was_cached', 'input_chars', 'tokens_used', 'latency_ms', 'confidence', 'created_at')
    list_filter = ('success', 'was_flagged', 'was_cached')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'input_chars', 'was_flagged', 'was_cached', 'success', 'confidence', 'latency_ms', 'tokens_used', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
