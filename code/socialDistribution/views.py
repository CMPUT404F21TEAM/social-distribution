from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def home(request):
    return render(request, 'home/index.html')

def authors(request):
    return render(request, 'authors/index.html')

def create(request):
    return render(request, 'create/index.html')

def post(request):
    return render(request, 'post/index.html')

def profile(request):
    return render(request, 'profile/index.html')

def register(request):
    return render(request, 'register/index.html')

def user(request):
    return render(request, 'user/index.html')
