from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from workshop.models import Category
from workshop.models import WorkshopProfile
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from request.models import Request
from proposal.models import Proposal
from notification.models import Notification
from message.models import Conversation, Message


# Create your views here.

def home_view(request:HttpRequest):
    categories = Category.objects.order_by('name')[:6]

    is_artisan_user = (
        request.user.is_authenticated
        and hasattr(request.user, 'artisanprofile')
    )

    top_rated_workshops = None
    latest_requests = None

    if is_artisan_user:
        latest_requests = (
            Request.objects
            .filter(status__in=[Request.Status.OPEN, Request.Status.IN_REVIEW])
            .select_related('requester', 'category')
            .prefetch_related('images')
            .order_by('-created_at')[:8]
        )
    else:
        top_rated_workshops = (
            WorkshopProfile.objects
            .filter(is_published=True)
            .select_related('artisan__user')
            .prefetch_related('categories')
            .annotate(avg_rating=Avg('artisan__user__reviews_received__rating'))
            .order_by('-avg_rating', '-created_at')[:8]
        )

    context = {
        'home_categories': categories,
        'home_feed_type': 'requests' if is_artisan_user else 'top_artisans',
        'top_rated_workshops': top_rated_workshops,
        'latest_requests': latest_requests,
    }

    return render(request, 'main/index.html', context)


@login_required(login_url='account:login_view')
def dashboard_view(request: HttpRequest):
    context = {}

    is_artisan_user = hasattr(request.user, 'artisanprofile')
    is_requester = not is_artisan_user and not request.user.is_staff

    if is_requester:
        my_requests_qs = Request.objects.filter(requester=request.user)
        status_filter = request.GET.get('request_status', 'all')

        filtered_requests_qs = my_requests_qs
        if status_filter in {
            Request.Status.OPEN,
            Request.Status.IN_REVIEW,
            Request.Status.CLOSED,
            Request.Status.TIME_ENDED,
        }:
            filtered_requests_qs = filtered_requests_qs.filter(status=status_filter)

        my_requests_recent = (
            filtered_requests_qs
            .select_related('category')
            .annotate(proposal_count=Count('proposals'))
            .order_by('-created_at')[:5]
        )

        proposals_qs = Proposal.objects.filter(request__requester=request.user)
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        notifications_recent = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]

        requester_conversations = Conversation.objects.filter(requester=request.user)
        unread_messages_count = Message.objects.filter(
            conversation__in=requester_conversations,
            is_read=False,
        ).exclude(sender=request.user).count()

        context.update({
            'request_status': status_filter,
            'my_requests_total': my_requests_qs.count(),
            'requests_open_total': my_requests_qs.filter(status=Request.Status.OPEN).count(),
            'requests_in_review_total': my_requests_qs.filter(status=Request.Status.IN_REVIEW).count(),
            'requests_closed_total': my_requests_qs.filter(status=Request.Status.CLOSED).count(),
            'proposals_total': proposals_qs.count(),
            'proposals_pending_total': proposals_qs.filter(status=Proposal.Status.PENDING).count(),
            'unread_notifications_count': unread_notifications_count,
            'notifications_recent': notifications_recent,
            'unread_messages_count': unread_messages_count,
            'active_conversations_count': requester_conversations.filter(is_active=True).count(),
            'my_requests_recent': my_requests_recent,
        })

    return render(request, 'main/dashboard.html', context)

def browse_view(request: HttpRequest):
    artisans = User.objects.filter(
        groups__name='artisan',
        artisanprofile__workshop_profile__is_published=True
    ).select_related(
        'artisanprofile',
        'artisanprofile__workshop_profile'
    ).prefetch_related(
        'artisanprofile__workshop_profile__categories'
    ).annotate(
        avg_rating=Avg('reviews_received__rating')
    ).distinct()

    category_id = request.GET.get('category')
    city = request.GET.get('city')
    q = request.GET.get('q')
    sort = request.GET.get('sort')
    rating_min = request.GET.get('rating_min')
    rating_max = request.GET.get('rating_max')
    use_rating = request.GET.get('use_rating') == '1'
    verified_only = request.GET.get('verified') == '1'

    if category_id:
        artisans = artisans.filter(
            artisanprofile__workshop_profile__categories__id=category_id
        )

    if city:
        artisans = artisans.filter(
            artisanprofile__workshop_profile__location__icontains=city
        )

    if verified_only:
        artisans = artisans.filter(
            artisanprofile__is_verified=True
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

    min_value = None
    max_value = None

    try:
        min_value = float(rating_min) if rating_min else 1.0
    except ValueError:
        min_value = 1.0
        rating_min = '1'

    try:
        max_value = float(rating_max) if rating_max else 5.0
    except ValueError:
        max_value = 5.0
        rating_max = '5'

    if min_value > max_value:
        min_value, max_value = max_value, min_value
        rating_min, rating_max = str(min_value), str(max_value)

    if use_rating:
        artisans = artisans.filter(
            avg_rating__gte=min_value,
            avg_rating__lte=max_value
        )

    sort_map = {
        'newest': '-artisanprofile__workshop_profile__created_at',
        'oldest': 'artisanprofile__workshop_profile__created_at',
        'name_az': 'first_name',
        'name_za': '-first_name',
        'workshop_az': 'artisanprofile__workshop_profile__workshop_name',
        'workshop_za': '-artisanprofile__workshop_profile__workshop_name',
        'city_az': 'artisanprofile__workshop_profile__location',
        'city_za': '-artisanprofile__workshop_profile__location',
        'rating_high': '-avg_rating',
        'rating_low': 'avg_rating',
    }

    if sort in sort_map:
        artisans = artisans.order_by(
            sort_map[sort],
            '-artisanprofile__workshop_profile__created_at'
        ).distinct()
    else:
        sort = 'newest'
        artisans = artisans.order_by(
            '-artisanprofile__workshop_profile__created_at'
        ).distinct()

    paginator = Paginator(artisans, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    context = {
        'artisans': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'cities': cities,
        'selected_category': category_id,
        'selected_city': city,
        'search_query': q,
        'selected_sort': sort,
        'selected_rating_min': str(min_value),
        'selected_rating_max': str(max_value),
        'use_rating': use_rating,
        'verified_only': verified_only,
        'query_params': query_params.urlencode(),
    }
    return render(request, 'main/user_browse.html', context)



def about_us_view(request: HttpRequest):
    return render(request, 'main/about_us.html')


def members_view(request: HttpRequest):
    return render(request, 'main/members.html')


def terms_view(request: HttpRequest):
    return render(request, 'main/terms.html')


