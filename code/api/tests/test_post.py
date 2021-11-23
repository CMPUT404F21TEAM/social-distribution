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
            "id": f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}",
            "source": f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}",
            "origin": f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}",
            "description":post.description,
            "contentType":post.get_content_type_display(),
            "content":post.content,
            "author":post.author.as_json(),
            "categories":previousCategoriesNames,
            "count": 0,
            "comments":f"http://{HOST}/{API_PREFIX}/author/{post.author.id}/posts/{post.id}/comments/",
            "commentsSrc":post.comments_as_json,
            "published":post.published.isoformat(),
            "visibility":post.get_visibility_display(),
            "unlisted":post.unlisted
        }

class PostViewTest(TestCase):

    def test_get_post_basic(self):
        self.maxDiff = None
        author = mixer.blend(LocalAuthor)
        post = create_post("first", author)
        expected = get_post_json(post)
        expected['content'] = expected['content'].decode('utf-8')

        response = self.client.get(reverse('api:post', args=(post.author.id,post.id)))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)
        
    def test_post_post(self):
        self.maxDiff = None
        author = mixer.blend(LocalAuthor)
        post = create_post("first", author)
        newJson = get_post_json(post)
        newJson['title'] = 'newPost'
        newJson['content'] = newJson['content'].decode('utf-8')

        response = self.client.post(reverse('api:post', args=(post.author.id,post.id)), content_type="application/json", data=json.dumps(newJson))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(newJson['title'], LocalPost.objects.filter(id=post.id).first().title)
        
    def test_delete_post(self):
        self.maxDiff = None
        author = mixer.blend(LocalAuthor)
        post = create_post("first", author)

        response = self.client.delete(reverse('api:post', args=(post.author.id,post.id)))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LocalPost.objects.filter(id=post.id).exists())
        