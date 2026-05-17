from django.shortcuts import get_object_or_404, render, redirect
from .forms import CustomUserCreationForm, ProfileForm, ArtisanProfileForm, CustomUserUpdateForm, ReviewForm
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ArtisanProfile, Review
from django.contrib.auth.models import Group, User
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
import datetime
import calendar
from twilio.rest import Client
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from notification.utils import send_welcome_email, send_artisan_welcome_email
# Create your views here.

def signup_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST,request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = new_user
                profile.save()
                messages.success(request, "You have been register")
            send_welcome_email(new_user)
            return redirect('account:login_view')
        else:
            print(user_form.errors)
            messages.error(request, "something goes Wrong")
            return render(request, 'account/signup.html', {'user_form': user_form, 'profile_form': profile_form})
        
    return render(request, 'account/signup.html')

def artisan_signup_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ArtisanProfileForm(request.POST,request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save()
                artisan_group, create = Group.objects.get_or_create(name='artisan')
                new_user.groups.add(artisan_group)
                profile = profile_form.save(commit=False)
                profile.user = new_user
                profile.save()
                messages.success(request, "You have been register")
            send_artisan_welcome_email(new_user)
            return redirect('account:login_view')
        else:
            print(user_form.errors)
            messages.error(request, "something goes Wrong")
            return render(request, 'account/artisan_signup.html', {'user_form': user_form, 'profile_form': profile_form})
        
    return render(request, 'account/artisan_signup.html')

        


def login_view(request:HttpRequest):
    if request.user.is_authenticated:
        return redirect('main:home_view')

    if request.method == 'POST':
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])

        if user:
            login(request,user)
            messages.success(request, "Logged in successufly")
            #redirect to the staff id the user is staff
            if user.is_staff:
                return redirect('staff:staff_dashboard_view')
            if user.groups.filter(name='artisan').exists():
                print('artisan')
                return redirect('account:artisan_dashboard_view')
            return redirect('main:home_view')
        else:
            messages.error(request, "Your Username or Password is wrong, try again")
            
    
    return render(request, 'account/login.html')

def logout_view(request:HttpRequest):
    logout(request)
    #response = redirect(request.GET.get("next"))
    #return response
    return redirect('main:home_view')


def is_artisan(user):
    """Check if user is an artisan."""
    return user.groups.filter(name='artisan').exists()
