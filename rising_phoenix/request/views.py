from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpRequest

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
