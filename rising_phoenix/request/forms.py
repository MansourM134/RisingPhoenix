from django import forms

from rising_phoenix.moderation import text_is_clean
from .models import Request


class RequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.order_by('name')

    class Meta:
        model = Request
        fields = ['title', 'description', 'budget_max', 'category', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'request-input'}),
            'description': forms.Textarea(attrs={'class': 'request-textarea'}),
            'category': forms.Select(attrs={'class': 'request-select'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'request-input'}),
            'budget_max': forms.NumberInput(attrs={'class': 'request-input', 'placeholder': 'e.g. 1500 (optional)', 'min': '0'}),
        }
        labels = {
            'budget_max': 'Budget (SAR)',
        }

    def clean_title(self):
        value = self.cleaned_data.get('title', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your title contains inappropriate language. Please revise it.')
        return value

    def clean_description(self):
        value = self.cleaned_data.get('description', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your description contains inappropriate language. Please revise it.')
        return value

    def clean_budget_max(self):
        budget = self.cleaned_data.get('budget_max')
        if budget is not None and budget < 0:
            raise forms.ValidationError('Budget cannot be negative.')
        return budget