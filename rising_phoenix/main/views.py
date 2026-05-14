from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from workshop.models import Category
from django.db.models import Q


# Create your views here.

def home_view(request:HttpRequest):

    return render(request,'main/index.html')


@login_required(login_url='account:login_view')
def dashboard_view(request: HttpRequest):
    return render(request, 'main/dashboard.html')

def browse_view(request: HttpRequest):
    artisans = User.objects.filter(
        groups__name='artisan',
        artisanprofile__workshop_profile__is_published=True
    ).select_related(
        'artisanprofile',
        'artisanprofile__workshop_profile'
    ).prefetch_related(
        'artisanprofile__workshop_profile__categories'
    ).distinct()

    category_id = request.GET.get('category')
    city = request.GET.get('city')
    q = request.GET.get('q')
    sort = request.GET.get('sort')

    if category_id:
        artisans = artisans.filter(
            artisanprofile__workshop_profile__categories__id=category_id
        )

    if city:
        artisans = artisans.filter(
            artisanprofile__workshop_profile__location__icontains=city
        )

    if q:
        artisans = artisans.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(artisanprofile__bio__icontains=q) |
            Q(artisanprofile__workshop_profile__workshop_name__icontains=q) |
            Q(artisanprofile__workshop_profile__tagline__icontains=q) |
            Q(artisanprofile__workshop_profile__description__icontains=q) |
            Q(artisanprofile__workshop_profile__services__icontains=q) |
            Q(artisanprofile__workshop_profile__location__icontains=q) |
            Q(artisanprofile__workshop_profile__categories__name__icontains=q)
        ).distinct()

    sort_map = {
        'newest': '-artisanprofile__workshop_profile__created_at',
        'oldest': 'artisanprofile__workshop_profile__created_at',
        'name_az': 'first_name',
        'name_za': '-first_name',
        'workshop_az': 'artisanprofile__workshop_profile__workshop_name',
        'workshop_za': '-artisanprofile__workshop_profile__workshop_name',
        'city_az': 'artisanprofile__workshop_profile__location',
        'city_za': '-artisanprofile__workshop_profile__location',
    }

    if sort in sort_map:
        artisans = artisans.order_by(sort_map[sort]).distinct()
    else:
        sort = 'newest'
        artisans = artisans.order_by('-artisanprofile__workshop_profile__created_at').distinct()

    categories = Category.objects.all().order_by('name')

    cities = User.objects.filter(
        groups__name='artisan',
        artisanprofile__workshop_profile__is_published=True,
        artisanprofile__workshop_profile__location__isnull=False
    ).exclude(
        artisanprofile__workshop_profile__location=''
    ).values_list(
        'artisanprofile__workshop_profile__location', flat=True
    ).distinct().order_by('artisanprofile__workshop_profile__location')

    context = {
        'artisans': artisans,
        'categories': categories,
        'cities': cities,
        'selected_category': category_id,
        'selected_city': city,
        'search_query': q,
        'selected_sort': sort,
    }
    return render(request, 'main/user_browse.html', context)


