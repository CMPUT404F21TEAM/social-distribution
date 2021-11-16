from django.contrib.auth import get_user_model
from django.http.response import *
from django.http import HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.core import serializers
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from urllib.parse import urlparse
import json
import logging
from datetime import datetime, timezone
import pprint

from cmput404.constants import HOST, API_PREFIX
from socialDistribution.models import *
from .decorators import authenticate_request
from .parsers import url_parser
from .utility import paginate

# References for entire file:
# Django Software Foundation, "Introduction to class-based views", 2021-10-13
# https://docs.djangoproject.com/en/3.2/topics/class-based-views/intro/
# Django Software Foundation, "JsonResponse objects", 2021-10-13
# https://docs.djangoproject.com/en/3.2/ref/request-response/#jsonresponse-objects

# Need to disable CSRF to make POST, PUT, etc requests. Otherwise, your request needs to contain 'X--CSRFToken: blahblah' with a CSRF token.
# If we need CSRF validation in the future, just remove the csrf_exempt decorators.
#
# Martijn ten Hoor, https://stackoverflow.com/users/6945548/martijn-ten-hoor, "How to disable Django's CSRF validation?",
# 2016-10-12, https://stackoverflow.com/a/39993384, CC BY-SA 3.0
#
# Note: @ensure_crsf_cookie will send the token in the response
# Ryan Pergent, https://stackoverflow.com/users/3904557/ryan-pergent, "how do I use ensure_csrf_cookie?",
# 2017-05-30, https://stackoverflow.com/a/43712324, CC BY-SA 3.0

# Django Software Foundation, "Logging", https://docs.djangoproject.com/en/3.2/topics/logging/
logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("Welcome to the Social Distribution API")


@method_decorator(csrf_exempt, name='dispatch')
class AuthorsView(View):

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        """ GET - Retrieve all user profiles 
            'page' is indexed from 1, NOT 0.
            'size' must be greater than 0
        """
        authors = [author.as_json() for author in LocalAuthor.objects.all()]
        page = request.GET.get("page")
        size = request.GET.get("size")
        
        # ensure query params are valid
        if page and size:
            page = int(page)
            size = int(size)
            try:
                if page < 1 or size < 1:
                    return HttpResponseBadRequest("Malformed query: page and size must be > 0")
            except:
                print('hi')
                return HttpResponseBadRequest("Malformed query")
            page -= 1
            # collect authors based on query
            paginated = paginate(authors, size)
            # return the last page if specified page is too large
            if page > len(paginated) - 1:
                authors = paginated[-1]
            else:
                authors = paginate(authors, size)[page]

        response = {
            "type": "authors",
            "items": authors
        }

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class AuthorView(View):

    def get(self, request, author_id):
        """ GET - Retrieve profile of {author_id} """

        author = get_object_or_404(LocalAuthor, pk=author_id)
        response = author.as_json()
        return JsonResponse(response)

    @method_decorator(authenticate_request)
    def post(self, request, author_id):
        """ POST - Update profile of {author_id} """

        # extract post data
        display_name = request.POST.get('display_name')
        github_url = request.POST.get('github_url')
        email = request.POST.get('email')
        profile_image_url = request.POST.get('profile_image_url')

        # check data for empty string
        if (not display_name or not email):
            return HttpResponseBadRequest()

        djangoUser = get_object_or_404(get_user_model(), username=request.user)
        author = get_object_or_404(LocalAuthor, user=request.user)

        try:
            # update author
            author.displayName = display_name
            author.githubUrl = github_url
            author.profileImageUrl = profile_image_url
            author.save()

            # update django user
            djangoUser.email = email
            djangoUser.save()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return redirect('socialDistribution:profile')


