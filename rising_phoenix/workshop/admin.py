from django.contrib import admin
from .models import WorkshopProfile, PortfolioImage, Category, CompletedProject, CompletedProjectImage

# Register your models here.


admin.site.register(WorkshopProfile)
admin.site.register(PortfolioImage)
admin.site.register(Category)


class CompletedProjectImageInline(admin.TabularInline):
	model = CompletedProjectImage
	extra = 1


@admin.register(CompletedProject)
class CompletedProjectAdmin(admin.ModelAdmin):
	list_display = ('title', 'workshop', 'request', 'date_completed', 'is_featured', 'is_published')
	list_filter = ('is_featured', 'is_published')
	search_fields = ('title', 'description', 'request__title')
	inlines = [CompletedProjectImageInline]
