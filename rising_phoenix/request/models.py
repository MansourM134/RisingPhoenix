from django.conf import settings
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


class RequestImage(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/requests/')
    caption = models.CharField(max_length=160, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Image for '{self.request.title}'"


class AIRefineLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ai_refine_logs')
    input_chars = models.PositiveIntegerField()
    was_flagged = models.BooleanField(default=False)
    was_cached = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    confidence = models.FloatField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AIRefineLog user={self.user_id} success={self.success} at {self.created_at}"
