# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mixer.backend.django import mixer

import base64 as b64
import logging
from datetime import datetime

from socialDistribution.models import LocalPost, Category, LocalAuthor
from .test_authors import create_author
from cmput404.constants import API_BASE
from datetime import datetime

def create_post(title, author):
    post = LocalPost.objects.create(
            author_id=author.id,
            title=title,
            description="testDesc",
            content_type=LocalPost.ContentType.PLAIN,
            content="testContexxt".encode("utf-8"),
            visibility=LocalPost.Visibility.PUBLIC,
            unlisted=False,
        )
    post.origin = post.get_id()
    post.source = post.get_id()
    post.save()
    
    return post


def get_post_json(post):
    previousCategories = post.categories.all()
    previousCategoriesNames = [cat.category for cat in previousCategories]
    return {
            "type":"post",
            "title":post.title,
            "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
            "source":f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
            "origin":f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
            "description":post.description,
            "contentType":post.get_content_type_display(),
            "content":post.decoded_content, # 
            "author":post.author.as_json(),
            "categories":previousCategoriesNames,
            "count": 0,
            "comments":f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/",
            "commentsSrc":post.comments_as_json,
            "published":post.published.isoformat(),
            "visibility":post.get_visibility_display(),
            "unlisted":post.unlisted
        }

class PostsViewTest(TestCase):

    # the pillow, https://stackoverflow.com/users/2812257/the-pillow, "How can I disable logging while running unit tests in Python Django?"
    # https://stackoverflow.com/a/54519433, 2019-02-04, CC BY-SA 4.0

    # disable logging before tests
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    # enable logging after tests
    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def test_get_posts_basic(self):
        self.maxDiff = None
        author = mixer.blend(LocalAuthor)
        post = create_post("first", author)
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
        post1 = create_post("first", author)
        post2 = create_post("second", author)

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
        post1 = create_post("first", author)
        post2 = create_post("second", author)
        post3 = create_post("third", author)

        expected = {
                "type": "posts",
                "page": page,
                "size": size,
                "items": [get_post_json(post3)]
            }
        
        response = self.client.get(reverse('api:posts', args=(post1.author.id,)) + f'?page={page}&size={size}')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)