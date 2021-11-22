from django.http.response import *
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.urls import reverse
from .forms import CreateUserForm, PostForm

import base64
import pyperclip

import socialDistribution.requests as api_requests
from cmput404.constants import API_PREFIX
from api.models import Node
from .models import *
from .forms import CreateUserForm, PostForm
from .decorators import unauthenticated_user
from PIL import Image
from io import BytesIO

from .dispatchers import dispatch_post, dispatch_follow_request
from .github_activity.github_activity import pull_github_events

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

def unlisted_post_image(request, post_id):
    """
        Return the embedded image (if any) of the unlisted post
    """
    
    if request.method == 'GET':
        post = get_object_or_404(LocalPost, pk=int(post_id))
        user_author = get_object_or_404(LocalAuthor, user=request.user)

        # post must be visible
        if not post.is_public() or post.author.id != user_author.id:
            return HttpResponseForbidden()

        accepted_types = request.headers['Accept']

        if 'image' in accepted_types:
            if post.is_image_post() and post.unlisted:
                accepted_types = accepted_types.split(',')
                for mime_type in accepted_types:
                    format = mime_type.split('/')[-1]
                    format = format.split(';')[0]

                    # Save post image as webp into a byte stream (BytesIO)
                    # The markdown parser uses webp to display embedded images
                    if format.lower() == 'webp':
                        image_binary = base64.b64decode(post.decoded_content)
                        img = Image.open(BytesIO(image_binary))
                        webp_bytes_arr = BytesIO()
                        img.save(webp_bytes_arr, 'webp')
                        webp_img = webp_bytes_arr.getvalue()
                        
                        response = HttpResponse()
                        response.write(webp_img)
                        response['Content-Type'] = 'image/webp'
                        return response

                return HttpResponse(status_code=415)    # unsupported media type

            else:
                return HttpResponseNotFound('Post image not found')
        else:
            return HttpResponse(status_code=415)    # unsupported media type

    return HttpResponseBadRequest()


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
    for other in author.get_followers():
        if author.has_friend(other):
            # can only get local posts if local author
            try:
                local_other = LocalAuthor.objects.get(id=other.id)
                friend_posts = local_other.posts.listed().get_friend()
                posts = posts.union(friend_posts)
            except LocalAuthor.DoesNotExist:
                pass

    github_events = None
    if author.githubUrl:
        github_user = author.githubUrl.strip('/').split('/')[-1]
        github_events = pull_github_events(github_user)

        if github_events is None:
            messages.info(request, "An error occurred while fetching github events")

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
        requestee = get_object_or_404(Author, pk=author_id)
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


    return redirect('socialDistribution:authors')


def un_befriend(request, author_id):
    """ Handles a POST request to unfollow an author.

        Parameters:
        - request (HttpRequest): the HTTP request
        - author_id (string): the ID of the Author to follow
    """

    # THIS DOES NOT RIGHT NOW
    # STILL BASED ON OLD LOCALAUTHOR METHOD

    if request.method == 'POST':
        author = get_object_or_404(LocalAuthor, pk=author_id)
        curr_user = LocalAuthor.objects.get(user=request.user)

        if author.has_follower(curr_user):
            author.follows.filter(actor=curr_user).delete()
        else:
            messages.info(request, f'Couldn\'t un-befriend {author.displayName}')

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

    remote_authors = []

    # get remote authors
    for node in Node.objects.all():
        # ignore current host
        if node.host == request.META['HTTP_HOST']:
            continue 

        # get request for authors
        try:
            try:
                res = api_requests.get(f'http://{node.host}/api/authors/')

            except Exception as error:
                # if remote server unavailable continue
                continue

            # prepare remote data
            for remote_author in res['items']:
                author, created = Author.objects.get_or_create(
                        url=remote_author['id']
                    )

                # add Local database id to remote author
                remote_author['local_id'] = author.id
                
                remote_authors.append({
                    "data": remote_author,
                    'type': "Remote"
                })

        except Exception as error:
            print(error)

    args["authors"] = local_authors + remote_authors
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

