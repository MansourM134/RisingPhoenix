from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Request(models.Model):
	class Status(models.TextChoices):
		OPEN = 'open', 'Open'
		IN_REVIEW = 'in_review', 'In review'
		TIME_ENDED = 'time_ended', 'Time ended'
		CLOSED = 'closed', 'Closed'

	requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
	title = models.CharField(max_length=150)
	description = models.TextField()
	budget_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	budget_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	category = models.ForeignKey('workshop.Category', on_delete=models.PROTECT, related_name='requests')
	deadline = models.DateField(blank=True, null=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title

	def clean(self):
		super().clean()
		if self.budget_min and self.budget_max and self.budget_min > self.budget_max:
			raise ValidationError({'budget_max': 'Maximum budget must be greater than or equal to minimum budget.'})


class RequestImage(models.Model):
	request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='images')
	image = models.ImageField(upload_to='images/requests/')
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['uploaded_at']

	def __str__(self):
		return f"Image for '{self.request.title}'"
