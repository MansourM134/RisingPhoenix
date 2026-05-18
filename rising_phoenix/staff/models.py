from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    display_name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=120, default='Staff Member')
    phone = PhoneNumberField(blank=True, null=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='images/avatars/', default='images/avatars/default_avatar.jpg')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'StaffProfile - {self.user.username}'


class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM         = 'spam',         'Spam'
        HARASSMENT   = 'harassment',   'Harassment'
        INAPPROPRIATE= 'inappropriate','Inappropriate Content'
        FRAUD        = 'fraud',        'Fraud'
        OTHER        = 'other',        'Other'

    class ContentType(models.TextChoices):
        USER             = 'user',             'User'
        REQUEST          = 'request',          'Request'
        PORTFOLIO_IMAGE  = 'portfolio_image',  'Portfolio Image'
        REVIEW           = 'review',           'Review'
        MESSAGE          = 'message',          'Message'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        REVIEWED  = 'reviewed',  'Under Review'
        RESOLVED  = 'resolved',  'Resolved'
        DISMISSED = 'dismissed', 'Dismissed'

    reporter     = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reports_made')
    content_type = models.CharField(max_length=20, choices=ContentType.choices, default=ContentType.USER)

    # One FK per reportable type — only one is set per report
    reported_user            = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports_received')
    reported_request         = models.ForeignKey('request.Request', null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reported_portfolio_image = models.ForeignKey('workshop.PortfolioImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reported_review          = models.ForeignKey('account.Review', null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reported_message         = models.ForeignKey('message.Message', null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')

    reason  = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)

    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    resolution_note = models.TextField(blank=True)
    reviewed_by     = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviews_done')
    reviewed_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Report by {self.reporter} on {self.content_type} ({self.status})'