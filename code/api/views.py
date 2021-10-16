from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from socialDistribution.models import *

# https://docs.djangoproject.com/en/3.2/topics/class-based-views/intro/


def index(request):
    return HttpResponse("Welcome to the Social Distribution API")


@method_decorator(csrf_exempt, name='dispatch')
class AuthorsView(View):

    def get(self, request):
        page = request.GET.get("page")
        size = request.GET.get("size")

        data = []
        for author in Author.objects.all():
            data.append(
                {
                    # WARNING: hardcode
                    "type": "author",
                    "id": f"http://127.0.0.1:8000/authors/{author.id}",
                    "url": f"http://127.0.0.1:8000/author/{author.id}",
                    "host": "http://127.0.0.1:8000/",
                    "displayName": author.displayName,
                    "github": author.githubUrl,
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                }
            )

        response = {
            "type": "authors",
            "items": data
        }

        return JsonResponse(response)


@method_decorator(csrf_exempt, name='dispatch')
class AuthorView(View):

    def get(self, request, author_id):
        author = get_object_or_404(Author, pk=author_id)
        response = {
            # WARNING; hardcode
            "type": "author",
            "id": f"http://127.0.0.1:8000/authors/{author.id}",
            "url": f"http://127.0.0.1:8000/author/{author.id}",
            "host": "http://127.0.0.1:8000/",
            "displayName": author.displayName,
            "github": author.githubUrl,
            "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
        }
        return JsonResponse(response)

    def post(self, request, author_id):
        return HttpResponse("authors post\nupdate profile")


@method_decorator(csrf_exempt, name='dispatch')
class FollowersView(View):

    def get(self, request, author_id):
        return HttpResponse("This is the authors/aid/followers/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class LikedView(View):

    def get(self, request, author_id):
        return HttpResponse("This is the authors/aid/liked/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class PostView(View):

    def get(self, request, author_id, post_id):
        return HttpResponse("This is the authors/aid/posts/pid/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class PostLikesView(View):

    def get(self, request, author_id, post_id):
        return HttpResponse("This is the authors/aid/posts/pid/likes/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class PostCommentsView(View):

    def get(self, request, author_id, post_id):
        return HttpResponse("This is the authors/aid/posts/pid/comments/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class CommentLikesView(View):

    def get(self, request, author_id, post_id, comment_id):
        return HttpResponse("This is the authors/aid/posts/pid/comments/cid/likes/ endpoint")


@method_decorator(csrf_exempt, name='dispatch')
class InboxView(View):

    def get(self, request, author_id):
        return HttpResponse("This is the authors/aid/inbox/ endpoint")
