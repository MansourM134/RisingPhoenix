from django.contrib import admin

from .models import Request, RequestImage


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
