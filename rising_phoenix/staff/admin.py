from django.contrib import admin
from .models import Report, StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'display_name', 'role', 'phone', 'updated_at')
	search_fields = ('user__username', 'display_name', 'role', 'phone')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
	list_display = ('id', 'reporter', 'content_type', 'reason', 'status', 'created_at')
	list_filter = ('content_type', 'reason', 'status')
	search_fields = ('reporter__username', 'details', 'resolution_note')
