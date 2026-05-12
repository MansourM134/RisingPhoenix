from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM = 'spam', 'Spam'
        INAPPROPRIATE = 'inappropriate', 'Inappropriate Content'
        FRAUD = 'fraud', 'Fraud'
        OTHER = 'other', 'Other'

    reporter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reports_made')
    reported_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reports_received')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviews_done')
    created_at = models.DateTimeField(auto_now_add=True)