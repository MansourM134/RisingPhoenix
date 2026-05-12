from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required
def dashboard_view(request: HttpRequest):

    if not request.user.is_staff:
        return redirect('main:home_view')
    

    return render(request, "staff/dashboard.html")