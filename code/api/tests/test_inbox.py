# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from mixer.backend.django import mixer
from datetime import datetime, timezone

from socialDistribution.models import LocalAuthor, LocalPost, Comment
from api.models import Node
from cmput404.constants import *
import base64

# Documentation and code samples taken from the following references:
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/intro/tutorial05/
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/topics/testing/overview/
# Python Software Foundation, https://docs.python.org/3/library/unittest.html


def create_author(id, username, displayName, githubUrl):
    user = mixer.blend(User, username=username)
    author = LocalAuthor.objects.create(
        id=id, username=username, displayName=displayName, githubUrl=githubUrl, user=user)
    return author


class InboxViewTests(TestCase):

    def setUp(self):
        Node.objects.create(host=HOST, username='testclient', password='testpassword!', remote_credentials=False)
        self.basicAuthHeaders = {
            'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(b'testclient:testpassword!').decode("ascii"),
        }

    def test_post_local_follow(self):
        author1 = create_author(
            1,
            "user1",
            "Greg Johnson",
            "http://github.com/gjohnson"
        )
        author2 = create_author(
            2,
            "user2",
            "Lara Croft",
            "http://github.com/laracroft"
        )

        body = {
            "type": "follow",
            "summary": "Greg wants to follow Lara",
            "actor": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/author/1",
                "url": "http://127.0.0.1:8000/api/author/1",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Greg Johnson",
                "github": "http://github.com/gjohnson",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            "object": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/author/2",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Lara Croft",
                "url": "http://127.0.0.1:8000/api/author/2",
                "github": "http://github.com/laracroft",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            }
        }

        response = self.client.post(
            reverse("api:inbox", kwargs={"author_id": 2}),
            content_type="application/json",
            **self.basicAuthHeaders,
            data=body
        )

        self.assertEqual(response.status_code, 200)

        query_set = author2.follow_requests.all()
        self.assertEqual(query_set.count(), 1)

        follow_request_author = author2.follow_requests.first()
        follow_request_author = LocalAuthor.objects.get(id=follow_request_author.id)
        self.assertEqual(follow_request_author, author1)

    def test_post_local_post(self):
        # NOTE: This test is very basic. More work needed on this endpoint.

        author1 = create_author(
            1,
            "user1",
            "Greg Johnson",
            "http://github.com/gjohnson"
        )
        author2 = create_author(
            2,
            "user2",
            "Lara Croft",
            "http://github.com/laracroft"
        )

        # Create a post from author1
        dummy_post = mixer.blend(
            LocalPost, 
            id=1, 
            author=author1,
            content="testcontent".encode("utf-8")
        )

        body = dummy_post.as_json()

        # Send the post to author 2
        response = self.client.post(
            reverse("api:inbox", kwargs={"author_id": 2}),
            content_type="application/json",
            **self.basicAuthHeaders,
            data=body
        )

        self.assertEqual(response.status_code, 200)

        # Check the received posts of author2
        query_set = author2.inbox_posts.all()
        self.assertEqual(query_set.count(), 1)

        inbox_post = author2.inbox_posts.first()
        self.assertEqual(inbox_post.title, dummy_post.title)
        self.assertEqual(inbox_post.description, dummy_post.description)
        self.assertEqual(inbox_post.decoded_content, dummy_post.decoded_content)
    
    def test_post_comment_local_like(self):
        '''
            Test liking a comment from a local author
        '''
        author1 = create_author(
            1,
            "user1",
            "Greg Johnson",
            "http://github.com/gjohnson"
        ) 

        post = mixer.blend(LocalPost, author = author1)
        comment = mixer.blend(Comment, author=author1, post=post, pub_date = datetime.now(timezone.utc) )

        body = {
                   "@context": "https://www.w3.org/ns/activitystreams",
                    "summary": f"{author1.username} Likes your post",         
                    "type": "like",
                    "author": author1.as_json(),
                    "object":f"http://{HOST}/author/{post.author.id}/posts/{post.id}/comments/{comment.id}"
        }

        response = self.client.post(
            reverse("api:inbox", kwargs={"author_id": 1}),
            content_type="application/json",
            **self.basicAuthHeaders,
            data=body
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.total_likes(), 1)
        liker = comment.likes.all()[0]
        self.assertEqual(liker.id, author1.id)

    def test_post_like(self):
        author = create_author(
            1,
            "user1",
            "Greg Johnson",
            "http://github.com/gjohnson"
        )
        post = mixer.blend(LocalPost, id=1, author=author)

        body = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": "Diego Becerra Likes your post",
            "type": "like",
            "author": {
                "type": "author",
                "id": "http://remote.com/author/432423432",
                "host": "http://remote.com/author/432423432",
                "displayName": "Diego Becerra",
                "url": "http://remote.com/author/432423432",
                "github": "http://github.com/diego",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            "object": "http://127.0.0.1:5454/author/1/posts/1"
        }

        # Send the like to author
        response = self.client.post(
            reverse("api:inbox", kwargs={"author_id": 1}),
            content_type="application/json",
            **self.basicAuthHeaders,
            data=body
        )

        self.assertEqual(response.status_code, 200)
        
        # Check that the post received a like
        post = LocalPost.objects.get(id=1)
        self.assertEqual(1, post.likes.count())

        # Check that the like was from the right author
        like = post.likes.first()
        self.assertEqual("http://remote.com/author/432423432", like.author.url)
