from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required

# Create your views here.

def home_view(request:HttpRequest):

    return render(request,'main/index.html')


@login_required(login_url='account:login_view')
def dashboard_view(request: HttpRequest):
    return render(request, 'main/dashboard.html')
