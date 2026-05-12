from django import forms
from django.contrib.auth.models import User
from .models import Profile, ArtisanProfile
from django.contrib.auth.forms import UserCreationForm

    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone','bio','avatar']

class ArtisanProfileForm(forms.ModelForm):
    class Meta:
        model = ArtisanProfile
        fields = ['phone','bio','avatar']

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")

        return email
