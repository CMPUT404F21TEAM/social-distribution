import base64
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http.response import *
from django.http import HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator

from datetime import datetime, timezone
import json
import logging
import base64

from cmput404.constants import API_BASE
import socialDistribution.requests as api_requests
from socialDistribution.models import *
from .decorators import authenticate_request, validate_node
from .parsers import url_parser
from .utility import getPaginated, makePost
from socialDistribution.utility import add_or_update_author

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
logger = logging.getLogger("api")


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
        logger.info(f"GET /authors API endpoint invoked")

        authors = LocalAuthor.objects.order_by('pk')
        page = request.GET.get("page")
        size = request.GET.get("size")

        if page and size:
            page = int(page)
            size = int(size)
            try:
                if page < 1 or size < 1:
                    return HttpResponseBadRequest("Malformed query: page and size must be > 0")
            except Exception as e:
                logger.error(e, exc_info=True)
                return HttpResponseBadRequest(e)
            authors = getPaginated(authors, page, size)

        authors = [author.as_json() for author in authors]
        response = {
            "type": "authors",
            "items": authors
        }

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class AuthorView(View):

    def get(self, request, author_id):
        """ GET - Retrieve profile of {author_id} """
        logger.info(f"GET /authors/{author_id} API endpoint invoked")

        author = get_object_or_404(LocalAuthor, pk=author_id)
        response = author.as_json()

        return JsonResponse(response)

    @method_decorator(authenticate_request)
    def post(self, request, author_id):
        """ POST - Update profile of {author_id} """
        logger.info(f"POST /authors/{author_id} API endpoint invoked")

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
        logger.info(f"GET /authors/{author_id}/followers API endpoint invoked")

        author = get_object_or_404(LocalAuthor, pk=author_id)
        followers = [follow.actor.as_json() for follow in author.follows.all()]

        response = {
            "type": "followers",
            "items": followers
        }

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class FollowersSingleView(View):

    def get(self, request, author_id, foreign_author_id):
        """ GET - Check if {foreign_author_id} is a follower of {author_id} """

        author = get_object_or_404(LocalAuthor, pk=author_id)
        logger.info(f"GET /author/{author_id}/followers/{foreign_author_id} API endpoint invoked")

        try:
            # try to find and return follower author object
            follower = Author.objects.get(url=foreign_author_id)
            follow = author.follows.get(actor=follower)
            response = follow.actor.as_json()
            return JsonResponse(response)

        except (Author.DoesNotExist, Follow.DoesNotExist):
            # return 404 if author not found
            return HttpResponseNotFound()

    def delete(self, request, author_id, foreign_author_id):
        """ DELETE - Remove {foreign_author_id} as a follower of {author_id} """
        logger.info(f"DELETE /author/{author_id}/followers/{foreign_author_id} API endpoint invoked")

        author = get_object_or_404(LocalAuthor, pk=author_id)

        try:
            # try to find and delete follower author object
            follower = Author.objects.get(url=foreign_author_id)
            follow = author.follows.get(actor=follower)
            follow.delete()
            return HttpResponse(status=204)  # no content
        except (Author.DoesNotExist, Follow.DoesNotExist):
            # return 404 if author not found
            return HttpResponseNotFound()


