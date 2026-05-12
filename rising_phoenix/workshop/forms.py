from django import forms
from .models import WorkshopProfile


class WorkshopProfileForm(forms.ModelForm):
    class Meta:
        model = WorkshopProfile
        fields = [
            'workshop_name',
            'tagline',
            'description',
            'services',
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
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City or area'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
