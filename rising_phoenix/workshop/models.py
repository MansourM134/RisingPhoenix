from django.db import models
from account.models import ArtisanProfile

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
class WorkshopProfile(models.Model):
	artisan = models.OneToOneField(ArtisanProfile, on_delete=models.CASCADE, related_name='workshop_profile')
	workshop_name = models.CharField(max_length=150)
	tagline = models.CharField(max_length=200, blank=True)
	description = models.TextField(blank=True)
	services = models.TextField(help_text='List the services you offer', blank=True)
	location = models.CharField(max_length=200, blank=True)
	phone = models.CharField(max_length=30, blank=True)
	cover_image = models.ImageField(upload_to='images/workshops/', blank=True, null=True)
	is_published = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	categories = models.ManyToManyField(Category, blank=True)
	

	def __str__(self):
		return f"WorkshopProfile - {self.workshop_name}"


class PortfolioImage(models.Model):
	workshop = models.ForeignKey(WorkshopProfile, on_delete=models.CASCADE, related_name='portfolio_images')
	image = models.ImageField(upload_to='images/workshop_portfolio/')
	caption = models.CharField(max_length=255, blank=True)
	is_pinned = models.BooleanField(default=False)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-is_pinned', '-uploaded_at']

	def __str__(self):
		return f"Portfolio - {self.workshop.workshop_name}"
	


class CompletedProject(models.Model):
	workshop = models.ForeignKey(WorkshopProfile, on_delete=models.CASCADE, related_name='completed_projects')
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	date_completed = models.DateField(null=True, blank=True)
	main_image = models.ImageField(upload_to='images/completed_projects/', blank=True, null=True)
	request = models.ForeignKey('request.Request', null=True, blank=True, on_delete=models.SET_NULL, related_name='completed_projects')
	is_featured = models.BooleanField(default=False)
	is_published = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-is_featured', '-date_completed', '-created_at']

	def __str__(self):
		return f"Project - {self.workshop.workshop_name}: {self.title}"


class CompletedProjectImage(models.Model):
	project = models.ForeignKey(CompletedProject, on_delete=models.CASCADE, related_name='images')
	image = models.ImageField(upload_to='images/completed_project_images/')
	caption = models.CharField(max_length=255, blank=True)
	is_before = models.BooleanField(default=False)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	pair_group = models.IntegerField(default=0, help_text='Group images into pairs by number (optional)')

	class Meta:
		ordering = ['pair_group', '-is_before', '-uploaded_at']

	def __str__(self):
		return f"ProjectImage - {self.project.title} ({'before' if self.is_before else 'after'})"





