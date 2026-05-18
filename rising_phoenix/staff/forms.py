from django import forms
from .models import Report, StaffProfile


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['display_name', 'role', 'phone', 'bio', 'avatar']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Display name'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+966...'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Short bio'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


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
