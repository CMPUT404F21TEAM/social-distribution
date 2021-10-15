from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.

def index(request): 
    return HttpResponse("Welcome to the Social Distribution API", status=200)

def authors(request):
    return HttpResponse("This is the authors/ endpoint")

def author(request, author_id):
    return HttpResponse("This is the authors/aid/ endpoint")

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
