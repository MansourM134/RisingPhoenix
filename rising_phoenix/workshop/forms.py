from django import forms
from .models import WorkshopProfile, PortfolioImage


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if data in self.empty_values:
            if self.required:
                raise forms.ValidationError(self.error_messages['required'], code='required')
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned_files = []
        for item in data:
            cleaned_files.append(super().clean(item, initial))
        return cleaned_files


class WorkshopProfileForm(forms.ModelForm):
    class Meta:
        model = WorkshopProfile
        fields = [
            'workshop_name',
            'tagline',
            'description',
            'services',
            'categories',
            'location',
            'phone',
            'cover_image',
            'is_published',
        ]
        widgets = {
            'workshop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Workshop name'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short tagline'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your workshop'}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List your services'}),
            'categories': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City or area'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PortfolioImageForm(forms.Form):
    images = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True, 'accept': 'image/*'}),
        label='Portfolio Images',
    )
    caption = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional caption'}),
    )
    is_pinned = forms.BooleanField(
        required=False,
        label='Pin these images to the portfolio',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
