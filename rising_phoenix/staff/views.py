from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
# from django.contrib.admin.views.decorators import staff_member_required
from account.models import Profile, ArtisanProfile
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages


# Create your views here.


def staff_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('main:home_view')
        return view_func(request, *args, **kwargs)
    return wrapper



@staff_required
def staff_dashboard_view(request: HttpRequest):
    profiles = Profile.objects.select_related('user').order_by('-created_at')
    artisan_profiles = ArtisanProfile.objects.select_related('user').order_by('-created_at')
 
    context = {
        'profiles': profiles,
        'artisan_profiles': artisan_profiles,
        'artisan_requests': artisan_profiles.filter(is_verified=False, is_banned=False),
 
        'total_users': profiles.count(),
        'banned_users': profiles.filter(is_banned=True).count(),
        'total_artisans': artisan_profiles.count(),
        'verified_artisans': artisan_profiles.filter(is_verified=True).count(),
        'featured_artisans': artisan_profiles.filter(is_featured=True).count(),
        'banned_artisans': artisan_profiles.filter(is_banned=True).count(),
    }
    return render(request, 'staff/staff_dashboard.html', context)
 

@staff_required
@require_POST
def ban_user_view(request: HttpRequest, user_id: int):
    profile = get_object_or_404(Profile, user__id=user_id)
 
    if profile.is_banned:
        # Unban
        profile.is_banned = False
        profile.ban_reason = ''
        profile.user.is_active = True
        profile.user.save()
        profile.save()
        messages.success(request, f'{profile.user.username} has been unbanned.')
    else:
        # Ban
        ban_reason = request.POST.get('ban_reason', '').strip()
        profile.is_banned = True
        profile.ban_reason = ban_reason
        profile.user.is_active = False
        profile.user.save()
        profile.save()
        messages.warning(request, f'{profile.user.username} has been banned.')
 
    return redirect('staff:staff_dashboard_view')
 
#same thing but for artisans
@staff_required
@require_POST
def ban_artisan_view(request: HttpRequest, user_id: int):
    artisan = get_object_or_404(ArtisanProfile, user__id=user_id)
 
    if artisan.is_banned:
        artisan.is_banned = False
        artisan.ban_reason = ''
        artisan.user.is_active = True
        artisan.user.save()
        artisan.save()
        messages.success(request, f'{artisan.user.username} has been unbanned.')
    else:
        ban_reason = request.POST.get('ban_reason', '').strip()
        artisan.is_banned = True
        artisan.ban_reason = ban_reason
        artisan.user.is_active = False
        artisan.user.save()
        artisan.save()
        messages.warning(request, f'{artisan.user.username} has been banned.')
 
    return redirect('staff:staff_dashboard_view')
 
 
@staff_required
@require_POST
def feature_artisan_view(request: HttpRequest, user_id: int):
    artisan = get_object_or_404(ArtisanProfile, user__id=user_id)
    artisan.is_featured = not artisan.is_featured
    artisan.save()
 
    state = 'featured' if artisan.is_featured else 'unfeatured'
    messages.success(request, f'{artisan.user.username} has been {state}.')
 
    return redirect('staff:staff_dashboard_view')

@staff_required
@require_POST
def verify_artisan_view(request: HttpRequest, user_id: int):
    artisan = get_object_or_404(ArtisanProfile, user__id=user_id)
    artisan.is_verified = not artisan.is_verified
    artisan.save()
 
    state = 'verified' if artisan.is_verified else 'not verified'
    messages.success(request, f'{artisan.user.username} has been {state}.')
 
    return redirect('staff:staff_dashboard_view')

