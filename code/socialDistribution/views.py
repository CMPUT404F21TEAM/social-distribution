from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def index(request):
    return HttpResponse("Hello, world. You're at the Login/SignUp Page.")

def home(request):
    return render(request, 'home/index.html')

def authors(request):
    # dummy data
    args = {}
    sample_data = [
        {
            "name": "John Doe",
            "type": "Local"
        },
        {
            "name": "Jane Doe",
            "type": "Remote"
        }
    ]

    args["authors"] = sample_data
    return render(request, 'authors/index.html', args)

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
