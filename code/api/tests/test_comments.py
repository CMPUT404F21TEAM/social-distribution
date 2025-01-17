# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from mixer.backend.django import mixer

import json
import datetime
import logging

from socialDistribution.models import Comment
from .test_authors import create_author
from cmput404.constants import API_BASE

def create_comment(author, content_type, comment, post, date=timezone.now()):
    return Comment.objects.create(
        author=author,
        content_type=content_type,
        comment=comment,
        pub_date=date,
        post=post
    )

def get_comments_json(post, comments, page=None, size=None):
    return {
        "type": "comments",
        "page": page,
        "size": size,
        "post": f"{API_BASE}/author/{post.author.id}/posts/{post.id}",
        "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments",
        "comments": comments
    }
    
def get_singular_comment_json(comment):
    return {
            "type": "comment",
            "author": comment.author.as_json(),
            "comment": comment.comment,
            "contentType": "text/markdown",
            "published": str(comment.pub_date),
            "id": f"{API_BASE}/author/{comment.post.author.id}/posts/{comment.post.id}/comments/{comment.id}",
        }
class PostCommentsViewTest(TestCase):

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

    def test_get_comment_basic(self):
        post = mixer.blend('socialDistribution.localpost')
        expected = get_comments_json(post, [])
        expected_data = json.dumps(expected)

        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_singular_comment(self):
        self.maxDiff = None
        post = mixer.blend('socialDistribution.localpost')
        comment_author = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment = create_comment(
            comment_author, 
            'text/markdown', 
            'Testing comment single author',
            post
        )

        expected = get_singular_comment_json(comment)

        expected_data = expected
        response = self.client.get(reverse('api:post_comments_single', args=(post.author.id, post.id, comment.id)))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected_data)

    def test_comment_single_author(self):
        post = mixer.blend('socialDistribution.localpost')
        comment_author = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment = create_comment(
            comment_author, 
            'text/markdown', 
            'Testing comment single author',
            post
        )

        expected_comments = [
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": comment_author.get_url_id(),
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": comment_author.get_url_id(),
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Testing comment single author",
                "contentType": "text/markdown",
                "published": str(comment.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment.id}"
            }
        ] 

        expected = get_comments_json(post, expected_comments)
        expected_data = json.dumps(expected)
        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected_data)


    def test_comment_multiple_authors(self):
        post = mixer.blend('socialDistribution.localpost')
        author1 = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author2 = create_author(
            "Jane Smith",
            "jane_smith",
            "https://github.com/jane_smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author3 = create_author(
            "Lara Croft",
            "lara_croft",
            "https://github.com/lara_croft",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment_author1 = create_comment(
            author1,
            "text/markdown",
            "Hello there",
            post
        )

        comment_author2 = create_comment(
            author2,
            "text/markdown",
            "This is great for testing",
            post
        )

        comment_author3 =create_comment(
            author3,
            "text/markdown",
            "Wow! This is such a nice comment for testing",
            post
        )

        expected_comments = [
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author1.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": f"{API_BASE}/author/{author1.id}",
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Hello there",
                "contentType": "text/markdown",
                "published": str(comment_author1.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author1.id}"
            },
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author2.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "jane_smith",
                    "url": f"{API_BASE}/author/{author2.id}",
                    "github": "https://github.com/jane_smith",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "This is great for testing",
                "contentType": "text/markdown",
                "published": str(comment_author2.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author2.id}"
            },
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author3.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "lara_croft",
                    "url": f"{API_BASE}/author/{author3.id}",
                    "github": "https://github.com/lara_croft",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Wow! This is such a nice comment for testing",
                "contentType": "text/markdown",
                "published": str(comment_author3.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author3.id}"
            },
        ]

        expected = get_comments_json(post, expected_comments)
        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)))

        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)

        expected_len = len(str(expected))
        res_data_len = len(str(res_data))
        self.assertEqual(expected_len, res_data_len,
            f"Expected response length to be {expected_len}")

        for comment in res_data["comments"]:
            self.assertTrue(str(comment) in str(expected),
                "Expected response does NOT contain:\n" + str(comment))

    def test_404_unmatching_authors(self):
        post = mixer.blend('socialDistribution.localpost')
        author = create_author(
            "John Doe",
            "johnDoe",
            "http://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment = create_comment(
            author,
            "text/markdown",
            "Cool post",
            post
        )

        response = self.client.get(reverse('api:post_comments', args=(author.id, post.id)))
        self.assertEqual(response.status_code, 404,
            "Expected 404 status code, but instead got" + str(response.status_code))

    def test_multi_comments_same_author(self):
        post = mixer.blend('socialDistribution.localpost')
        author = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment1 = create_comment(
            author,
            "text/markdown",
            "Cool post",
            post
        )

        comment2 = create_comment(
            author,
            "text/markdown",
            "Really cool post",
            post
        )

        comment3 = create_comment(
            author,
            "text/markdown",
            "Hi again folks",
            post
        )

        expected_comments = [
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": f"{API_BASE}/author/{author.id}",
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Cool post",
                "contentType": "text/markdown",
                "published": str(comment1.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment1.id}"
            },
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": f"{API_BASE}/author/{author.id}",
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Really cool post",
                "contentType": "text/markdown",
                "published": str(comment2.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment2.id}"
            },{
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": f"{API_BASE}/author/{author.id}",
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Hi again folks",
                "contentType": "text/markdown",
                "published": str(comment3.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment3.id}"
            },
        ]

        expected = get_comments_json(post, expected_comments)
        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)))

        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)

        expected_len = len(str(expected))
        res_data_len = len(str(res_data))
        self.assertEqual(expected_len, res_data_len,
            f"Expected response length to be {expected_len}")

        for comment in res_data["comments"]:
            self.assertTrue(str(comment) in str(expected),
                "Expected response does NOT contain:\n" + str(comment))
            
            
    def test_comment_multiple_authors_paginated(self):
        self.maxDiff = None
        post = mixer.blend('socialDistribution.localpost')
        page = 1
        size = 2
        author1 = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author2 = create_author(
            "Jane Smith",
            "jane_smith",
            "https://github.com/jane_smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author3 = create_author(
            "Lara Croft",
            "lara_croft",
            "https://github.com/lara_croft",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment_author1 = create_comment(
            author1,
            "text/markdown",
            "Hello there",
            post,
            timezone.now() + datetime.timedelta(minutes=1)
        )

        comment_author2 = create_comment(
            author2,
            "text/markdown",
            "This is great for testing",
            post,
            timezone.now() + datetime.timedelta(minutes=2)
        )

        comment_author3 =create_comment(
            author3,
            "text/markdown",
            "Wow! This is such a nice comment for testing",
            post,
            timezone.now() + datetime.timedelta(minutes=3)
        )

        expected_comments = [
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author3.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "lara_croft",
                    "url": f"{API_BASE}/author/{author3.id}",
                    "github": "https://github.com/lara_croft",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Wow! This is such a nice comment for testing",
                "contentType": "text/markdown",
                "published": str(comment_author3.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author3.id}"
            },
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author2.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "jane_smith",
                    "url": f"{API_BASE}/author/{author2.id}",
                    "github": "https://github.com/jane_smith",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "This is great for testing",
                "contentType": "text/markdown",
                "published": str(comment_author2.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author2.id}"
            }
        ]

        expected = get_comments_json(post, expected_comments, page, size)
        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)) + f'?page={page}&size={size}')

        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        

        expected_len = len(str(expected))
        res_data_len = len(str(res_data))
        self.assertEqual(expected_len, res_data_len,
            f"Expected response length to be {expected_len}")

        for comment in res_data["comments"]:
            self.assertTrue(str(comment) in str(expected),
                "Expected response does NOT contain:\n" + str(comment))
            
    def test_comment_multiple_authors_paginated_page_2(self):
        self.maxDiff = None
        post = mixer.blend('socialDistribution.localpost')
        page = 2
        size = 2
        author1 = create_author(
            "John Doe",
            "johnDoe",
            "https://github.com/johnDoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author2 = create_author(
            "Jane Smith",
            "jane_smith",
            "https://github.com/jane_smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author3 = create_author(
            "Lara Croft",
            "lara_croft",
            "https://github.com/lara_croft",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        comment_author1 = create_comment(
            author1,
            "text/markdown",
            "Hello there",
            post,
            timezone.now() + datetime.timedelta(minutes=1)
        )

        comment_author2 = create_comment(
            author2,
            "text/markdown",
            "This is great for testing",
            post,
            timezone.now() + datetime.timedelta(minutes=2)
        )

        comment_author3 =create_comment(
            author3,
            "text/markdown",
            "Wow! This is such a nice comment for testing",
            post,
            timezone.now() + datetime.timedelta(minutes=3)
        )

        expected_comments = [
            {
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": f"{API_BASE}/author/{author1.id}",
                    "host": f"{API_BASE}/",
                    "displayName": "johnDoe",
                    "url": f"{API_BASE}/author/{author1.id}",
                    "github": "https://github.com/johnDoe",
                    "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
                },
                "comment": "Hello there",
                "contentType": "text/markdown",
                "published": str(comment_author1.pub_date),
                "id": f"{API_BASE}/author/{post.author.id}/posts/{post.id}/comments/{comment_author1.id}"
            }
        ]

        expected = get_comments_json(post, expected_comments, page, size)
        response = self.client.get(reverse('api:post_comments', args=(post.author.id, post.id)) + f'?page={page}&size={size}')

        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        
        expected_len = len(str(expected))
        res_data_len = len(str(res_data))
        self.assertEqual(expected_len, res_data_len,
            f"Expected response length to be {expected_len}")

        for comment in res_data["comments"]:
            self.assertTrue(str(comment) in str(expected),
                "Expected response does NOT contain:\n" + str(comment))