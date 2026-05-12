from django import forms

from .models import Request


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['title', 'description', 'reference_image', 'budget_min', 'budget_max', 'category', 'deadline']
        labels = {
            'budget_min': 'Minimum budget (SAR)',
            'budget_max': 'Maximum budget (SAR)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'request-input'}),
            'description': forms.Textarea(attrs={'class': 'request-textarea'}),
            'category': forms.Select(attrs={'class': 'request-select'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'request-input'}),
            'budget_min': forms.NumberInput(attrs={'class': 'request-input', 'placeholder': 'e.g. 500'}),
            'budget_max': forms.NumberInput(attrs={'class': 'request-input', 'placeholder': 'e.g. 2000'}),
            'reference_image': forms.ClearableFileInput(attrs={'class': 'request-file'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')

        if budget_min is not None and budget_max is not None and budget_min > budget_max:
            raise forms.ValidationError('Minimum budget cannot be greater than maximum budget.')

        return cleaned_data