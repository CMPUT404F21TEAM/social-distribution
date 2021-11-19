# python manage.py test api.tests.test_followers

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from mixer.backend.django import mixer
import json

from socialDistribution.models import LocalAuthor, Author, Follow

# Documentation and code samples taken from the following references:
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/intro/tutorial05/
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/topics/testing/overview/
# Python Software Foundation, https://docs.python.org/3/library/unittest.html


class FollowersViewTests(TestCase):

    def test_get_followers(self):

        author = mixer.blend(LocalAuthor)

        expected = json.dumps({"type": "followers", "items": []})
        kwargs = {"author_id": author.id}
        response = self.client.get(reverse("api:followers", kwargs=kwargs))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, expected)
