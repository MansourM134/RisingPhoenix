import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from .forms import RequestForm
from .models import Request, RequestImage
from workshop.models import Category, WorkshopProfile

logger = logging.getLogger(__name__)


def _save_uploaded_request_images(request_instance: Request, request_files):
	for image_file in request_files.getlist('reference_images'):
		try:
			RequestImage.objects.create(request=request_instance, image=image_file)
		except Exception:
			logger.exception('Failed to save uploaded image "%s"', image_file.name)


def _refresh_time_based_statuses():
	today = timezone.localdate()
	Request.objects.filter(
		status__in=[Request.Status.OPEN, Request.Status.IN_REVIEW],
		deadline__isnull=False,
		deadline__lt=today,
	).update(status=Request.Status.TIME_ENDED)


def request_list_view(request: HttpRequest):
	_refresh_time_based_statuses()
	project_requests = Request.objects.select_related('requester', 'category').prefetch_related('images')

	search_query = request.GET.get('q', '').strip()
	category = request.GET.get('category', '').strip()
	status = request.GET.get('status', '').strip()
	sort = request.GET.get('sort', 'newest').strip()

	valid_statuses = {choice[0] for choice in Request.Status.choices}

	if search_query:
		project_requests = project_requests.filter(
			Q(title__icontains=search_query)
			| Q(description__icontains=search_query)
			| Q(category__name__icontains=search_query)
			| Q(requester__username__icontains=search_query)
		)

	if category.isdigit():
		project_requests = project_requests.filter(category_id=int(category))

	if status in valid_statuses:
		project_requests = project_requests.filter(status=status)

	if sort == 'deadline_soon':
		project_requests = project_requests.order_by(F('deadline').asc(nulls_last=True), '-created_at')
	elif sort == 'budget_high':
		project_requests = project_requests.order_by(F('budget_max').desc(nulls_last=True), '-created_at')
	elif sort == 'budget_low':
		project_requests = project_requests.order_by(F('budget_min').asc(nulls_last=True), '-created_at')
	elif sort == 'oldest':
		project_requests = project_requests.order_by('created_at')
	else:
		project_requests = project_requests.order_by('-created_at')

	total_count = project_requests.count()
	paginator = Paginator(project_requests, 9)
	page_obj = paginator.get_page(request.GET.get('page'))

	context = {
		'project_requests': page_obj.object_list,
		'page_obj': page_obj,
		'total_count': total_count,
		'category_choices': Category.objects.order_by('name'),
		'status_choices': Request.Status.choices,
		'current_q': search_query,
		'current_category': category,
		'current_status': status,
		'current_sort': sort,
	}
	return render(request, 'request/request_list.html', context)


def suggested_artisans_view(request: HttpRequest):
	category_id = request.GET.get('category_id', '').strip()
	if not category_id.isdigit():
		return JsonResponse({'artisans': []})

	workshops = (
		WorkshopProfile.objects.select_related('artisan__user')
		.filter(is_published=True, categories__id=int(category_id))
		.distinct()[:6]
	)

	artisans = []
	for workshop in workshops:
		artisans.append(
			{
				'workshop_name': workshop.workshop_name,
				'tagline': workshop.tagline,
				'location': workshop.location,
				'artisan_username': workshop.artisan.user.username,
				'workshop_url': reverse('workshop:workshop_detail_view', args=[workshop.artisan.user_id]),
			}
		)

	return JsonResponse({'artisans': artisans})


def request_detail_view(request: HttpRequest, request_id: int):
	_refresh_time_based_statuses()
	project_request = get_object_or_404(
		Request.objects.select_related('requester', 'category').prefetch_related('images'),
		id=request_id,
	)
	images = list(project_request.images.all())
	return render(request, 'request/request_detail.html', {'project_request': project_request, 'images': images, 'has_images': bool(images)})



@login_required
def request_create_view(request: HttpRequest):
	_refresh_time_based_statuses()
	if request.method == 'POST':
		form = RequestForm(request.POST, request.FILES)
		if form.is_valid():
			request_instance = form.save(commit=False)
			request_instance.requester = request.user
			request_instance.save()
			_save_uploaded_request_images(request_instance, request.FILES)
			messages.success(request, 'Your request has been posted.')
			return redirect('request:request_list_view')
	else:
		form = RequestForm()

	return render(request, 'request/request_form.html', {'form': form, 'edit_mode': False})


@login_required
def request_edit_view(request: HttpRequest, request_id: int):
	_refresh_time_based_statuses()
	request_instance = get_object_or_404(Request.objects.prefetch_related('images'), id=request_id)

	if request_instance.requester_id != request.user.id:
		messages.error(request, 'You can only edit your own requests.')
		return redirect('request:request_list_view')

	if request_instance.status in [Request.Status.CLOSED, Request.Status.TIME_ENDED]:
		messages.warning(request, 'This request is no longer editable.')
		return redirect('request:request_list_view')

	if request.method == 'POST':
		form = RequestForm(request.POST, request.FILES, instance=request_instance)
		if form.is_valid():
			form.save()
			delete_image_ids = request.POST.getlist('delete_image_ids')
			if delete_image_ids:
				request_instance.images.filter(id__in=delete_image_ids).delete()
			_save_uploaded_request_images(request_instance, request.FILES)
			messages.success(request, 'Request updated successfully.')
			return redirect('request:request_edit_view', request_id=request_instance.id)
	else:
		form = RequestForm(instance=request_instance)

	context = {
		'form': form,
		'edit_mode': True,
		'request_instance': request_instance,
		'existing_images': request_instance.images.all(),
	}
	return render(request, 'request/request_form.html', context)


@login_required
@require_POST
def refine_request_view(request: HttpRequest):
	try:
		payload = json.loads(request.body or '{}')
	except json.JSONDecodeError:
		return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

	user_text = (payload.get('text') or '').strip()
	if not user_text:
		return JsonResponse({'error': 'Please provide request text to refine.'}, status=400)

	api_key = getattr(settings, 'OPENAI_API_KEY', '').strip()
	if not api_key:
		logger.warning('OPENAI_API_KEY not configured')
		return JsonResponse({'error': 'AI service is not configured. Add OPENAI_API_KEY in environment settings.'}, status=503)

	try:
		from openai import OpenAI # type: ignore
	except ImportError:
		logger.error('OpenAI package not installed')
		return JsonResponse({'error': 'OpenAI package is not installed. Add it to requirements and install dependencies.'}, status=503)

	model_name = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
	system_prompt = (
		'You are an expert artisan consultant. Rewrite the request as if the requester is speaking in first person. '
		'The response must begin with "I want". Include useful details about materials, dimensions, texture, and finish '
		'when relevant. Keep it under 50 words.'
	)

	try:
		client = OpenAI(api_key=api_key)
		response = client.chat.completions.create(
			model=model_name,
			messages=[
				{'role': 'system', 'content': system_prompt},
				{'role': 'user', 'content': user_text},
			],
			temperature=0.6,
		)
		refined_text = (response.choices[0].message.content or '').strip()
	except Exception as e:
		logger.exception(f'OpenAI API error: {str(e)}')
		error_msg = str(e)[:100]
		return JsonResponse({'error': f'OpenAI error: {error_msg}'}, status=502)

	if not refined_text:
		return JsonResponse({'error': 'AI returned an empty response. Please try again.'}, status=502)

	if not refined_text.lower().startswith('i want'):
		refined_text = f"I want {refined_text.lstrip()}"

	return JsonResponse({'refined_text': refined_text})




