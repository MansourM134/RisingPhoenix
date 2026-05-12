from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Request(models.Model):
	class Category(models.TextChoices):
		WOODWORKING = 'woodworking', 'Woodworking'
		ART = 'art', 'Art'
		HANDMADE_GIFTS = 'handmade_gifts', 'Handmade Gifts'
		FASHION_EMBROIDERY = 'fashion_embroidery', 'Fashion & Embroidery'
		LEATHERCRAFT = 'leathercraft', 'Leathercraft'
		HOME_DECOR = 'home_decor', 'Home Decor'
		POTTERY_CERAMICS = 'pottery_ceramics', 'Pottery & Ceramics'

	class Status(models.TextChoices):
		OPEN = 'open', 'Open'
		IN_REVIEW = 'in_review', 'In review'
		CLOSED = 'closed', 'Closed'

	requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
	title = models.CharField(max_length=150)
	description = models.TextField()
	reference_image = models.ImageField(upload_to='images/requests/', blank=True, null=True)
	budget_min = models.DecimalField(max_digits=10, decimal_places=2)
	budget_max = models.DecimalField(max_digits=10, decimal_places=2)
	category = models.CharField(max_length=20, choices=Category.choices)
	deadline = models.DateField()
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
