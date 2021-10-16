from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core import serializers
from socialDistribution.models import *

# Create your views here.


def index(request):
    return HttpResponse("Welcome to the Social Distribution API")


def authors(request):
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


def author(request, author_id):
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


def followers(request, author_id):
    return HttpResponse("This is the authors/aid/followers/ endpoint")


def liked(request, author_id):
    return HttpResponse("This is the authors/aid/liked/ endpoint")


def post(request, author_id, post_id):
    return HttpResponse("This is the authors/aid/posts/pid/ endpoint")


def post_likes(request, author_id, post_id):
    return HttpResponse("This is the authors/aid/posts/pid/likes/ endpoint")


def post_comments(request, author_id, post_id):
    return HttpResponse("This is the authors/aid/posts/pid/comments/ endpoint")


def comment_likes(request, author_id, post_id, comment_id):
    return HttpResponse("This is the authors/aid/posts/pid/comments/cid/likes/ endpoint")


def inbox(request, author_id):
    return HttpResponse("This is the authors/aid/inbox/ endpoint")
