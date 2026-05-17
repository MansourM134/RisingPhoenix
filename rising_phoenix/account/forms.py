from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from rising_phoenix.moderation import image_is_clean, text_is_clean
from .models import Profile, ArtisanProfile, Review


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'avatar']

    def clean_bio(self):
        value = self.cleaned_data.get('bio', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your bio contains inappropriate language. Please revise it.')
        return value

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'chunks') and not image_is_clean(avatar):
            raise forms.ValidationError('Your profile picture contains inappropriate content.')
        return avatar


class ArtisanProfileForm(forms.ModelForm):
    class Meta:
        model = ArtisanProfile
        fields = ['phone', 'bio', 'avatar']

    def clean_bio(self):
        value = self.cleaned_data.get('bio', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your bio contains inappropriate language. Please revise it.')
        return value

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'chunks') and not image_is_clean(avatar):
            raise forms.ValidationError('Your profile picture contains inappropriate content.')
        return avatar


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=True)
    username = forms.CharField(min_length=5, max_length=20)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class CustomUserUpdateForm(forms.ModelForm):
    username = forms.CharField(min_length=5, max_length=20)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=Review.Rate.choices),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }

    def clean_comment(self):
        value = self.cleaned_data.get('comment', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your review contains inappropriate language. Please revise it.')
        return value