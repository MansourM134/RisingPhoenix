import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.conf import settings

logger = logging.getLogger(__name__)

from .forms import RequestForm
from .models import Request


def request_list_view(request: HttpRequest):
	project_requests = Request.objects.select_related('requester').all()
	return render(request, 'request/request_list.html', {'project_requests': project_requests})



def request_create_view(request: HttpRequest):
	if request.method == 'POST':
		form = RequestForm(request.POST, request.FILES)
		if form.is_valid():
			request_instance = form.save(commit=False)
			request_instance.requester = request.user
			request_instance.save()
			messages.success(request, 'Your request has been posted.')
			return redirect('request:request_list_view')
	else:
		form = RequestForm()

	return render(request, 'request/request_form.html', {'form': form})


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
		from openai import OpenAI
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



def check_ai_config_view(request: HttpRequest):
	"""Debug endpoint to verify AI configuration is loaded."""
	api_key = getattr(settings, 'OPENAI_API_KEY', '').strip()
	model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
	
	key_status = 'loaded' if api_key else 'NOT FOUND'
	key_preview = f"{api_key[:10]}...{api_key[-10:]}" if api_key else 'N/A'
	
	return JsonResponse({
		'openai_api_key': key_status,
		'key_preview': key_preview,
		'openai_model': model,
	})
