from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from account.models import ArtisanProfile
from .models import WorkshopProfile
from .forms import WorkshopProfileForm


def is_artisan(user):
    """Check if user is an artisan."""
    return user.groups.filter(name='artisan').exists()


@login_required(login_url='account:login_view')
@user_passes_test(is_artisan, login_url='main:home_view')
def create_workshop_view(request):
    """Create or edit workshop profile for artisan."""
    try:
        artisan_profile = ArtisanProfile.objects.get(user=request.user)
    except ArtisanProfile.DoesNotExist:
        messages.error(request, "You must have an artisan profile to create a workshop.")
        return redirect('main:home_view')
    
    # Check if workshop already exists
    try:
        workshop = WorkshopProfile.objects.get(artisan=artisan_profile)
    except WorkshopProfile.DoesNotExist:
        workshop = None
    
    if request.method == 'POST':
        form = WorkshopProfileForm(request.POST, request.FILES, instance=workshop)
        if form.is_valid():
            with transaction.atomic():
                workshop_profile = form.save(commit=False)
                if not workshop:
                    workshop_profile.artisan = artisan_profile
                workshop_profile.save()
                messages.success(request, "Workshop profile saved successfully!")
                return redirect('workshop:workshop_detail_view', artisan_id=artisan_profile.user.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = WorkshopProfileForm(instance=workshop)
    
    context = {
        'form': form,
        'is_edit': workshop is not None,
        'workshop': workshop,
    }
    return render(request, 'workshop/create_workshop.html', context)


def workshop_detail_view(request, artisan_id):
    """View public workshop profile."""
    try:
        artisan_profile = ArtisanProfile.objects.get(user_id=artisan_id)
        workshop = WorkshopProfile.objects.get(artisan=artisan_profile)
    except ArtisanProfile.DoesNotExist:
        messages.error(request, "Artisan profile not found.")
        return redirect('main:home_view')
    except WorkshopProfile.DoesNotExist:
        messages.error(request, "Workshop profile not found. The artisan hasn't created a workshop yet.")
        return redirect('main:home_view')
    
    context = {
        'workshop': workshop,
        'artisan': artisan_profile,
    }
    return render(request, 'workshop/workshop_detail.html', context)

# Create your views here.