@method_decorator(csrf_exempt, name='dispatch')
class LikedView(View):

    def get(self, request, author_id):
        """ GET - Get a list of like objects from {author_id} """
        logger.info(f"GET /author/{author_id}/liked API endpoint invoked")

        try:
            page = request.GET.get("page")
            size = request.GET.get("size")

            author = LocalAuthor.objects.get(id=author_id)
            author_liked_posts = LocalPost.objects.filter(
                likes__author=author,
                visibility=LocalPost.Visibility.PUBLIC
            )

            author_liked_comments = Comment.objects.filter(likes__author=author)
            likes = []
            for post in author_liked_posts:
                like = {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{author.displayName} Likes your post",
                    "type": "like",
                    "author": author.as_json(),
                    "object": f"{API_BASE}/author/{post.author.id}/posts/{post.id}"
                }
                likes.append(like)

            for comment in author_liked_comments:
                like = {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{author.displayName} Likes your comment",
                    "type": "like",
                    "author": author.as_json(),
                    "object": f"{API_BASE}/author/{comment.post.author.id}/posts/{comment.post.id}/comments/{comment.id}"
                }
                likes.append(like)

            response = {
                "type": "liked",
                "items": likes
            }

        except LocalAuthor.DoesNotExist:
            return HttpResponseNotFound()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class PostsView(View):

    def get(self, request, author_id):
        logger.info(f"GET /author/{author_id}/posts API endpoint invoked")

        # Send all PUBLIC posts
        try:
            # TODO handle pagination
            page = request.GET.get("page")
            size = request.GET.get("size")
            author = get_object_or_404(LocalAuthor, id=author_id)
            posts = LocalPost.objects.listed().get_public().filter(author=author).order_by('pk')

            if page and size:
                page = int(page)
                size = int(size)
                try:
                    if page < 1 or size < 1:
                        return HttpResponseBadRequest("Malformed query: page and size must be > 0")
                except Exception as e:
                    return HttpResponseBadRequest(e)
                posts = getPaginated(posts, page, size)

            posts = [post.as_json() for post in posts]

            response = {
                "type": "posts",
                "page": page,
                "size": size,
                "items": posts
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
        """ GET - Get json for post {post_id} """
        logger.info(f"GET /author/{author_id}/posts/{post_id} API endpoint invoked")


        try:
            post = LocalPost.objects.get(id=post_id)
            response = post.as_json()

        except LocalPost.DoesNotExist:
            return HttpResponseNotFound()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)
    
    # TODO: authenticate
    def delete(self, request, author_id, post_id):
        """ DELETE - Delete post {post_id} """
        logger.info(f"DELETE /author/{author_id}/posts/{post_id} API endpoint invoked")

        try:
            post = LocalPost.objects.get(id=post_id)
            post.delete()

        except LocalPost.DoesNotExist:
            return HttpResponseNotFound()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return HttpResponse(200)
    
    # TODO: authenticate
    def post(self, request, author_id, post_id):
        """ POST - Update post {post_id} """
        logger.info(f"POST /author/{author_id}/posts/{post_id} API endpoint invoked")


        data = json.loads(request.body)
        post = LocalPost.objects.get(id=post_id)

        try:
            post.title = data['title']
            post.description = data['description']
            post.content_type = data['contentType']
            post.content = data['content'].encode('utf-8')
            post.visibility = data['visibility']
            post.unlisted = data['unlisted']

            categories = data['categories']

            if categories is not None:
                categories_to_remove = [cat.category for cat in post.categories.all()]

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
            return JsonResponse(status=201, data=post.as_json())

        except ValidationError:
            messages.info(request, 'Unable to edit post.')


@method_decorator(csrf_exempt, name='dispatch')
class PostLikesView(View):

    def get(self, request, author_id, post_id):
        """ GET - Get a list of authors who like {post_id} """
        logger.info(f"GET /author/{author_id}/posts/{post_id}/likes API endpoint invoked")


        try:
            post = LocalPost.objects.get(id=post_id)
            authors = [like.author.as_json() for like in post.likes.all()]

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
        logger.info(f"GET /author/{author_id}/posts/{post_id}/comments API endpoint invoked")

        # Send all comments
        try:
            page = request.GET.get("page")
            size = request.GET.get("size")
            post = get_object_or_404(LocalPost, id=post_id)
            author = get_object_or_404(LocalAuthor, id=author_id)
            # Check if the post author match with author in url
            if post.author.id != author.id:
                return HttpResponseNotFound()

            comments = post.comments()

            if page and size:
                page = int(page)
                size = int(size)
                try:
                    if page < 1 or size < 1:
                        return HttpResponseBadRequest("Malformed query: page and size must be > 0")
                except Exception as e:
                    logger.error(e, exc_info=True)
                    return HttpResponseBadRequest(e)

                comments = getPaginated(comments, page, size)

            comments = [comment.as_json() for comment in comments]
            response = {
                "type": "comments",
                "page": page,
                "size": size,
                "post": f"{API_BASE}/author/{author_id}/posts/{post_id}",
                "id": f"{API_BASE}/author/{author_id}/posts/{post_id}/comments",
                "comments": comments
            }

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)

    def post(self, request, author_id, post_id):
        return NotImplementedError()


