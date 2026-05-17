from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'details']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide any context that will help the moderation team review this report...',
            }),
        }
        labels = {
            'reason': 'Reason for report',
            'details': 'Additional details (optional)',
        }