@login_required(login_url='account:login_view')
@user_passes_test(is_artisan, login_url='main:home_view')
def artisan_dashboard_view(request: HttpRequest):
    """Artisan dashboard showing stats, orders, and workshop info."""

    try:
        artisan_profile = ArtisanProfile.objects.get(
            user=request.user
        )
    except ArtisanProfile.DoesNotExist:
        messages.error(
            request,
            "You don't have an artisan profile."
        )
        return redirect('main:home_view')

    workshop = getattr(
        artisan_profile,
        'workshop_profile',
        None
    )

    now = timezone.now()
    year = now.year
    month = now.month

    from progress.models import Contract, ProgressUpdate
    from request.models import Request as UserRequest
    from proposal.models import Proposal


    # ==========================
    # Earnings last 6 months
    # ==========================

    earnings_6months = []

    for n in range(5, -1, -1):

        total_months = (
            (year * 12 + month - 1)
            - n
        )

        y = total_months // 12
        m = total_months % 12 + 1

        total = (
            Contract.objects.filter(
                proposal__artisan=request.user,
                status=Contract.Status.COMPLETED,
                completed_at__year=y,
                completed_at__month=m
            )
            .aggregate(
                total=Sum(
                    'proposal__price'
                )
            )['total']
            or 0
        )

        earnings_6months.append({
            'label': f"{calendar.month_abbr[m]} {y}",
            'total': float(total)
        })


    earnings_this_month = (
        earnings_6months[-1]['total']
        if earnings_6months
        else 0
    )

    earnings_last_month = (
        earnings_6months[-2]['total']
        if len(earnings_6months) > 1
        else 0
    )

    try:

        if earnings_last_month == 0:

            earnings_growth_percent = (
                100
                if earnings_this_month > 0
                else 0
            )

        else:

            earnings_growth_percent = int(
                (
                    (
                        earnings_this_month
                        - earnings_last_month
                    )
                    /
                    float(
                        earnings_last_month
                    )
                ) * 100
            )

    except Exception:

        earnings_growth_percent = 0


    # ==========================
    # Active Orders
    # ==========================

    active_contracts_qs = (
        Contract.objects.filter(
            proposal__artisan=request.user,
            status=Contract.Status.IN_PROGRESS
        )
        .select_related(
            'proposal',
            'proposal__request'
        )
    )

    active_orders = active_contracts_qs.count()


    # ==========================
    # Completed Orders
    # ==========================

    completed_orders = (
        Contract.objects.filter(
            proposal__artisan=request.user,
            status=Contract.Status.COMPLETED
        )
        .select_related(
            'proposal',
            'proposal__request'
        )
        .order_by(
            '-completed_at'
        )
    )


    # ==========================
    # Awaiting photos
    # ==========================

    photos_awaiting = (
        ProgressUpdate.objects.filter(
            contract__proposal__artisan=request.user
        )
        .annotate(
            img_count=Count(
                'images'
            )
        )
        .filter(
            img_count=0
        )
        .count()
    )


    # ==========================
    # Proposals
    # ==========================

    my_proposals_qs = (
        Proposal.objects.filter(
            artisan=request.user
        )
        .select_related(
            'request'
        )
    )

    my_proposals = my_proposals_qs.count()

    my_proposals_pending = (
        my_proposals_qs.filter(
            status=Proposal.Status.PENDING
        ).count()
    )


    # ==========================
    # Matching Requests
    # ==========================

    requests_matching_count = 0
    requests_matching_list = []

    if workshop and hasattr(
        workshop,
        'categories'
    ):

        cats = workshop.categories.all()

        if cats.exists():

            reqs_qs = (
                UserRequest.objects.filter(
                    status=UserRequest.Status.OPEN,
                    category__in=cats
                )
                .distinct()
            )

            requests_matching_count = reqs_qs.count()

            requests_matching_list = list(
                reqs_qs.order_by(
                    '-created_at'
                )[:5]
            )


    stats = {

        'earnings_6months': earnings_6months,
        'earnings_this_month': earnings_this_month,
        'earnings_last_month': earnings_last_month,
        'earnings_growth_percent': earnings_growth_percent,
        'active_orders': active_orders,
        'photos_awaiting': photos_awaiting,
        'rating': artisan_profile.average_rating,
        'rating_reviews': request.user.reviews_received.count(),
        'open_requests': requests_matching_count,

    }


    context = {

        'artisan': artisan_profile,
        'workshop': workshop,
        'stats': stats,

        'active_contracts': active_contracts_qs[:5],

        'completed_orders': completed_orders[:10],

        'my_proposals': my_proposals_qs[:5],

        'requests_matching_list': requests_matching_list,

    }

    return render(
        request,
        'account/artisan_dashboard.html',
        context
    )

def profile_view(request:HttpRequest, user_name):
    user = get_object_or_404(User, username = user_name)
    if user.groups.filter(name='artisan').exists():
        messages.warning(request, 'Your are not allowed')
        return redirect('main:home_view')
    user_profile = user.profile
    user_reviews = user.reviews_received.all()
    avg_rating = user_reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
    return render(request,'account/profile.html',{'user_profile': user_profile, 'user_reviews': user_reviews, 'avg_rating': avg_rating})

