# python manage.py test api

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from mixer.backend.django import mixer
import json
import logging

from socialDistribution.models import LocalAuthor
from .utilities import create_author as create_author_with_auth, get_basic_auth

# Documentation and code samples taken from the following references:
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/intro/tutorial05/
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/topics/testing/overview/
# Python Software Foundation, https://docs.python.org/3/library/unittest.html


def create_author(username, displayName, githubUrl, profileImageUrl):
    user = mixer.blend(User, username=username)
    author = LocalAuthor.objects.create(username=username, displayName=displayName, githubUrl=githubUrl, user=user, profileImageUrl=profileImageUrl)
    return LocalAuthor.objects.get(id=author.id) # refetch to get the generated ID


class AuthorsViewTests(TestCase):

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

    def test_get_authors_basic(self):
        expected = json.dumps({"type": "authors", "items": []})
        response = self.client.get(reverse("api:authors"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)

    def test_get_authors_single(self):
        author = create_author(
            "user1",
            "John Doe",
            "https://github.com/johndoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        expected = {
            "type": "author",
            "id": author.get_url_id(),
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "John Doe",
            "url": author.get_url_id(),
            "github": "https://github.com/johndoe",
            "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        }

        response = self.client.get(reverse("api:authors"))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("type"), "authors")
        self.assertEqual(len(data.get("items")), 1)

        author = data.get("items")[0]
        self.assertDictEqual(author, expected)

    def test_get_authors_multiple(self):
        self.maxDiff = None
        user = mixer.blend(User)

        author1 = create_author(
            "user1",
            "John Smith",
            "https://github.com/smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author2 = create_author(
            "user2",
            "Apple J Doe",
            "https://github.com/apple",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        author3 = create_author(
            "user3",
            "Jane Smith G. Sr.",
            "https://github.com/another",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        expected = [
            {
                "type": "author",
                "id": author1.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "John Smith",
                "url": author1.get_url_id(),
                "github": "https://github.com/smith",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            {
                "type": "author",
                "id": author2.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Apple J Doe",
                "url": author2.get_url_id(),
                "github": "https://github.com/apple",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            {
                "type": "author",
                "id": author3.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Jane Smith G. Sr.",
                "url": author3.get_url_id(),
                "github": "https://github.com/another",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            }
        ]

        response = self.client.get(reverse("api:authors"))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("type"), "authors")
        self.assertEqual(len(data.get("items")), 3,
                         "Expected to recieve list of 3 authors")

        items = data.get("items")
        self.assertListEqual(items, expected)

    def test_get_authors_multiple_paginated(self):
        self.maxDiff = None

        user = mixer.blend(User)

        author1 = create_author(
            "user1",
            "John Smith",
            "https://github.com/smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )
        author2 = create_author(
            "user2",
            "Apple J Doe",
            "https://github.com/apple",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )
        author3 = create_author(
            "user3",
            "Jane Smith G. Sr.",
            "https://github.com/another",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        expected = [
            {
                "type": "author",
                "id": author1.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "John Smith",
                "url": author1.get_url_id(),
                "github": "https://github.com/smith",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            {
                "type": "author",
                "id": author2.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Apple J Doe",
                "url": author2.get_url_id(),
                "github": "https://github.com/apple",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
        ]

        response = self.client.get(reverse("api:authors") + '?page=1&size=2')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("type"), "authors")
        self.assertEqual(len(data.get("items")), 2,
                         "Expected to recieve list of 2 authors")

        items = data.get("items")
        self.assertListEqual(items, expected)

    def test_get_authors_multiple_paginated_page_2(self):
        self.maxDiff = None
        page = 2
        size = 2
        user = mixer.blend(User)
        author1 = create_author(
            "user1",
            "John Smith",
            "https://github.com/smith",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )
        author2 = create_author(
            "user2",
            "Apple J Doe",
            "https://github.com/apple",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )
        author3 = create_author(
            "user3",
            "Jane Smith G. Sr.",
            "https://github.com/another",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )

        expected = [
            {
                "type": "author",
                "id": author3.get_url_id(),
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Jane Smith G. Sr.",
                "url": author3.get_url_id(),
                "github": "https://github.com/another",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            }
        ]

        response = self.client.get(reverse("api:authors") + f'?page={page}&size={size}')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("type"), "authors")
        self.assertEqual(len(data.get("items")), 1,
                         "Expected to recieve list of 1 authors")

        items = data.get("items")
        self.assertListEqual(items, expected)

    def test_get_author(self):
        author = create_author(
            "user1",
            "John Doe",
            "https://github.com/johndoe",
            "https://i.imgur.com/k7XVwpB.jpeg"
        )
        expected = {
            "type": "author",
            "id": author.get_url_id(),
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "John Doe",
            "url": author.get_url_id(),
            "github": "https://github.com/johndoe",
            "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
        }
        response = self.client.get(
            reverse("api:author", kwargs={"author_id": author.id}))

        actual = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(actual, expected)

    def test_post_author(self):
        author = create_author_with_auth()

        data = {
            "displayName": "Lara Croft",
            "github": "https://github.com/croft",
            "profileImage": "https://lh4.googleusercontent.com/-qu9N5sJB6Uc/TXdJsP9YGOI/AAAAAAAAAZs/AIta6Ea3XVU/s1600/TR3.jpg"
        }

        # make post to update author object
        response = self.client.post(
            reverse("api:author", kwargs={"author_id": author.id}),
            content_type="application/json",
            data=json.dumps(data),
            **get_basic_auth(author)
        )

        self.assertEqual(200, response.status_code)

        actual = response.json()
        self.assertEqual(actual["displayName"], data["displayName"])
        self.assertEqual(actual["github"], data["github"])
        self.assertEqual(actual["profileImage"], data["profileImage"])

    def test_no_auth(self):
        author = create_author_with_auth()

        data = {
            "displayName": "Lara Croft",
            "github": "https://github.com/croft",
            "profileImage": "https://lh4.googleusercontent.com/-qu9N5sJB6Uc/TXdJsP9YGOI/AAAAAAAAAZs/AIta6Ea3XVU/s1600/TR3.jpg"
        }

        # make post to update author object
        response = self.client.post(
            reverse("api:author", kwargs={"author_id": author.id}),
            content_type="application/json",
            data=json.dumps(data)
        )

        self.assertEqual(401, response.status_code)
