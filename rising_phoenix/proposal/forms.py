from django import forms

from rising_phoenix.moderation import text_is_clean
from .models import Proposal


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['price', 'estimated_days', 'message']
        widgets = {
            'price': forms.NumberInput(attrs={
                'class': 'proposal-input',
                'placeholder': 'e.g. 1500',
                'min': '0',
                'step': '0.01',
            }),
            'estimated_days': forms.NumberInput(attrs={
                'class': 'proposal-input',
                'placeholder': 'e.g. 7',
                'min': '1',
            }),
            'message': forms.Textarea(attrs={
                'class': 'proposal-textarea',
                'placeholder': 'Describe your approach, experience, and why you are the right fit for this project.',
                'rows': 5,
            }),
        }
        labels = {
            'price': 'Your price (SAR)',
            'estimated_days': 'Estimated completion (days)',
            'message': 'Proposal message',
        }

    def clean_message(self):
        value = self.cleaned_data.get('message', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your proposal message contains inappropriate language. Please revise it.')
        return value

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        return price

    def clean_estimated_days(self):
        days = self.cleaned_data.get('estimated_days')
        if days is not None and days < 1:
            raise forms.ValidationError('Estimated days must be at least 1.')
        return days
