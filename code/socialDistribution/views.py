from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout

from .forms import CreateUserForm
from .decorators import allowedUsers, unauthenticated_user
from django.core.exceptions import ValidationError
from .models import *
from datetime import datetime
# Create your views here.

def index(request):
    return HttpResponse("Hello, world. You're at the Login/SignUp Page.")

@unauthenticated_user
def loginPage(request):
    """
        Logs in a user and redirects to Home page
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, "Username or Passoword is incorrect.")

    return render(request, 'user/login.html')

@unauthenticated_user
def register(request):
    """
        Registers a new user and redirects to Login page
    """
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            try:
                # extract form data
                username = form.cleaned_data.get('username')
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                github_url = request.POST.get('github_url', '')
                full_name = f"{first_name} {last_name}"

                # check github url
                if (github_url and not github_url.startswith('https://github.com/')):
                    context = { 'form': form }
                    messages.info(request, 'Invalid github url, must be of format: https://github.com/username')
                    return render(request, 'user/register.html', context)

                user = form.save()

                # add user to author group by default
                group, created = Group.objects.get_or_create(name="author")
                user.groups.add(group)
                Author.objects.create(
                    user=user,
                    username=username,
                    displayName=full_name,
                    githubUrl=github_url
                )
            except:
                return HttpResponse("Sign up failed. Internal Server Error. Please Try again.", status=500)


            messages.success(request, f'Account created for {username}')

            return redirect('login')

    context = { 'form': form }
    return render(request, 'user/register.html', context)

def logoutUser(request): 
    """
        Logoust out a user and redirects to login page
    """
    logout(request)
    return redirect('login')

def home(request):
    return render(request, 'home/index.html')

@allowedUsers(allowed_roles=['author']) # just for demonstration
def authors(request):
    return render(request, 'authors/index.html')

def create(request):
    return render(request, 'create/index.html')

def post(request):
    context = {}
    context['modal_type'] = 'post'

    if request.method == 'POST':
        title = request.POST.get('title')
        source = request.POST.get('source')
        origin = request.POST.get('origin')
        categories = request.POST.get('categories').split()
        img = request.POST.get('img')
        description = request.POST.get('description')
        content = request.POST.get('content')
        visibility = request.POST.get('visibility')
        is_unlisted = request.POST.get('unlisted')
        pub_date = datetime.now()

        if is_unlisted is None:
            is_unlisted = False
        else:
            is_unlisted = True

        if visibility == '1':
            visibility = Post.PostVisibility.FRIENDS
        else:
            visibility = Post.PostVisibility.PUBLIC
        
        # temporarily set to zero; will need to fix that soon!
        page_size = 0
        count = 0

        try:
            post = Post.objects.create(
                author_id=Author.objects.get(displayName='someauthor').id,  # temporary
                title=title, 
                source=source, 
                description=description,
                content_text=content,
                visibility=visibility,
                pub_date=pub_date,
                unlisted=is_unlisted,
                page_size=page_size,
                count=count
            )

            for category in categories:
                Category.objects.create(category=category, post=post)

        except ValidationError:
            context['message'] = "Something went wrong! Couldn't add post"
    
    latest_posts = Post.objects.order_by('-pub_date')[:5]
    context['latest_posts'] = latest_posts
    return render(request, 'post/index.html', context)

def profile(request):
    return render(request, 'profile/index.html')

def user(request):
    return render(request, 'user/index.html')
