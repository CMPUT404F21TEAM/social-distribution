from django.http.response import *
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout, get_user_model

from .forms import CreateUserForm, PostForm
from .decorators import allowedUsers, unauthenticated_user
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.urls import reverse
from .models import *
from datetime import datetime
from .utility import make_request
import base64
import json

REQUIRE_SIGNUP_APPROVAL = False
''' 
    sign up approval not required by default, should turn on in prod. 
    if time permits store this in database and allow change from admin dashboard.
'''


def index(request):
    """
        Redirect User on visiting /
    """
    if request.user.is_authenticated:
        author_id = get_object_or_404(LocalAuthor, user=request.user).id
        return redirect('socialDistribution:home')
    else:
        return redirect('socialDistribution:login')


@unauthenticated_user
def loginPage(request):
    """
        Logs in a user and redirects to Home page
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        User = get_user_model()

        # check if user is active
        try:
            user = User.objects.get(username=username)
        except Exception:
            messages.info(request, "Login Failed. Please try again.")
            return render(request, 'user/login.html')

        if REQUIRE_SIGNUP_APPROVAL and not user.is_active:
            # user inactive
            messages.info(request, "Your account is currently pending approval. Please check back later.")
        else:
            # user active, proceed to authentication
            user = authenticate(request, username=username, password=password)

            try:
                author_id = LocalAuthor.objects.get(user=user).id

                if user is not None:
                    login(request, user)
                    return redirect('socialDistribution:home')
                else:
                    raise KeyError

            except (KeyError, LocalAuthor.DoesNotExist):
                messages.info(request, "Username or Password is incorrect.")

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
                display_name = form.cleaned_data.get('display_name')
                github_url = form.cleaned_data.get('github_url', '')
                profile_image_url = form.cleaned_data.get('profile_image_url', '')

                # check github url
                if (github_url and not github_url.startswith('https://github.com/')):
                    context = {'form': form}
                    form.errors['github_url'] = 'Invalid github url, must be of format: https://github.com/username'
                    return render(request, 'user/register.html', context)

                user = form.save()

                if REQUIRE_SIGNUP_APPROVAL:
                    # admin must approve user from console
                    user.is_active = False

                user.save()

                # add user to author group by default
                group, created = Group.objects.get_or_create(name="author")
                user.groups.add(group)
                author = LocalAuthor.objects.create(
                    user=user,
                    username=username,
                    displayName=display_name,
                    githubUrl=github_url,
                    profileImageUrl=profile_image_url
                )
                Inbox.objects.create(author=author)
            except:
                return HttpResponse("Sign up failed. Internal Server Error. Please Try again.", status=500)

            if REQUIRE_SIGNUP_APPROVAL:
                messages.success(request, f'Account creation request sent to admin for {username}.')
            else:
                messages.success(request, f'Account created for {username}.')

            # On successful sign up request, redirect to login page
            return redirect('socialDistribution:login')

    context = {'form': form}
    return render(request, 'user/register.html', context)


def logoutUser(request):
    """
        Logoust out a user and redirects to login page
    """
    logout(request)
    return redirect('socialDistribution:login')


def home(request):
    """ Renders an author's homepage.

    Display posts sent to the feed of the author that is logged in. The feed will include public 
    posts of local authors, public posts of followed authors, and friends posts of friends.
    """

    author = get_object_or_404(LocalAuthor, user=request.user)

    # get all local public posts
    posts = Post.objects.listed().get_public()

    # get all posts created by author
    my_posts = author.posts.listed()
    posts = posts.union(my_posts)

    # get all friend posts from authors friends
    # this should probably just get from recieved_posts (TODO)
    for other in author.followers.all():
        if author.is_friends_with(other):
            friend_posts = other.posts.listed().get_friend()
            posts = posts.union(friend_posts)

    context = {
        'author': author,
        'modal_type': 'post',
        'latest_posts': posts.chronological(),
        'error': False,
        'error_msg': ""
    }

    return render(request, 'home/index.html', context)


def friend_request(request, author_id, action):
    """
        Displays an author's friend requests 
    """
    author = get_object_or_404(LocalAuthor, pk=author_id)
    curr_user = LocalAuthor.objects.get(user=request.user)

    if request.method == 'POST':
        if action not in ['accept', 'decline']:
            return HttpResponseNotFound()

        elif curr_user.id != author.id and curr_user.inbox.has_req_from(author) \
                and not curr_user.has_follower(author):
            curr_user.inbox.follow_requests.remove(author)
            if action == 'accept':
                curr_user.followers.add(author)
        else:
            messages.info(request, f'Couldn\'t {action} request')

    return redirect('socialDistribution:inbox')


def befriend(request, author_id):
    """
        User can send an author a follow request
    """
    if request.method == 'POST':
        author = get_object_or_404(LocalAuthor, pk=author_id)
        curr_user = LocalAuthor.objects.get(user=request.user)

        if author.has_follower(curr_user):
            messages.info(request, f'Already following {author.displayName}')

        if author.inbox.has_req_from(curr_user):
            messages.info(request, f'Follow request to {author.displayName} is pending')

        if author.id != curr_user.id:
            # send follow request
            author.inbox.follow_requests.add(curr_user)

    return redirect('socialDistribution:author', author_id)


def un_befriend(request, author_id):
    """
        User can unfriend an author
    """
    if request.method == 'POST':
        author = get_object_or_404(LocalAuthor, pk=author_id)
        curr_user = LocalAuthor.objects.get(user=request.user)

        if author.has_follower(curr_user):
            author.followers.remove(curr_user)
        else:
            messages.info(f'Couldn\'t un-befriend {author.displayName}')

    return redirect('socialDistribution:author', author_id)


def authors(request):
    """
        Displays all authors
    """
    args = {}

    # demonstration purposes: Authors on remote server
    remote_authors = [
        {
            "data": {
                "id": 16000,
                "username": "johnd",
                "displayName": "John Doe",
                "profileImageUrl": "https://media-exp1.licdn.com/dms/image/C4E03AQEgrX3MR7UULQ/profile-displayphoto-shrink_200_200/0/1614384030904?e=1640822400&v=beta&t=vVdjlx5NgDHfpo-QHx7TMlFHpmwCaQi4vAW6viWjiYA",
                "post__count": 0,
            },
            "type": "Remote"
        },
        {
            "data": {
                "id": 15000,
                "username": "janed",
                "displayName": "Hane Doe",
                "profileImageUrl": "https://media-exp1.licdn.com/dms/image/C4D03AQFD4cImNWN_1A/profile-displayphoto-shrink_200_200/0/1620746712768?e=1640822400&v=beta&t=ItUGhKqEncBHOtBNlP1o3uZWRECUSAjQ0s3PZauSb0o",
                "post__count": 0
            },
            "type": "Remote"
        }
    ]

    # Django Software Foundation, "Generating aggregates for each item in a QuerySet", 2021-10-13
    # https://docs.djangoproject.com/en/3.2/topics/db/aggregation/#generating-aggregates-for-each-item-in-a-queryset
    authors = LocalAuthor.objects.annotate(
        posts__count=Count("posts", filter=Q(posts__visibility=Post.PUBLIC)))
    local_authors = [{
        "data": author,
        "type": "Local"
    } for author in authors]

    args["authors"] = local_authors + remote_authors
    return render(request, 'author/index.html', args)


def author(request, author_id):
    """ Display author's public profile and any posts created by the author that the current 
        user is premitted to view.
    """

    curr_user = LocalAuthor.objects.get(user=request.user)
    author = get_object_or_404(LocalAuthor, pk=author_id)

    # TODO: Should become an API request since won't know if author is local/remote

    if author.is_friends_with(curr_user):
        posts = author.posts.listed().get_friend()
    else:
        posts = author.posts.listed().get_public()

    context = {
        'author': author,
        'author_type': 'Local',
        'curr_user': curr_user,
        'author_posts': posts
    }

    return render(request, 'author/detail.html', context)


def create(request):
    return render(request, 'create/index.html')


def posts(request, author_id):
    """
        Allows user to create a post. The newly created post will also be rendered. 
    """
    author = get_object_or_404(LocalAuthor, pk=author_id)
    user_id = LocalAuthor.objects.get(user=request.user).id

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=user_id)
        if form.is_valid():
            bin_content = form.cleaned_data.get('content_media')
            if bin_content is not None:
                content_media = base64.b64encode(bin_content.read())
            else:
                content_media = None

            pub_date = datetime.now()

            try:
                post = Post.objects.create(
                    author_id=author_id,  # temporary
                    title=form.cleaned_data.get('title'),
                    source=request.build_absolute_uri(request.path),  # will need to fix when moved to api
                    origin=request.build_absolute_uri(request.path),  # will need to fix when moved to api
                    description=form.cleaned_data.get('description'),
                    content_text=form.cleaned_data.get('content_text'),
                    visibility=form.cleaned_data.get('visibility'),
                    unlisted=form.cleaned_data.get('unlisted'),
                    content_media=content_media,
                    pub_date=pub_date,
                    count=0
                )

                if form.cleaned_data.get('visibility') == Post.PRIVATE:
                    recipients = form.cleaned_data.get('post_recipients')
                    for recipient in recipients:
                        recipient.inbox.add_post(post)

                categories = form.cleaned_data.get('categories')
                if categories is not None:
                    categories = categories.split()

                    """
                    This implementation makes category names case-insensitive.
                    This makes handling Category objects cleaner, albeit slightly more
                    involved.
                    """
                    for category in categories:
                        category_obj, created = Category.objects.get_or_create(
                            category__iexact=category, 
                            defaults={'category': category}
                        )
                        post.categories.add(category_obj)

            except ValidationError:
                messages.info(request, 'Unable to create new post.')

    # if using view name, app_name: must prefix the view name
    # In this case, app_name is socialDistribution
    return redirect('socialDistribution:home')


def editPost(request, id):
    """
        Edits an existing post
    """
    author = LocalAuthor.objects.get(user=request.user)
    post = Post.objects.get(id=id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=author.id)
        if form.is_valid():
            bin_content = form.cleaned_data.get('content_media')
            if bin_content is not None:
                content_media = base64.b64encode(bin_content.read())
            else:
                content_media = post.content_media

            try:
                post.title = form.cleaned_data.get('title')
                post.source = request.build_absolute_uri(request.path)    # will need to fix when moved to api
                post.origin = request.build_absolute_uri(request.path)    # will need to fix when moved to api
                post.description = form.cleaned_data.get('description')
                post.content_text = form.cleaned_data.get('content_text')
                post.visibility = form.cleaned_data.get('visibility')
                post.unlisted = form.cleaned_data.get('unlisted')
                post.content_media = content_media

                categories = form.cleaned_data.get('categories')

                if categories is not None:
                    categories = categories.split()
                    categories_to_remove = [ cat.category for cat in post.categories.all()]

                    """
                    This implementation makes category names case-insensitive.
                    This makes handling Category objects cleaner, albeit slightly more
                    involved.
                    """
                    for category in categories:
                        category_obj, created = Category.objects.get_or_create(
                            category__iexact=category,
                            defaults={'category': category}
                        )
                        post.categories.add(category_obj)
                        
                        while category_obj.category in categories_to_remove:
                            categories_to_remove.remove(category_obj.category)     # don't remove this category

                    for category in categories_to_remove:
                        post.categories.get(category=category).delete()

                post.save()

            except ValidationError:
                messages.info(request, 'Unable to edit post.')

    # if using view name, app_name: must prefix the view name
    # In this case, app_name is socialDistribution
    return redirect('socialDistribution:home')

# https://www.youtube.com/watch?v=VoWw1Y5qqt8 - Abhishek Verma


def likePost(request, id):
    """
        Like a specific post
    """
    post = get_object_or_404(Post, id=id)
    author = LocalAuthor.objects.get(user=request.user)
    post = get_object_or_404(Post, id=id)
    host = request.get_host()
    if request.method == 'POST':
        # create like object
        like = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": f"{author.username} Likes your post",
            "type": "like",
            "author": author.as_json(),
            "object": f"http://{host}/author/{post.author.id}/posts/{id}"
        }
    # redirect request to remote/local api
    make_request('POST', f'http://{host}/api/author/{post.author.id}/inbox/', json.dumps(like))
    prev_page = request.META['HTTP_REFERER']

    if prev_page is None:
        return redirect('socialDistribution:home')
    else:
        # prev_page -> url to inbox at the moment
        # will have to edit this if other endpoints require args
        return redirect(prev_page)


def commentPost(request, id):
    '''
        Render Post and comments
    '''
    post = get_object_or_404(Post, id=id)
    author = get_object_or_404(LocalAuthor, user=request.user)

    try:
        comments = Comment.objects.filter(post=post).order_by('-pub_date')
    except Exception:
        return HttpResponseServerError()

    context = {
        'author': author,
        'author_type': 'Local',
        'modal_type': 'post',
        'post': post,
        'comments': comments
    }

    return render(request, 'posts/comments.html', context)

def likeComment(request, id):
    '''
        Likes a comment
    '''

    comment = get_object_or_404(Comment, id = id)
    author = get_object_or_404(LocalAuthor, user=request.user)

    host = request.get_host()
    prev_page = request.META['HTTP_REFERER']

    if request.method == 'POST':
    # create like object
        like =  {
        "@context": "https://www.w3.org/ns/activitystreams",
        "summary": f"{author.username} Likes your comment",         
        "type": "like",
        "author":author.as_json(),
        "object":f"http://{host}/author/{comment.author.id}/posts/{comment.post.id}/comments/{id}"
        }  

    # redirect request to remote/local api
    make_request('POST', f'http://{host}/api/author/{comment.author.id}/inbox/', json.dumps(like))

    if prev_page is None:
        return redirect('socialDistribution:home')
    else:
        return redirect(prev_page)


def deletePost(request, id):
    """
        Deletes a post
    """
    # move functionality to API
    post = get_object_or_404(Post, id=id)
    author = LocalAuthor.objects.get(user=request.user)
    if post.author == author:
        post.delete()
    return redirect('socialDistribution:home')


def profile(request):
    '''
        Render user profile
    '''
    author = get_object_or_404(LocalAuthor, user=request.user)
    djangoUser = get_object_or_404(get_user_model(), username=request.user)

    # add missing information to author
    author.email = djangoUser.email

    return render(request, 'user/profile.html', {'author': author})


def user(request):
    return render(request, 'user/index.html')


def inbox(request):
    """
        Renders info in a user's inbox
    """
    author = LocalAuthor.objects.get(user=request.user)
    follow_requests = author.inbox.follow_requests.all()
    posts = author.inbox.posts.all()
    context = {
        'author': author,
        'follow_requests': follow_requests,
        'posts': posts
    }

    return render(request, 'author/inbox.html', context)
