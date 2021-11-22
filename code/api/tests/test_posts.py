# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mixer.backend.django import mixer
import base64 as b64

from socialDistribution.models import LocalPost, Category, LocalAuthor
from api.models import Node
from .test_authors import create_author
from cmput404.constants import HOST, API_PREFIX
from datetime import datetime
import base64

def create_post(title, author):
    return LocalPost.objects.create(
            author_id=author.id,
            title=title,
            description="testDesc",
            content_type=LocalPost.ContentType.PLAIN,
            content="testContexxt".encode("utf-8"),
            visibility=LocalPost.Visibility.PUBLIC,
            unlisted=False,
        )


def get_post_json(post):
    previousCategories = post.categories.all()
    previousCategoriesNames = [cat.category for cat in previousCategories]
    return {
            "type":"post",
            "title":post.title,
            "id": f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}",
            "source": post.author.get_url_id() + f'/posts/{post.id}',
            "origin": post.author.get_url_id() + f'/posts/{post.id}',
            "description":post.description,
            "contentType":post.get_content_type_display(),
            "content":post.decoded_content, # 
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


class PostViewTest(TestCase):

    basicAuthHeaders = {
        'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(b'remotegroup:topsecret!').decode("ascii"),
    }

    def setUp(self):
        Node.objects.create(host=HOST, basic_auth_credentials='remotegroup:topsecret!')

    def test_get_single_post(self):
        author = mixer.blend(LocalAuthor)
        post = create_post("single-post", author)

        expected = get_post_json(post)
        response = self.client.get(
            reverse('api:post', args=(author.id, post.id)),
            HTTP_REFERER=HOST,
            **self.basicAuthHeaders
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)

    def test_get_post_notfound_1(self):
        author1 = mixer.blend(LocalAuthor)
        author2 = mixer.blend(LocalAuthor)
        post = create_post("single-post", author2)

        response = self.client.get(
            reverse('api:post', args=(author1.id, post.id)),
            HTTP_REFERER=HOST,
            **self.basicAuthHeaders
        )
        self.assertEqual(response.status_code, 404)

    def test_get_post_notfound_2(self):
        author = mixer.blend(LocalAuthor)
        post = create_post("single-post", author)
        post.id = 100
        post.save()

        response = self.client.get(
            reverse('api:post', args=(author.id, 10)),
            HTTP_REFERER=HOST,
            **self.basicAuthHeaders
        )
        self.assertEqual(response.status_code, 404)

    def test_get_post_not_public(self):
        author = mixer.blend(LocalAuthor)
        post = create_post("single-post", author)
        post.visibility = LocalPost.Visibility.PRIVATE
        post.save()

        response = self.client.get(
            reverse('api:post', args=(author.id, post.id)),
            HTTP_REFERER=HOST,
            **self.basicAuthHeaders
        )
        self.assertEqual(response.status_code, 404)

        post.visibility = LocalPost.Visibility.FRIENDS
        post.save()

        response = self.client.get(
            reverse('api:post', args=(author.id, post.id)),
            HTTP_REFERER=HOST,
            **self.basicAuthHeaders
        )
        self.assertEqual(response.status_code, 404)