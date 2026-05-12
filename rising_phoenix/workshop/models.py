from django.db import models
from account.models import ArtisanProfile

# Create your models here.


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

	def __str__(self):
		return f"WorkshopProfile - {self.workshop_name}"