@method_decorator(csrf_exempt, name='dispatch')
class FollowersView(View):

    def get(self, request, author_id):
        """ GET - Get a list of authors who are the followers of {author_id} """

        author = get_object_or_404(LocalAuthor, pk=author_id)
        followers = [follower.as_json() for follower in author.followers.all()]

        response = {
            "type": "followers",
            "items": followers
        }

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class LikedView(View):

    def get(self, request, author_id):
        """ GET - Get a list of like objects from {author_id} """
        try:
            author = LocalAuthor.objects.get(id=author_id)
            authorLikedPosts = LocalPost.objects.filter(likes__exact=author)
            host = request.get_host()
            likes = []
            for post in authorLikedPosts:
                like = {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{author.displayName} Likes your post",
                    "type": "like",
                    "author": author.as_json(),
                    "object": f"http://{host}/author/{post.author.id}/posts/{post.id}"
                }
                likes.append(like)

            response = {
                "type:": "liked",
                "items": likes}

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class PostsView(View):

    def get(self, request, author_id):
        # Send all PUBLIC posts
        try:
            # TODO handle pagination
            page = request.GET.get("page")
            size = request.GET.get("size")
            author = get_object_or_404(LocalAuthor, id=author_id)
            posts = LocalPost.objects.listed().get_public().filter(author=author)
        
            jsonPosts = []
            for post in posts:
                jsonPosts.append(post.as_json())

            response = {
                "type": "posts",
                "page": page,
                "size": size,
                "items": jsonPosts
            }

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)

    def post(self, request, author_id):
        return HttpResponse("This is the authors/aid/posts/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class PostView(View):

    def get(self, request, author_id, post_id):
        return HttpResponse("This is the authors/aid/posts/pid/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class PostLikesView(View):

    def get(self, request, author_id, post_id):
        """ GET - Get a list of authors who like {post_id} """
        try:
            post = LocalPost.objects.get(id=post_id)
            authors = [author.as_json() for author in post.likes.all()]

            response = {
                "type:": "likes",
                "items": authors
            }

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class PostCommentsView(View):
    '''
        HANDLE Comment GET and POST
    '''

    def get(self, request, author_id, post_id):
        # Send all comments
        try:
            page = request.GET.get("page")
            size = request.GET.get("size")
            post = get_object_or_404(LocalPost, id=post_id)
            author = get_object_or_404(LocalAuthor, id=author_id)
            # Check if the post author match with author in url
            if post.author.id != author.id:
                return HttpResponseNotFound()

            response = post.comments_as_json

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)

    def post(self, request, author_id, post_id):
        # check if authenticated
        if (not request.user):
            return HttpResponseForbidden()

        comment = request.POST.get('comment')

        # check if empty
        if not len(comment):
            return HttpResponseBadRequest("Comment cannot be empty.")

        pub_date = datetime.now(timezone.utc)

        try:
            author = get_object_or_404(LocalAuthor, pk=author_id)
            post = get_object_or_404(LocalPost, id=post_id)

            comment = Comment.objects.create(
                author=author,
                post=post,
                comment=comment,
                content_type='PL',  # TODO: add content type
                pub_date=pub_date,
            )

        except Exception:
            return HttpResponse('Internal Server Error')

        return redirect('socialDistribution:commentPost', id=post_id)


@method_decorator(csrf_exempt, name='dispatch')
class CommentLikesView(View):

    def get(self, request, author_id, post_id, comment_id):
        return HttpResponse("This is the authors/aid/posts/pid/comments/cid/likes/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class InboxView(View):
    """ This endpoint currently only works for requests from local server.
    """

    @method_decorator(authenticate_request)
    def get(self, request, author_id):
        """ GET - If authenticated, get a list of posts sent to {author_id} """

        return JsonResponse({
            "message": f"This is the inbox for author_id={author_id}. Only author {author_id} can read this."
        })

    # TODO: authenticate user
    def post(self, request, author_id):
        """ POST - Send a post to {author_id}
            - if the type is “post” then add that post to the author’s inbox
            - if the type is “follow” then add that follow is added to the author’s inbox to approve later
            - if the type is “like” then add that like to the author’s inbox    
        """
        data = json.loads(request.body)
        # pprint.pprint(data)
        try:
            if data["type"] == "post":
                # get owner of inbox
                receiving_author = get_object_or_404(LocalAuthor, id=author_id)

                # save the received post as an InboxPost
                received_post, created = InboxPost.objects.get_or_create(
                    public_id=data["id"],
                    defaults={
                        "title": data["title"],
                        "source": data["source"],
                        "origin": data["origin"],
                        "description": data["description"],
                        "content_type": data["contentType"],
                        "content": data["content"],
                        # "categories": data["categories"],
                        "author": data["author"]["id"],
                        "_author_json": data["author"],
                        "published": data["published"],
                        "visibility": data["visibility"],
                        "unlisted": data["unlisted"],
                    }
                )

                # add post to inbox of author
                receiving_author.inbox_posts.add(received_post)

                return HttpResponse(status=200)

            elif data["type"] == "follow":
                # actor requests to follow Object

                actor, obj = data["actor"], data["object"]
                if not url_parser.is_local_url(actor["id"]) or not url_parser.is_local_url(obj["id"]):
                    raise ValueError()

                follower_id = url_parser.parse_author(actor["id"])  # only works for local followers right now
                followee_id = url_parser.parse_author(obj["id"])

                # check if this is the correct endpoint
                if followee_id != author_id:
                    raise ValueError("Object ID does not match inbox ID")

                followee_author = get_object_or_404(LocalAuthor, id=followee_id)

                # add follow request to inbox
                try:
                    follower_author = LocalAuthor.objects.get(id=follower_id)
                    followee_author.follow_requests.add(follower_author)
                except LocalAuthor.DoesNotExist:
                    raise ValueError()

                return HttpResponse(status=200)

            elif data["type"] == "like":
                # extract data from request body
                object_url = urlparse(data['object']).path.strip('/')
                split_url = object_url.split('/')
                object = split_url[-2]
                id = split_url[-1]
                liking_author_url = data["author"]["id"]

                # retrieve author
                liking_author, created = Author.objects.get_or_create(
                    url=liking_author_url
                )

                # check if liking post or comment
                if object == 'comments':
                    context_object = get_object_or_404(Comment, id=id)
                elif (object == 'posts'):
                    context_object = get_object_or_404(LocalPost, id=id)
                else:
                    raise ValueError("Unknown object for like")

                if context_object.likes.filter(author=liking_author).exists():
                    # if like already exists, remove it
                    like = context_object.likes.get(author=liking_author)
                    like.delete()
                else:
                    # create a new like from liking_author on object
                    context_object.likes.create(author=liking_author, object=context_object)

                return HttpResponse(status=200)

            else:
                raise ValueError("Unknown object received by inbox")

        except KeyError as e:
            return HttpResponseBadRequest("JSON body could not be parsed")

        except ValueError as e:
            return JsonResponse({
                "error": e.args[0]
            }, status=400)

        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({
                "error": "Internal Server Error"
            }, status=500)

    def delete(self, request, author_id):
        """ DELETE - Clear the inbox """

        return HttpResponse("Hello")
