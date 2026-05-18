from django import forms

from rising_phoenix.moderation import text_is_clean
from .models import WorkshopProfile, PortfolioImage, WorkshopDetail


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


    def clean_workshop_name(self):
        value = self.cleaned_data.get('workshop_name', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your workshop name contains inappropriate language. Please revise it.')
        return value

    def clean_tagline(self):
        value = self.cleaned_data.get('tagline', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your tagline contains inappropriate language. Please revise it.')
        return value

    def clean_description(self):
        value = self.cleaned_data.get('description', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your description contains inappropriate language. Please revise it.')
        return value

    def clean_services(self):
        value = self.cleaned_data.get('services', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your services description contains inappropriate language. Please revise it.')
        return value


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


class CompletedProjectForm(forms.ModelForm):
    request = forms.ModelChoiceField(queryset=None, required=False, label='Related request')

    class Meta:
        model = __import__('workshop.models', fromlist=['CompletedProject']).CompletedProject
        fields = ['title', 'description', 'date_completed', 'main_image', 'is_featured', 'is_published', 'request']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_completed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        value = self.cleaned_data.get('title', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your project title contains inappropriate language. Please revise it.')
        return value

    def clean_description(self):
        value = self.cleaned_data.get('description', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your project description contains inappropriate language. Please revise it.')
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # lazy import to avoid circular import
        from request.models import Request
        self.fields['request'].queryset = Request.objects.none()


class ProjectImageUploadForm(forms.Form):
    images = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True, 'accept': 'image/*'}),
        label='Project Images',
    )
    caption = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional caption for these images'}),
    )
    is_before = forms.BooleanField(
        required=False,
        label='Mark these images as "before"'
    )


class WorkshopDetailForm(forms.ModelForm):
    class Meta:
        model = WorkshopDetail
        fields = [
            'typical_turnaround',
            'ships_ksa',
            'protection_text',
        ]
        widgets = {
            'typical_turnaround': forms.TextInput(attrs={'class': 'form-control'}),
            'ships_ksa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'protection_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