def unlisted_posts(request, author_id):
    """ Display an author's unlisted posts 
    """

    curr_user = LocalAuthor.objects.get(user=request.user)
    author = get_object_or_404(LocalAuthor, pk=author_id)

    # TODO: Should become an API request (same as /author/<author-id>) since won't know if author is local/remote

    posts = author.posts.unlisted()

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
    user_id = LocalAuthor.objects.get(user=request.user).id

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user_id=user_id)
        if form.is_valid():
            content, content_type = form.get_content_and_type()
                
            # Will do some more refactoring to remove code duplication soon
            
            try:
                # create the post
                new_post = LocalPost(
                    author_id=author_id,  # temporary
                    title=form.cleaned_data.get('title'),
                    description=form.cleaned_data.get('description'),
                    content_type=content_type,
                    content=content,
                    visibility=form.cleaned_data.get('visibility'),
                    unlisted=form.cleaned_data.get('unlisted'),
                )
                new_post.save()

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
                        new_post.categories.add(category_obj)

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
def share_post(request, id):
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

def copy_link(request, id):
    """
        Allows user to copy a post's link
    """

    # TODO:
    #     * make copy notification prettier 
    #     * redirect to the same page after copying link to unlisted post 
    #     * add pyperclip to requirements.txt

    post = LocalPost.objects.get(id=id)
    link = post.get_shareable_link()
    pyperclip.copy(link)

    return redirect('socialDistribution:home')
    return render(request, 'author/copy_link.html', {'post': post})


def edit_post(request, id):
    """
        Edits an existing post
    """
    author = LocalAuthor.objects.get(user=request.user)
    post = LocalPost.objects.get(id=id)
    if not post.is_public():
        return HttpResponseBadRequest("Only public posts are editable")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user_id=author.id)
        if form.is_valid():
            content, content_type = form.get_content_and_type()

            # Will do some more refactoring to remove code duplication soon

            try:
                post.title = form.cleaned_data.get('title')
                post.description = form.cleaned_data.get('description')
                post.visibility = form.cleaned_data.get('visibility')
                post.unlisted = form.cleaned_data.get('unlisted')
                post.content_type = content_type
                post.content = content

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
                        category_obj = Category.objects.get(category=category)
                        post.categories.remove(category_obj)

                post.save()

            except ValidationError:
                messages.info(request, 'Unable to edit post.')

    # if using view name, app_name: must prefix the view name
    # In this case, app_name is socialDistribution
    return redirect('socialDistribution:home')

# https://www.youtube.com/watch?v=VoWw1Y5qqt8 - Abhishek Verma


def like_post(request, id, post_host):
    """
        Like a specific post
    """
    if post_host == 'remote':
        post = get_object_or_404(InboxPost, id=id)
        request_url = post.author.strip('/') + '/inbox'
        obj = post.public_id.strip('/')
    else:
        post = get_object_or_404(LocalPost, id=id)
        host = request.get_host()
        request_url = f'http://{host}/{API_PREFIX}/author/{post.author.id}/inbox'
        obj = f'http://{host}/{API_PREFIX}/author/{post.author.id}/posts/{id}'

    author = LocalAuthor.objects.get(user=request.user)
    prev_page = request.META['HTTP_REFERER']
    
    if request.method == 'POST':
        # create like object
        like = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": f"{author.username} Likes your post",
            "type": "like",
            "author": author.as_json(),
            "object": obj
        }

        # redirect request to remote/local api
        status_code, response_data = api_requests.post(url=request_url, data=like, sendBasicAuthHeader=True)

        if status_code >= 400:
            messages.error(request, 'An error occurred while liking post')

    prev_page = request.META['HTTP_REFERER']

    if prev_page is None:
        return redirect('socialDistribution:home')
    else:
        # prev_page -> url to inbox at the moment
        # will have to edit this if other endpoints require args
        return redirect(prev_page)


def comment_post(request, id):
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


def like_comment(request, id):
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
    request_url = f'http://{host}/api/author/{comment.author.id}/inbox/'
    api_requests.post(url=request_url, data=like, sendBasicAuthHeader=True)

    if prev_page is None:
        return redirect('socialDistribution:home')
    else:
        return redirect(prev_page)


def delete_post(request, id):
    """
        Deletes a post
    """
    # move functionality to API
    post = get_object_or_404(LocalPost, id=id)
    author = LocalAuthor.objects.get(user=request.user)
    author_id = author.id
    
    if post.author == author:
        post.delete()
    
    # remain on unlisted page if the deleted post is unlisted 
    if post.unlisted is True:
        unlisted_posts(request, author_id)

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
    posts = author.inbox_posts.all().order_by('-published')
    context = {
        'author': author,
        'follow_requests': follow_requests,
        'posts': posts
    }

    return render(request, 'author/inbox.html', context)
