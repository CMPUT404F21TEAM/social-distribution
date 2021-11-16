# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mixer.backend.django import mixer
import json

from socialDistribution.models import LocalPost, Category, LocalAuthor
from .test_authors import create_author
from cmput404.constants import HOST, API_PREFIX
from datetime import datetime


def get_post_json(post):
    previousCategories = Category.objects.filter(post=post)
    previousCategoriesNames = [cat.category for cat in previousCategories]
    return {
            "type":"post",
            "title":post.title,
            "id": f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}",
            "source":"blah",
            "origin":"blah",
            "description":post.description,
            "contentType":post.get_content_type_display(),
            "content":post.content, # 
            "author":post.author.as_json(),
            "categories":previousCategoriesNames,
            "count": 0,
            "comments":f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}/comments/",
            "commentsSrc":post.comments_as_json,
            "published":post.published.isoformat(),
            "visibility":post.get_visibility_display(),
            "unlisted":post.unlisted
        }

class PostsViewTest(TestCase):

    def test_get_posts_basic(self):
        self.maxDiff = None
        post = mixer.blend(LocalPost, content_type='PL')
        expected = {
            "type":"posts",
            "page": None,
            "size": None,
            "items": [get_post_json(post)]
            }

        response = self.client.get(reverse('api:posts', args=(post.author.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)
        
    def test_get_posts_paginated(self):
        self.maxDiff = None
        page = 1
        size = 2
        author = mixer.blend(LocalAuthor)
        post1 = mixer.blend(LocalPost, content_type='PL', author=author)
        post2 = mixer.blend(LocalPost, content_type='PL', author=author)

        expected = {
                "type": "posts",
                "page": page,
                "size": size,
                "items": [get_post_json(post1), get_post_json(post2)]
            }
        
        response = self.client.get(reverse('api:posts', args=(post1.author.id,)) + f'?page={page}&size={size}')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)
        
    def test_get_posts_paginated_page_2(self):
        self.maxDiff = None
        page = 2
        size = 2
        author = mixer.blend(LocalAuthor)
        post1 = mixer.blend(LocalPost, content_type='PL', author=author)
        post2 = mixer.blend(LocalPost, content_type='PL', author=author)
        post3 = mixer.blend(LocalPost, content_type='PL', author=author)

        expected = {
                "type": "posts",
                "page": page,
                "size": size,
                "items": [get_post_json(post3)]
            }
        
        response = self.client.get(reverse('api:posts', args=(post1.author.id,)) + f'?page={page}&size={size}')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)