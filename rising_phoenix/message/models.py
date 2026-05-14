from django.db import models
from django.contrib.auth.models import User
from proposal.models import Proposal

class Conversation(models.Model):
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        related_name='conversation'
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_conversations'
    )
    artisan = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='artisan_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation for Proposal #{self.proposal.id}"
    

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_conversation_messages'
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='conversation_images/', blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} in conversation #{self.conversation.id}"