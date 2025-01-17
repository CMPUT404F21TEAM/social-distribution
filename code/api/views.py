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
from .decorators import validate_user, validate_node
from .parsers import url_parser
from .utility import getPaginated, makeInboxPost, makeLocalPost

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
    response = {
        "message": "Welcome to the Social Distribution API for T04",
        "documentation": "https://github.com/CMPUT404F21TEAM/social-distribution/wiki/Web-Service-API-Documentation",
        "authors": f'{API_BASE}/authors/'
    }
    return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class AuthorsView(View):

    def get(self, request):
        """ GET - Retrieve all user profiles
            'page' is indexed from 1, NOT 0.
            'size' must be greater than 0
        """
        logger.info(f"GET /authors API endpoint invoked")

        authors = LocalAuthor.objects.order_by('created_date')
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

    @method_decorator(validate_user)
    def post(self, request, author_id):
        """ POST - Update profile of {author_id} """
        logger.info(f"POST /authors/{author_id} API endpoint invoked")

        author = get_object_or_404(LocalAuthor, id=author_id)
        djangoUser = author.user

        try:
            data = json.loads(request.body)

            # extract post data
            if data.get('displayName'):
                author.displayName = data.get('displayName')
            if data.get('github'):
                author.githubUrl = data.get('github')
            if data.get('email'):
                djangoUser.email = data.get('email')
            if data.get('profileImage'):
                author.profileImageUrl = data.get('profileImage')

            # update author
            author.save()

            # update django user
            djangoUser.save()

        except json.decoder.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON"
            }, status=400)

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(author.as_json())


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

        logger.info(f"GET /author/{author_id}/followers/{foreign_author_id} API endpoint invoked")
        author = get_object_or_404(LocalAuthor, pk=author_id)

        try:
            # try to find and return follower author object
            follower = Author.objects.get(url=foreign_author_id)
            follow = author.follows.get(actor=follower)
            response = follow.actor.as_json()
            return JsonResponse(response)

        except (Author.DoesNotExist, Follow.DoesNotExist):
            # return 404 if author not found
            return HttpResponseNotFound()

    @method_decorator(validate_user)
    def put(self, request, author_id, foreign_author_id):
        """ PUT - Add {foreign_author_id} as a follower of {author_id} """

        logger.info(f"PUT /author/{author_id}/followers/{foreign_author_id} API endpoint invoked")
        author = get_object_or_404(LocalAuthor, pk=author_id)

        follower, created = Author.objects.get_or_create(url=foreign_author_id)

        follow_obj = Follow.objects.create(
            object=author,
            actor=follower
        )

        author.follows.add(follow_obj)  # django doesn't duplicate relations

        response = follower.as_json()

        return JsonResponse(response)

    @method_decorator(validate_node)
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

        author = get_object_or_404(LocalAuthor, id=author_id)

        try:

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
                    "type": "Like",
                    "author": author.as_json(),
                    "object": f"{API_BASE}/author/{post.author.id}/posts/{post.id}"
                }
                likes.append(like)

            for comment in author_liked_comments:
                like = {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{author.displayName} Likes your comment",
                    "type": "Like",
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

        author = get_object_or_404(LocalAuthor, id=author_id)

        # Send all PUBLIC posts
        try:
            page = request.GET.get("page")
            size = request.GET.get("size")
            posts = LocalPost.objects.listed().get_public().filter(author=author).order_by('pk')

            if page and size:
                page = int(page)
                size = int(size)
                try:
                    if page < 1 or size < 1:
                        return HttpResponseBadRequest({
                            "error": "Malformed query: page and size must be > 0"
                        })
                except Exception as e:
                    return HttpResponseBadRequest()
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

    @method_decorator(validate_user)
    def post(self, request, author_id):
        '''
            POST - creates a LocalPost for the given {author_id} with the given data
        '''

        try:
            data = json.loads(request.body)
            post = makeLocalPost(data, author_id)

        except json.decoder.JSONDecodeError as e:
            return JsonResponse({
                "error": "Invalid JSON: " + e.msg
            }, status=400)

        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({
                "error": "An unknown error occurred"
            }, status=500)

        return JsonResponse(status=201, data=post.as_json())


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

    @method_decorator(validate_user)
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

    @method_decorator(validate_user)
    def post(self, request, author_id, post_id):
        """ POST - Update post {post_id} """
        logger.info(f"POST /author/{author_id}/posts/{post_id} API endpoint invoked")

        post = get_object_or_404(LocalPost, id=post_id)
        data = json.loads(request.body)

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
            return HttpResponseBadRequest()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

    @method_decorator(validate_user)
    def put(self, request, author_id, post_id):
        '''
            PUT - creates a LocalPost for the given {author_id} with the given data with the given {post_id}
        '''
        get_object_or_404(LocalAuthor, id=author_id)
        try:
            data = json.loads(request.body)
            post = makeLocalPost(data, author_id, post_id)

        except json.decoder.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON"
            }, status=400)

        except ValidationError:
            return JsonResponse({
                "error": "Not a valid UUID"
            }, status=400)

        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({
                "error": "An unknown error occurred"
            }, status=500)

        return JsonResponse(status=201, data=post.as_json())


