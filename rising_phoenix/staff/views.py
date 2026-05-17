from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
# from django.contrib.admin.views.decorators import staff_member_required
from account.models import Profile, ArtisanProfile
from workshop.models import Category, WorkshopProfile
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
import datetime
from .models import Report
from .forms import ReportForm


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
    categories = Category.objects.all()
    
    categories = Category.objects.annotate(
    workshop_count=Count('workshopprofile')
    )
 
    context = {
        'profiles': profiles,
        'artisan_profiles': artisan_profiles,
        'artisan_requests': artisan_profiles.filter(is_verified=False, is_banned=False),
        'categories': categories,
        
        
        'total_users': profiles.count(),
        'banned_users': profiles.filter(is_banned=True).count(),
        'total_artisans': artisan_profiles.count(),
        'verified_artisans': artisan_profiles.filter(is_verified=True).count(),
        'featured_artisans': artisan_profiles.filter(is_featured=True).count(),
        'banned_artisans': artisan_profiles.filter(is_banned=True).count(),
        'pending_reports_count': Report.objects.filter(status=Report.Status.PENDING).count(),
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

@staff_required
@require_POST
def add_category_view(request: HttpRequest):
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    if name:
        Category.objects.create(name=name, description=description)
        messages.success(request, f'Category "{name}" has been added.')
    else:
        messages.error(request, 'Category name cannot be empty.')
    return redirect('staff:staff_dashboard_view')


# ── Report & Flagging ─────────────────────────────────────────────────────────

def _resolve_report_target(content_type, object_id):
    """Return (target_object, field_name) or (None, None) if invalid."""
    from request.models import Request as ItemRequest
    from workshop.models import PortfolioImage
    from account.models import Review
    from message.models import Message
    from django.contrib.auth.models import User

    mapping = {
        Report.ContentType.USER:            (User,          'reported_user'),
        Report.ContentType.REQUEST:         (ItemRequest,   'reported_request'),
        Report.ContentType.PORTFOLIO_IMAGE: (PortfolioImage,'reported_portfolio_image'),
        Report.ContentType.REVIEW:          (Review,        'reported_review'),
        Report.ContentType.MESSAGE:         (Message,       'reported_message'),
    }
    entry = mapping.get(content_type)
    if not entry:
        return None, None
    model_class, field_name = entry
    try:
        obj = model_class.objects.get(pk=object_id)
    except model_class.DoesNotExist:
        return None, None
    return obj, field_name


@login_required
def submit_report_view(request: HttpRequest, content_type: str, object_id: int):
    from urllib.parse import urlparse

    target, field_name = _resolve_report_target(content_type, object_id)
    if target is None:
        messages.error(request, 'The content you are trying to report could not be found.')
        return redirect('main:home_view')

    def get_safe_next(url):
        """Return a safe local path, stripping host if needed. Falls back to '/'."""
        if not url:
            return '/'
        parsed = urlparse(url)
        path = parsed.path or '/'
        return path if path.startswith('/') else '/'

    cutoff = timezone.now() - datetime.timedelta(hours=24)

    if request.method == 'POST':
        next_url = get_safe_next(request.POST.get('next', '/'))

        existing = Report.objects.filter(
            reporter=request.user,
            content_type=content_type,
            created_at__gte=cutoff,
            **{field_name: target},
        ).exists()
        if existing:
            messages.warning(request, 'You have already submitted a report on this content recently. Please wait before reporting again.')
            return redirect(next_url)

        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = content_type
            setattr(report, field_name, target)
            report.save()

            from notification.utils import notify
            from django.contrib.auth.models import User as AuthUser
            for staff_user in AuthUser.objects.filter(is_staff=True):
                notify(
                    recipient=staff_user,
                    notif_type='report_received',
                    title='New report submitted',
                    body=f'{request.user.username} reported a {content_type.replace("_", " ")}.',
                    link='/staff/reports/',
                )

            messages.success(request, 'Your report has been submitted. Our team will review it shortly.')
            return redirect(next_url)
    else:
        next_url = get_safe_next(request.META.get('HTTP_REFERER', '/'))

        existing = Report.objects.filter(
            reporter=request.user,
            content_type=content_type,
            created_at__gte=cutoff,
            **{field_name: target},
        ).exists()
        if existing:
            messages.warning(request, 'You have already submitted a report on this content recently. Please wait before reporting again.')
            return redirect(next_url)

        form = ReportForm()

    return render(request, 'staff/report_form.html', {
        'form': form,
        'content_type': content_type,
        'target': target,
        'next': next_url,
    })


@login_required
def my_reports_view(request: HttpRequest):
    reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
    return render(request, 'staff/my_reports.html', {'reports': reports})


@staff_required
def report_list_view(request: HttpRequest):
    status_filter = request.GET.get('status', Report.Status.PENDING)
    reports = Report.objects.filter(status=status_filter).select_related('reporter').order_by('-created_at')
    return render(request, 'staff/report_list.html', {
        'reports': reports,
        'status_filter': status_filter,
        'status_choices': Report.Status.choices,
    })


@staff_required
@require_POST
def resolve_report_view(request: HttpRequest, report_id: int):
    report = get_object_or_404(Report, pk=report_id)
    action = request.POST.get('action', '')
    resolution_note = request.POST.get('resolution_note', '').strip()

    if action not in (Report.Status.RESOLVED, Report.Status.DISMISSED, Report.Status.REVIEWED):
        messages.error(request, 'Invalid action.')
        return redirect('staff:report_list_view')

    report.status = action
    report.resolution_note = resolution_note
    report.reviewed_by = request.user
    report.reviewed_at = timezone.now()
    report.save()

    # Notify the reporter
    if report.reporter:
        from notification.utils import notify
        status_label = report.get_status_display()
        notify(
            recipient=report.reporter,
            notif_type='report_status_update',
            title=f'Your report has been {status_label.lower()}',
            body=resolution_note or 'The moderation team has reviewed your report.',
            link='/account/my-reports/',
        )

    messages.success(request, f'Report marked as {report.get_status_display()}.')
    return redirect('staff:report_list_view')
