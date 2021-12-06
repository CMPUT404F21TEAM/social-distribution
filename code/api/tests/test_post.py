# python manage.py test api

from django.test import TestCase
from django.urls import reverse
from mixer.backend.django import mixer
import base64

import json
import logging
import uuid

from socialDistribution.models import LocalPost, LocalAuthor
from cmput404.constants import API_BASE
from .utilities import create_author, get_basic_auth


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
        "type": "post",
        "title": post.title,
        "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
        "source": f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
        "origin": f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
        "description": post.description,
        "contentType": post.get_content_type_display(),
        "content": post.content,
        "author": post.author.as_json(),
        "categories": previousCategoriesNames,
        "count": 0,
        "comments": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/",
        "commentsSrc": post.recent_comments_json,
        "published": post.published.isoformat(),
        "visibility": post.get_visibility_display(),
        "unlisted": post.unlisted
    }


class PostViewTest(TestCase):

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

    def setUp(self):
        self.basicAuthHeaders = {
            'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(b'testuser:123456!').decode("ascii"),
        }

    def test_get_post_basic(self):
        self.maxDiff = None
        author = mixer.blend(LocalAuthor)
        post = create_post("first", author)
        expected = get_post_json(post)
        expected['content'] = expected['content'].decode('utf-8')

        response = self.client.get(reverse('api:post', args=(post.author.id, post.id)))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)

    def test_post_post(self):
        self.maxDiff = None
        author = create_author()
        post = create_post("first", author)
        newJson = get_post_json(post)
        newJson['title'] = 'newPost'
        newJson['content'] = newJson['content'].decode('utf-8')

        response = self.client.post(
            reverse('api:post', args=(post.author.id, post.id)),
            content_type="application/json",
            data=json.dumps(newJson),
            **get_basic_auth(author)
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(newJson['title'], LocalPost.objects.filter(id=post.id).first().title)

    def test_put_post(self):
        self.maxDiff = None
        author = create_author()
        post = create_post("first", author)
        newJson = get_post_json(post)
        newJson['title'] = 'newPost'
        newJson['content'] = newJson['content'].decode('utf-8')
        post_id = uuid.uuid4()

        response = self.client.put(
            reverse('api:post', args=(post.author.id, str(post_id))),
            content_type="application/json",
            **get_basic_auth(author),
            data=json.dumps(newJson),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(newJson['title'], LocalPost.objects.latest('published').title)
        self.assertEqual(post_id, LocalPost.objects.latest('published').id)

    def test_delete_post(self):
        self.maxDiff = None
        author = create_author()
        post = create_post("first", author)

        response = self.client.delete(
            reverse('api:post', args=(post.author.id, post.id)),
            **get_basic_auth(author)
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LocalPost.objects.filter(id=post.id).exists())