@method_decorator(csrf_exempt, name='dispatch')
class PostLikesView(View):

    def get(self, request, author_id, post_id):
        """ GET - Get a list of authors who like {post_id} """
        logger.info(f"GET /author/{author_id}/posts/{post_id}/likes API endpoint invoked")

        author = get_object_or_404(Author, id=author_id)
        post = get_object_or_404(LocalPost, id=post_id, author=author)

        try:
            post_likes = post.likes.all()

            items = []
            for like in post_likes:
                like_author_json = like.author.as_json()

                like = {
                    "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{like_author_json['displayName']} Likes your post",
                    "type": "Like",
                    "author": like_author_json,
                    "object": f"{API_BASE}/author/{post.author.id}/posts/{post.id}"
                }

                items.append(like)

            response = {
                "type": "likes",
                "items": items
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

        post = get_object_or_404(LocalPost, id=post_id)
        author = get_object_or_404(LocalAuthor, id=author_id)

        # Send all comments
        try:
            page = request.GET.get("page")
            size = request.GET.get("size")
            # Check if the post author match with author in url
            if post.author.id != author.id:
                return HttpResponseNotFound()

            comments = post.comments()

            if page and size:
                page = int(page)
                size = int(size)
                try:
                    if page < 1 or size < 1:
                        return HttpResponseBadRequest({
                            "error": "Malformed query: page and size must be > 0"
                        })
                except Exception as e:
                    logger.error(e, exc_info=True)
                    return HttpResponseBadRequest()

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


@method_decorator(csrf_exempt, name='dispatch')
class PostCommentsSingleView(View):
    '''
        HANDLE Singular Comment GET
    '''

    def get(self, request, author_id, post_id, comment_id):
        logger.info(f"GET /author/{author_id}/posts/{post_id}/comments/{comment_id} API endpoint invoked")

        post = get_object_or_404(LocalPost, id=post_id)
        author = get_object_or_404(LocalAuthor, id=author_id)
        comment = get_object_or_404(Comment, id=comment_id)

        # Send comment
        try:
            # Check if the post author match with author in url
            if post.author.id != author.id:
                return HttpResponseNotFound()

            # Check if the post id and comment id match
            if post.id != comment.post.id:
                return HttpResponseNotFound()

            response = comment.as_json()

        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponseServerError()

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class CommentLikesView(View):

    @method_decorator(validate_node)
    def get(self, request, author_id, post_id, comment_id):
        """ GET - Get a list of likes on comment_id which
            was made on post_id which was created by author_id
        """
        logger.info(f"GET /author/{author_id}/posts/{post_id}/comments/{comment_id} API endpoint invoked")
        author = get_object_or_404(LocalAuthor, pk=author_id)
        post = get_object_or_404(LocalPost, id=post_id, author=author)
        comment = get_object_or_404(Comment, id=comment_id, post=post)

        try:

            comment_likes = comment.likes.all()
            comment_likes_list = []

            for like in comment_likes:
                if Author.objects.filter(url=like.author.url).exists():
                    like_author = Author.objects.get(url=like.author.url)
                    like_author_json = like_author.as_json()

                    like = {
                        "@context": "https://www.w3.org/ns/activitystreams",
                        "summary": f"{like_author_json['displayName']} Likes your comment",
                        "type": "Like",
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
    @method_decorator(validate_user)
    def get(self, request, author_id):
        """ GET - If authenticated, get a list of posts sent to {author_id} """

        logger.info(f"GET /author/{author_id}/inbox/ API endpoint invoked")

        author = get_object_or_404(LocalAuthor, id=author_id)

        # Send all posts sent to the author's inbox
        try:
            page = request.GET.get("page")
            size = request.GET.get("size")
            posts = author.inbox_posts.all().order_by('-published')

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
                "type": "inbox",
                "author": author.url,
                "page": page,
                "size": size,
                "items": posts
            }

        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({
                "error": "An unknown error occurred"
            }, status=500)

        return JsonResponse(response)

    @method_decorator(validate_node)
    def post(self, request, author_id):
        """ POST - Send a post to {author_id}
            - if the type is “post” then add that post to the author’s inbox
            - if the type is “follow” then add that follow is added to the author’s inbox to approve later
            - if the type is “like” then add that like to the author’s inbox
        """
        logger.info(f"POST /author/{author_id}/inbox/ API endpoint invoked")

        try:
            data = json.loads(request.body)
            logger.info(f"Object recieved by {request.build_absolute_uri()}: \n{data}")

            if str(data["type"]).lower() == "post":
                logger.info("Inbox object identified as post")

                received_post = makeInboxPost(data)

                # get owner of inbox
                receiving_author = get_object_or_404(LocalAuthor, id=author_id)

                # add post to inbox of author
                receiving_author.inbox_posts.add(received_post)

                return HttpResponse(status=200)

            elif str(data["type"]).lower() == "follow":
                logger.info("Inbox object identified as follow")

                # actor requests to follow object
                actor, obj = data["actor"], data["object"]
                if not url_parser.is_local_url(obj["id"]):
                    raise ValueError("Author not hosted on this server")

                object_id = url_parser.parse_author(obj["id"])

                # check if this is the correct endpoint
                if object_id != str(author_id):
                    raise ValueError("Object ID does not match inbox ID")

                # try to get object author, otherwise raise 400 error
                try:
                    object_author = LocalAuthor.objects.get(id=object_id)
                except LocalAuthor.DoesNotExist:
                    raise ValueError("'object' does not exist")

                # get or create actor author
                actor_author, created = Author.objects.get_or_create(
                    url=actor["id"]
                )

                # add or update remaining fields
                actor_author.update_with_json(data=actor)

                # add follow request
                object_author.follow_requests.add(actor_author)

                return HttpResponse(status=200)

            elif str(data["type"]).lower() == "like":
                logger.info("Inbox object identified as like")

                # retrieve author
                liking_author, created = Author.objects.get_or_create(
                    url=data["author"]["id"]
                )

                # add or update remaining fields
                liking_author.update_with_json(data=data["author"])

                # retrieve object
                object_type = url_parser.get_object_type(data['object'])
                try:
                    if object_type == "posts":
                        _, id = url_parser.parse_post(data['object'])
                        context_object = LocalPost.objects.get(id=id)
                    elif object_type == "comments":
                        _, __, id = url_parser.parse_comment(data['object'])
                        context_object = Comment.objects.get(id=id)
                    else:
                        raise ValueError("Unknown object type")

                except (LocalPost.DoesNotExist, Comment.DoesNotExist):
                    raise ValueError("'object' does not exist")

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
                    raise ValueError("Attribute 'comment' in json body must be a non-empty string.")

                # retrieve author
                commenting_author, created = Author.objects.get_or_create(
                    url=data["author"]['id']
                )

                # add or update remaining fields
                commenting_author.update_with_json(data=data["author"])

                # get the post
                try:
                    _, post_id = url_parser.parse_post(data['object'])
                    post = LocalPost.objects.get(id=post_id)
                except LocalPost.DoesNotExist:
                    raise ValueError("'object' does not exist")

                # add remote comment
                Comment.objects.create(
                    author=commenting_author,
                    post=post,
                    comment=data['comment'],
                    content_type=data['contentType'],
                    pub_date=datetime.now(timezone.utc),
                )

                return HttpResponse(status=200)
            else:
                raise ValueError("Unknown object sent to inbox")

        except json.decoder.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON"
            }, status=400)

        except Http404:
            return HttpResponseNotFound()

        except KeyError as e:
            logger.warn(e, exc_info=True)
            return JsonResponse({
                "error": "JSON body could not be parsed",
                "details": f"{e.args[0]} field not found"
            }, status=400)

        except ValueError as e:
            logger.warn(e, exc_info=True)
            return JsonResponse({
                "error": e.args[0]
            }, status=400)

        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({
                "error": "An unknown error occurred"
            }, status=500)

    @method_decorator(validate_user)
    def delete(self, request, author_id):
        """ DELETE - Clear the inbox """

        logger.info(f"POST /author/{author_id}/inbox/ API endpoint invoked")
        author = get_object_or_404(LocalAuthor, id=author_id)
        author.follow_requests.clear()
        author.inbox_posts.clear()
        return HttpResponse(status=204)
