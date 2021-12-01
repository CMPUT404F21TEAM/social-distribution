# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mixer.backend.django import mixer

import json
import base64
import logging

from socialDistribution.models import PostLike, CommentLike, Comment, LocalAuthor, LocalPost
from cmput404.constants import API_BASE, HOST
from  api.models import Node
from .test_post import create_post, get_post_json
from .test_inbox import create_author
from datetime import datetime

def create_postlike(author, object):
    return PostLike.objects.create(
        author=author,
        object=object
    )

def post_like_as_json(postlike):
    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "summary": f"{postlike.author.displayName} Likes your post",
        "author": postlike.author.as_json(),
        "type": "Like",
        "object": f"{API_BASE}/author/{postlike.object.author.id}/posts/{postlike.object.id}"
    }


def create_commentlike(author, object):
    return CommentLike.objects.create(
        author=author,
        object=object
    )

def comment_like_as_json(commentlike):
    post = commentlike.object.post
    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "summary": f"{commentlike.author.displayName} Likes your comment",
        "author": commentlike.author.as_json(),
        "type": "Like",
        "object": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{commentlike.object.id}"
    }


class LikedViewTest(TestCase):

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

    def test_get_liked_postlikes(self):
        author1 = create_author(
            "user1",
            "user 1",
            ""
        )

        author2 = create_author(
            "user2",
            "user 2",
            ""
        )

        post1 = create_post("Test post 1", author1)
        post2 = create_post("Test post 2", author2)

        author3 = create_author(
            "user3",
            "user 3",
            ""
        )

        post_like1 = create_postlike(author3, post1)
        post_like2 = create_postlike(author3, post2)

        expected = {
            "type": "liked",
            "items": [
                post_like_as_json(post_like1),
                post_like_as_json(post_like2)
            ]
        }

        response = self.client.get(reverse('api:liked', args=(author3.id,)))
        self.assertEqual(response.status_code, 200)

        self.maxDiff = None
        res_json = response.json()
        self.assertTrue(res_json["type"] == "liked")

        for post_like in expected["items"]:
            self.assertIn(post_like, res_json["items"])

    def test_get_liked_commentlikes(self):
        author1 = mixer.blend(LocalAuthor)
        author2 = mixer.blend(LocalAuthor)
        post1 = create_post('Test post 1', author1)
        post2 = create_post('Test post 2', author2)

        author3 = mixer.blend(LocalAuthor)
        
        comment1 = mixer.blend(Comment, author=author1, post=post2)
        comment2 = mixer.blend(Comment, author=author2, post=post1)
        comment3 = mixer.blend(Comment, author=author3, post=post1)

        comment_like1 = create_commentlike(author3, comment1)
        comment_like2 = create_commentlike(author3, comment2)
        comment_like3 = create_commentlike(author3, comment3)

        expected = {
            "type": "liked",
            "items": [
                comment_like_as_json(comment_like1),
                comment_like_as_json(comment_like2),
                comment_like_as_json(comment_like3)
            ]
        }

        response = self.client.get(reverse('api:liked', args=(author3.id,)))
        self.assertEqual(response.status_code, 200)
        
        res_json = response.json()
        self.assertTrue(res_json["type"] == "liked")
        for comment_like in expected["items"]:
            self.assertIn(comment_like, res_json["items"])

    def test_get_liked(self):
        author1 = mixer.blend(LocalAuthor)
        author2 = mixer.blend(LocalAuthor)
        author3 = mixer.blend(LocalAuthor)
        author4 = mixer.blend(LocalAuthor)
        author5 = mixer.blend(LocalAuthor)

        post1 = create_post('Test post 1', author1)
        post2 = create_post('Test post 2', author2)
        post3 = create_post('Test post 3', author3)
        post4 = create_post('Test post 4', author4)
        
        comment1 = mixer.blend(Comment, author=author1, post=post1)
        comment2 = mixer.blend(Comment, author=author2, post=post2)
        comment3 = mixer.blend(Comment, author=author2, post=post3)
        comment4 = mixer.blend(Comment, author=author3, post=post4)
        comment5 = mixer.blend(Comment, author=author4, post=post2)

        post_like1 = create_postlike(author5, post1)
        post_like2 = create_postlike(author5, post2)
        post_like3 = create_postlike(author5, post3)
        post_like4 = create_postlike(author5, post4)

        comment_like1 = create_commentlike(author5, comment1)
        comment_like2 = create_commentlike(author5, comment2)
        comment_like3 = create_commentlike(author5, comment3)
        comment_like4 = create_commentlike(author5, comment4)
        comment_like5 = create_commentlike(author5, comment5)

        expected = {
            "type": "liked",
            "items": [
                post_like_as_json(post_like1),
                post_like_as_json(post_like2),
                post_like_as_json(post_like3),
                post_like_as_json(post_like4),
                comment_like_as_json(comment_like1),
                comment_like_as_json(comment_like2),
                comment_like_as_json(comment_like3),
                comment_like_as_json(comment_like4),
                comment_like_as_json(comment_like5),
            ]
        }

        response = self.client.get(reverse('api:liked', args=(author5.id,)))
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertTrue(res_json["type"] == "liked")

        for like in expected["items"]:
            self.assertIn(like, res_json["items"])


class TestCommentLikesView(TestCase):

    # the pillow, https://stackoverflow.com/users/2812257/the-pillow, "How can I disable logging while running unit tests in Python Django?"
    # https://stackoverflow.com/a/54519433, 2019-02-04, CC BY-SA 4.0

    # disable logging before tests
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)
        Node.objects.create(host=HOST, username='testclient', password='testpassword!', remote_credentials=False)
        cls.basicAuthHeaders = {
            'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(b'testclient:testpassword!').decode("ascii"),
        }

    # enable logging after tests
    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def test_get_comments(self):
        author1 = mixer.blend(LocalAuthor)
        author2 = mixer.blend(LocalAuthor)
        author3 = mixer.blend(LocalAuthor)
        author4 = mixer.blend(LocalAuthor)

        post = create_post("Test post", author1)

        comment = mixer.blend(Comment, author=author1, post=post)

        comment_like1 = create_commentlike(author2, comment)
        comment_like2 = create_commentlike(author3, comment)
        comment_like3 = create_commentlike(author4, comment)

        expected = {
            "type": "likes",
            "items": [
                comment_like_as_json(comment_like1),
                comment_like_as_json(comment_like2),
                comment_like_as_json(comment_like3),
            ]
        }

        response = self.client.get(
            reverse('api:comment_likes', args=(author1.id, post.id, comment.id,)),
            **self.basicAuthHeaders
        )
        self.maxDiff = None
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(json.dumps(expected), response.json())
        