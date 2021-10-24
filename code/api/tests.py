from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from mixer.backend.django import mixer
import json

from socialDistribution.models import Author


def create_author(username, displayName, githubUrl):
    return Author.objects.create(username=username, displayName=displayName, githubUrl=githubUrl)


class AuthorsViewTests(TestCase):

    def test_get_authors_basic(self):
        expected = json.dumps({"type": "authors", "items": []})
        response = self.client.get(reverse("api:authors"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)

    def test_get_authors_single(self):
        author = create_author(
            "user1",
            "John Doe",
            "https://github.com/johndoe"
        )
        expected = {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/author/1/",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "John Doe",
            "url": "http://127.0.0.1:8000/api/author/1/",
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
        author1 = create_author(
            "user1",
            "John Smith",
            "https://github.com/smith"
        )
        author2 = create_author(
            "user2",
            "Apple J Doe",
            "https://github.com/apple"
        )
        author3 = create_author(
            "user3",
            "Jane Smith G. Sr.",
            "https://github.com/another"
        )

        expected = [
            {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/author/1/",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "John Smith",
                "url": "http://127.0.0.1:8000/api/author/1/",
                "github": "https://github.com/smith",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/author/2/",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Apple J Doe",
                "url": "http://127.0.0.1:8000/api/author/2/",
                "github": "https://github.com/apple",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/author/3/",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Jane Smith G. Sr.",
                "url": "http://127.0.0.1:8000/api/author/3/",
                "github": "https://github.com/another",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            }
        ]

        response = self.client.get(reverse("api:authors"))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("type"), "authors")
        self.assertEqual(len(data.get("items")), 3, "Expected to recieve list of 3 authors")

        items = data.get("items")
        self.assertListEqual(items, expected)
