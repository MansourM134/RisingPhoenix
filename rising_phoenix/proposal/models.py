from django.conf import settings
from django.db import models


class Proposal(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    request = models.ForeignKey(
        'request.Request',
        on_delete=models.CASCADE,
        related_name='proposals',
    )
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proposals',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # One proposal per artisan per request
        unique_together = [['request', 'artisan']]

    def __str__(self):
        return f"Proposal by {self.artisan.username} for '{self.request.title}'"

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def is_accepted(self):
        return self.status == self.Status.ACCEPTED


class ProposalImage(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/proposals/')
    caption = models.CharField(max_length=160, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Image for proposal by '{self.proposal.artisan.username}'"