def update_profile_view(request:HttpRequest,user_name):
    if user_name != request.user.username:
        messages.warning(request,'Your are not allowed')
        return redirect('main:home_view')
    user = User.objects.get(username = user_name)
    if user.groups.filter(name='artisan').exists():
        messages.warning(request, 'Your are not allowed')
        redirect('main:home_view')
    user_profile = user.profile
    if request.method == 'POST':
        user_form = CustomUserUpdateForm(request.POST,instance=request.user)
        profile_form = ProfileForm(request.POST,request.FILES,instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()

                profile = profile_form.save(commit=False)

                if 'phone' in profile_form.changed_data:
                    profile.is_phone_verified = False

                profile.save()

                messages.success(request, "Your profile has been updated")

            return redirect('account:profile_view', user_name=request.user.username)
        else:
            print(user_form.errors)
            messages.error(request, "something goes Wrong")
            return render(request, 'account/update_profile.html', {'user_form': user_form, 'user_profile': user_profile, 'profile_form': profile_form})
    return render(request, 'account/update_profile.html',{'user_profile': user_profile})


def verify_phone_view(request: HttpRequest, user_name):
    if user_name != request.user.username:
        messages.warning(request, 'You are not allowed')
        return redirect('main:home_view')

    user = get_object_or_404(User, username=user_name)
    user_profile = user.profile

    if not user_profile.phone:
        messages.error(request, 'Please add your phone number first.')
        return redirect('account:update_profile_view', user_name=user.username)

    if request.method == 'POST':
        code = request.POST.get('code')

        if not code:
            messages.error(request, 'Please enter the verification code.')
            return render(request, 'account/verify_phone.html', {
                'user_profile': user_profile
            })

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            verification_check = client.verify.v2.services(
                settings.TWILIO_VERIFY_SERVICE_SID
            ).verification_checks.create(
                to=str(user_profile.phone),
                code=code
            )

            if verification_check.status == 'approved':
                user_profile.is_phone_verified = True
                user_profile.save()
                messages.success(request, 'Your phone number has been verified successfully.')
                return redirect('account:profile_view', user_name=user.username)
            else:
                messages.error(request, 'Invalid verification code.')
        except Exception as e:
            messages.error(request, 'Verification failed. Please try again.')

    return render(request, 'account/verified_phone.html', {
        'user_profile': user_profile
    })


def send_phone_verification_view(request: HttpRequest, user_name):
    if user_name != request.user.username:
        messages.warning(request, 'You are not allowed')
        return redirect('main:home_view')

    user = get_object_or_404(User, username=user_name)
    user_profile = user.profile

    if not user_profile.phone:
        messages.error(request, 'Please add your phone number first.')
        return redirect('account:update_profile_view', user_name=user.username)

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=str(user_profile.phone),
            channel='sms'
        )
        messages.success(request, 'Verification code sent to your phone.')
        return redirect('account:verify_phone_view', user_name=user.username)
    except Exception as e:
        print(e)
        messages.error(request, 'Failed to send verification code.')
        return redirect('account:profile_view', user_name=user.username)


@login_required(login_url='account:login_view')
def submit_review_view(request: HttpRequest, contract_id):
    from progress.models import Contract
    contract = get_object_or_404(
        Contract.objects.select_related('proposal__artisan', 'proposal__request__requester'),
        id=contract_id,
    )

    if request.user != contract.requester:
        messages.warning(request, 'You are not allowed to review this project.')
        return redirect('main:home_view')

    if not contract.is_completed:
        messages.warning(request, 'You can only leave a review after the project is completed.')
        return redirect('progress:contract_detail_view', contract_id=contract_id)

    request_obj = contract.proposal.request
    if hasattr(request_obj, 'review'):
        messages.warning(request, 'You have already submitted a review for this project.')
        return redirect('workshop:workshop_detail_view', artisan_id=contract.artisan.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.request = request_obj
            review.reviews_given = request.user
            review.reviews_received = contract.artisan
            review.save()
            messages.success(request, 'Your review has been submitted. Thank you!')
            return redirect('workshop:workshop_detail_view', artisan_id=contract.artisan.id)
    else:
        form = ReviewForm()

    return render(request, 'account/submit_review.html', {
        'form': form,
        'contract': contract,
    })


@login_required(login_url='account:login_view')
def review_history_view(request: HttpRequest):
    reviews = request.user.reviews_given.select_related(
        'request', 'reviews_received'
    ).order_by('-created_at')
    return render(request, 'account/review_history.html', {'reviews': reviews})


def password_reset_view(request: HttpRequest):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,
                email_template_name='account/password_reset_email.html',
                subject_template_name='account/password_reset_subject.txt',
            )
            messages.success(request, "Password reset email sent.")
            return redirect('account:password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'account/password_reset.html', {'form': form})


