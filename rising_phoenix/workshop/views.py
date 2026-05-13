from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from account.models import ArtisanProfile
from .models import WorkshopProfile, PortfolioImage
from .forms import WorkshopProfileForm, PortfolioImageForm


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
                # Save ManyToMany fields (categories)
                form.save_m2m()
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

    can_edit_portfolio = request.user.is_authenticated and request.user == artisan_profile.user

    if request.method == 'POST' and can_edit_portfolio:
        # Handle caption update
        if 'caption' in request.POST and 'portfolio_image_id' in request.POST:
            image_id = request.POST.get('portfolio_image_id')
            caption = request.POST.get('caption', '').strip()
            portfolio_image = workshop.portfolio_images.filter(id=image_id).first()
            if portfolio_image:
                portfolio_image.caption = caption
                portfolio_image.save(update_fields=['caption'])
                messages.success(request, "Portfolio description updated successfully.")
            else:
                messages.error(request, "Portfolio image not found.")
            return redirect('workshop:workshop_detail_view', artisan_id=artisan_id)
        # Handle image delete
        elif 'delete_portfolio_image_id' in request.POST:
            image_id = request.POST.get('delete_portfolio_image_id')
            portfolio_image = workshop.portfolio_images.filter(id=image_id).first()
            if portfolio_image:
                portfolio_image.delete()
                messages.success(request, "Portfolio image deleted successfully.")
            else:
                messages.error(request, "Portfolio image not found.")
            return redirect('workshop:workshop_detail_view', artisan_id=artisan_id)
    
    context = {
        'workshop': workshop,
        'artisan': artisan_profile,
        'portfolio_images': workshop.portfolio_images.all(),
        'can_edit_portfolio': can_edit_portfolio,
    }
    return render(request, 'workshop/workshop_detail.html', context)


@login_required(login_url='account:login_view')
@user_passes_test(is_artisan, login_url='main:home_view')
def upload_portfolio_view(request):
    """Upload portfolio images for an artisan workshop."""
    try:
        artisan_profile = ArtisanProfile.objects.get(user=request.user)
        workshop = WorkshopProfile.objects.get(artisan=artisan_profile)
    except ArtisanProfile.DoesNotExist:
        messages.error(request, "You must have an artisan profile to upload portfolio images.")
        return redirect('main:home_view')
    except WorkshopProfile.DoesNotExist:
        messages.error(request, "You must create a workshop profile first.")
        return redirect('workshop:create_workshop_view')

    if request.method == 'POST':
        if 'toggle_pin_image_id' in request.POST:
            image_id = request.POST.get('toggle_pin_image_id')
            portfolio_image = workshop.portfolio_images.filter(id=image_id).first()
            if portfolio_image:
                portfolio_image.is_pinned = not portfolio_image.is_pinned
                portfolio_image.save(update_fields=['is_pinned'])
                messages.success(request, f"Image {'pinned' if portfolio_image.is_pinned else 'unpinned'} successfully.")
            else:
                messages.error(request, "Portfolio image not found.")
            return redirect('workshop:upload_portfolio_view')

        form = PortfolioImageForm(request.POST, request.FILES)

        if form.is_valid():
            images = form.cleaned_data['images']
            caption = form.cleaned_data.get('caption', '')
            is_pinned = form.cleaned_data.get('is_pinned', False)

            if not images:
                messages.error(request, "Please select at least one image to upload.")
            else:
                with transaction.atomic():
                    for image in images:
                        PortfolioImage.objects.create(
                            workshop=workshop,
                            image=image,
                            caption=caption,
                            is_pinned=is_pinned,
                        )

                messages.success(request, f"{len(images)} portfolio image(s) uploaded successfully.")
                return redirect('workshop:upload_portfolio_view')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PortfolioImageForm()

    context = {
        'form': form,
        'workshop': workshop,
        'portfolio_images': workshop.portfolio_images.all(),
    }
    return render(request, 'workshop/upload_portfolio.html', context)

# Create your views here.