@method_decorator(csrf_exempt, name='dispatch')
class CommentLikesView(View):

    def get(self, request, author_id, post_id, comment_id):
        """ GET - Get a list of likes on comment_id which 
            was made on post_id which was created by author_id
        """
        logger.info(f"GET /author/{author_id}/posts/{post_id}/comments/{comment_id} API endpoint invoked")

        try:
            author = get_object_or_404(LocalAuthor, pk=author_id)
            post = get_object_or_404(
                LocalPost, 
                id=post_id, 
                author=author,
                visibility=LocalPost.Visibility.PUBLIC
            )
            comment = get_object_or_404(Comment, id=comment_id, post=post)

            comment_likes = comment.likes.all()
            comment_likes_list = []

            for like in comment_likes:
                if Author.objects.filter(url=like.author.url).exists():
                    like_author = Author.objects.get(url=like.author.url)
                    like_author_json = like_author.as_json()

                    like = {
                        "@context": "https://www.w3.org/ns/activitystreams",
                        "summary": f"{like_author_json['displayName']} Likes your comment",
                        "type": "like",
                        "author": like_author_json,
                        "object": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment.id}"
                    }
                    comment_likes_list.append(like)

            response = {
                "type": "likes",
                "items": comment_likes_list
            }

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class InboxView(View):
    """ This endpoint currently only works for requests from local server.
    """

    @method_decorator(authenticate_request)
    def get(self, request, author_id):
        """ GET - If authenticated, get a list of posts sent to {author_id} """

        logger.info(f"GET /author/{author_id}/inbox/ API endpoint invoked")


        return JsonResponse({
            "message": f"This is the inbox for author_id={author_id}. Only author {author_id} can read this."
        })

    # TODO: authenticate user
    @method_decorator(validate_node)
    def post(self, request, author_id):
        """ POST - Send a post to {author_id}
            - if the type is “post” then add that post to the author’s inbox
            - if the type is “follow” then add that follow is added to the author’s inbox to approve later
            - if the type is “like” then add that like to the author’s inbox    
        """
        logger.info(f"POST /author/{author_id}/inbox/ API endpoint invoked")

        data = json.loads(request.body)

        logger.info(f"inbox request body\n{data}")
        try:
            if str(data["type"]).lower() == "post":
                logger.info("Inbox object identified as post")

                makePost(author_id, data)
                return HttpResponse(status=200)

            elif str(data["type"]).lower() == "follow":
                logger.info("Inbox object identified as follow")

                # actor requests to follow object
                actor, obj = data["actor"], data["object"]
                if not url_parser.is_local_url(obj["id"]):
                    raise ValueError("Author not hosted on this server")

                object_id = url_parser.parse_author(obj["id"])

                # check if this is the correct endpoint
                if object_id != author_id:
                    raise ValueError("Object ID does not match inbox ID")

                object_author = get_object_or_404(LocalAuthor, id=object_id)
                actor_author, created = Author.objects.get_or_create(
                    url = actor["id"]
                )

                # add or update remaining fields
                add_or_update_author(author=actor_author, data=actor)

                # add follow request
                object_author.follow_requests.add(actor_author)

                return HttpResponse(status=200)

            elif str(data["type"]).lower() == "like":
                logger.info("Inbox object identified as like")

                # retrieve author
                liking_author, created = Author.objects.get_or_create(
                    url= data["author"]["id"]
                )

                # add or update remaining fields
                add_or_update_author(author=liking_author, data=data["author"])

                # retrieve object
                object_type = url_parser.get_object_type(data['object'])
                if object_type == "posts":
                    _, id = url_parser.parse_post(data['object'])
                    context_object = get_object_or_404(LocalPost, id=id)
                elif object_type == "comments":
                    _, __, id = url_parser.parse_comment(data['object'])
                    context_object = get_object_or_404(Comment, id=id)
                else:
                    raise ValueError("Unknown object type")

                if context_object.likes.filter(author=liking_author).exists():
                    # if like already exists, remove it
                    like = context_object.likes.get(author=liking_author)
                    like.delete()
                else:
                    # create a new like from liking_author on object
                    context_object.likes.create(author=liking_author, object=context_object)

                return HttpResponse(status=200)

            elif str(data["type"]).lower() == "comment":
                logger.info("Inbox object identified as comment")

                # check if comment attribute present
                if not data['comment']:
                    HttpResponseBadRequest("Attribute 'comment' in json body must be a non-empty string.")

                # retrieve author
                commenting_author, created = Author.objects.get_or_create(
                    url = data["author"]['id']
                )

                # add or update remaining fields
                add_or_update_author(author=commenting_author, data=data["author"])

                _, post_id = url_parser.parse_post(data['object'])
                post = get_object_or_404(LocalPost, id=post_id)
                # add remote comment
                Comment.objects.create(
                    author = commenting_author,
                    post = post,
                    comment = data['comment'],
                    content_type = data['contentType'],
                    pub_date= datetime.now(timezone.utc),
                )

                return HttpResponse(status=200)
            else:
                raise ValueError("Unknown object received by inbox")

        except KeyError as e:
            logger.warn(e, exc_info=True)
            return JsonResponse({
                "error": "JSON body could not be parsed"
            })

        except ValueError as e:
            logger.warn(e, exc_info=True)
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

        logger.info(f"POST /author/{author_id}/inbox/ API endpoint invoked")

        return HttpResponse("Hello")
