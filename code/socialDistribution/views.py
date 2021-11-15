from logging import error
from django.db.models.fields.related import OneToOneField
from django.http.response import *
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone

from .forms import CreateUserForm, PostForm
from .decorators import allowedUsers, unauthenticated_user
from .github_activity.github_activity import pull_github_events
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.urls import reverse
import base64
import json

from .forms import CreateUserForm, PostForm
from .decorators import allowedUsers, unauthenticated_user
from .models import *
from .utility import make_request

from .dispatchers import dispatch_post, dispatch_follow_request

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
    posts = LocalPost.objects.listed().get_public()

    # get all posts created by author
    my_posts = author.posts.listed()
    posts = posts.union(my_posts)

    # get all friend posts from authors friends
    # this should probably just get from recieved_posts (TODO)
    # for other in author.followers.all():
    #     if author.is_friends_with(other):
    #         friend_posts = other.posts.listed().get_friend()
    #         posts = posts.union(friend_posts)

    github_events = None
    if author.githubUrl:
        github_user = author.githubUrl.strip('/').split('/')[-1]
        github_events = pull_github_events(github_user)

        if github_events is None:
            messages.info("An error occurred while fetching github events")

    context = {
        'author': author,
        'github_events': github_events,
        'modal_type': 'post',
        'latest_posts': posts.chronological(),
        'error': False,
        'error_msg': ""
    }

    return render(request, 'home/index.html', context)


def friend_request(request, author_id, action):
    """ Handles POST request to resolve a pending follow request.

        Parameters:
        - request (HttpRequest): the HTTP request
        - author_id (string): The ID of the author who created the friend request
        - action (string): The resolution of the friend request. Must be "accept" or "decline"

    """

    if action not in ['accept', 'decline']:
        return HttpResponseNotFound()

    if request.method == 'POST':
        # get models
        requestee = get_object_or_404(LocalAuthor, pk=author_id)
        curr_user = LocalAuthor.objects.get(user=request.user)

        # process action
        if curr_user.has_follow_request(requestee):
            is_accept = action == 'accept'
            curr_user.handle_follow_request(requestee, is_accept)


    return redirect('socialDistribution:inbox')


def befriend(request, author_id):
    """ Handles POST request to create a follow request.

        Parameters:
        - request (HttpRequest): the HTTP request
        - author_id (string): the ID of the Author to follow
    """

    if request.method == 'POST':
        object = get_object_or_404(Author, id=author_id)
        actor = LocalAuthor.objects.get(user=request.user)

        if object.id != actor.id:
            # send follow request
            dispatch_follow_request(actor, object)

    return redirect('socialDistribution:author', author_id)


def un_befriend(request, author_id):
    """ Handles a POST request to unfollow an author.

        Parameters:
        - request (HttpRequest): the HTTP request
        - author_id (string): the ID of the Author to follow
    """

    # FIX THIS

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

    # Django Software Foundation, "Generating aggregates for each item in a QuerySet", 2021-10-13
    # https://docs.djangoproject.com/en/3.2/topics/db/aggregation/#generating-aggregates-for-each-item-in-a-queryset
    authors = LocalAuthor.objects.annotate(posts__count=Count(
        "posts", filter=Q(posts__visibility=LocalPost.Visibility.PUBLIC)))
    local_authors = [{
        "data": author,
        "type": "Local"
    } for author in authors]

    args["authors"] = local_authors
    return render(request, 'author/index.html', args)


def author(request, author_id):
    """ Display author's public profile and any posts created by the author that the current 
        user is premitted to view.
    """

    curr_user = LocalAuthor.objects.get(user=request.user)
    author = get_object_or_404(LocalAuthor, pk=author_id)

    # TODO: Should become an API request since won't know if author is local/remote

    if curr_user.has_friend(author):
        posts = author.posts.listed().get_friend()
    else:
        posts = author.posts.listed().get_public()

    context = {
        'author': author,
        'author_type': 'Local',
        'curr_user': curr_user,
        'author_posts': posts.chronological()
    }

    return render(request, 'author/detail.html', context)


def create(request):
    return render(request, 'create/index.html')


