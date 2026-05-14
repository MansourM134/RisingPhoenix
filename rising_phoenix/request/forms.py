from django import forms

from .models import Request


class RequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = self.fields['category'].queryset.order_by('name')

    class Meta:
        model = Request
        fields = ['title', 'description', 'budget_min', 'budget_max', 'category', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'request-input'}),
            'description': forms.Textarea(attrs={'class': 'request-textarea'}),
            'category': forms.Select(attrs={'class': 'request-select'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'request-input'}),
            'budget_min': forms.NumberInput(attrs={'class': 'request-input', 'placeholder': 'e.g. 500 (optional)', 'min': '0'}),
            'budget_max': forms.NumberInput(attrs={'class': 'request-input', 'placeholder': 'e.g. 2000 (optional)', 'min': '0'}),
        }

    def clean_budget_min(self):
        budget_min = self.cleaned_data.get('budget_min')
        if budget_min is not None and budget_min < 0:
            raise forms.ValidationError('Budget cannot be negative.')
        return budget_min

    def clean_budget_max(self):
        budget_max = self.cleaned_data.get('budget_max')
        if budget_max is not None and budget_max < 0:
            raise forms.ValidationError('Budget cannot be negative.')
        return budget_max

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')

        if budget_min is not None and budget_max is not None and budget_min > budget_max:
            raise forms.ValidationError('Minimum budget cannot be greater than maximum budget.')

        return cleaned_data