def posts(request, author_id):
    """ Handles POST request to publish a post.

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

            try:
                # create the post
                new_post = LocalPost(
                    author_id=author_id,  # temporary
                    title=form.cleaned_data.get('title'),
                    description=form.cleaned_data.get('description'),
                    content=form.cleaned_data.get('content_text'),
                    visibility=form.cleaned_data.get('visibility'),
                    unlisted=form.cleaned_data.get('unlisted'),
                    content_media=content_media,
                )
                new_post.save()

                categories = form.cleaned_data.get('categories')
                if categories is not None:
                    categories = categories.split()

                    for category in categories:
                        Category.objects.create(category=category, post=new_post)

                # get recipients for a private post
                if form.cleaned_data.get('visibility') == LocalPost.Visibility.PRIVATE:
                    recipients = form.cleaned_data.get('post_recipients')
                else:
                    recipients = None

                # send to other authors
                post = LocalPost.objects.get(id=new_post.id)
                dispatch_post(post, recipients)

            except ValidationError:
                messages.info(request, 'Unable to create new post.')

    # if using view name, app_name: must prefix the view name
    # In this case, app_name is socialDistribution
    return redirect('socialDistribution:home')

# https://books.agiliq.com/projects/django-orm-cookbook/en/latest/copy.html - How to copy or clone an existing model object
def sharePost(request, id):
    """
        Allows user to share a post.
        The user that is sharing is the owner of the shared post
        Public posts are shared to everyone
        Friend posts are shared to friends
    """
    author = LocalAuthor.objects.get(user=request.user)
    post = LocalPost.objects.get(id=id)
    
    if not post.is_public() and not post.is_friends():
        return redirect('socialDistribution:home')
    
    oldSource = post.get_id()
    
    post.pk = None # duplicate the post
    post.author = author
    post.published = timezone.now()
    post.source = oldSource
    post.save()
    
    
    dispatch_post(post, [])
    
    return redirect('socialDistribution:home')


def editPost(request, id):
    """
        Edits an existing post
    """
    author = LocalAuthor.objects.get(user=request.user).id
    post = LocalPost.objects.get(id=id)
    if not post.is_public():
        return HttpResponseBadRequest("Only public posts are editable")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=author)
        if form.is_valid():
            bin_content = form.cleaned_data.get('content_media')
            if bin_content is not None:
                content_media = base64.b64encode(bin_content.read())
            else:
                content_media = post.content_media

            try:
                post.title = form.cleaned_data.get('title')
                post.description = form.cleaned_data.get('description')
                post.content = form.cleaned_data.get('content_text')
                post.visibility = form.cleaned_data.get('visibility')
                post.unlisted = form.cleaned_data.get('unlisted')
                post.content_media = content_media

                categories = form.cleaned_data.get('categories').split()
                previousCategories = Category.objects.filter(post=post)
                previousCategoriesNames = [
                    cat.category for cat in previousCategories]

                # Create new categories
                for category in categories:
                    if category in previousCategoriesNames:
                        previousCategoriesNames.remove(category)
                    else:
                        Category.objects.create(category=category, post=post)

                # Remove old categories that were deleted
                for category in previousCategoriesNames:
                    Category.objects.get(category=category, post=post).delete()

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
    post = get_object_or_404(LocalPost, id=id)
    author = LocalAuthor.objects.get(user=request.user)
    post = get_object_or_404(LocalPost, id=id)
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
    post = get_object_or_404(LocalPost, id=id)
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

    comment = get_object_or_404(Comment, id=id)
    author = get_object_or_404(LocalAuthor, user=request.user)

    host = request.get_host()
    prev_page = request.META['HTTP_REFERER']

    if request.method == 'POST':
        # create like object
        like = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": f"{author.username} Likes your comment",
            "type": "like",
            "author": author.as_json(),
            "object": f"http://{host}/author/{comment.author.id}/posts/{comment.post.id}/comments/{id}"
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
    post = get_object_or_404(LocalPost, id=id)
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
    follow_requests = author.follow_requests.all()
    posts = author.inbox_posts.all()
    context = {
        'author': author,
        'follow_requests': follow_requests,
        'posts': posts
    }

    return render(request, 'author/inbox.html', context)
