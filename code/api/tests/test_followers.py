# python manage.py test api.tests.test_followers

from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from mixer.backend.django import mixer

import json
import logging
import base64

from socialDistribution.models import LocalAuthor, Author, Follow
from api.models import Node
from cmput404.constants import HOST

# Documentation and code samples taken from the following references:
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/intro/tutorial05/
# Django Software Foundation, https://docs.djangoproject.com/en/3.2/topics/testing/overview/
# Python Software Foundation, https://docs.python.org/3/library/unittest.html


class FollowersSingleViewTests(TestCase):
    """ Test the Followers API endpoint. This test suite runs a test server on port 8000,
        which means the dev server cannot also be running on the same port. 
    """

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
        Node.objects.create(host=HOST, username='testclient', password='testpassword!', remote_credentials=False)
        self.basicAuthHeaders = {
            'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(b'testclient:testpassword!').decode("ascii"),
        }

    def test_get(self):
        object = mixer.blend(LocalAuthor)
        object = LocalAuthor.objects.get(id=object.id)  # refetch to get the proper url
        actor = mixer.blend(LocalAuthor)
        actor = LocalAuthor.objects.get(id=actor.id)  # refetch to get the proper url

        object.follows.create(actor=actor)

        kwargs = {"author_id": object.id, "foreign_author_id": actor.url}
        request_url = reverse("api:followers-single", kwargs=kwargs)
        response = self.client.get(request_url)

        expected = actor.as_json()
        actual = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected, actual)

    def test_get_404(self):
        object = mixer.blend(LocalAuthor)
        object = LocalAuthor.objects.get(id=object.id)  # refetch to get the proper url
        actor = mixer.blend(LocalAuthor)
        actor = LocalAuthor.objects.get(id=actor.id)  # refetch to get the proper url

        kwargs = {"author_id": object.id, "foreign_author_id": actor.url}
        request_url = reverse("api:followers-single", kwargs=kwargs)
        response = self.client.get(request_url)

        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        object = mixer.blend(LocalAuthor)
        object = LocalAuthor.objects.get(id=object.id)  # refetch to get the proper url
        actor = mixer.blend(LocalAuthor)
        actor = LocalAuthor.objects.get(id=actor.id)  # refetch to get the proper url

        object.follows.create(actor=actor)
        self.assertEqual(1, object.follows.count())
        self.assertEqual(actor.url, object.follows.first().actor.url)

        # create follower and check that it's there when GET
        kwargs = {"author_id": object.id, "foreign_author_id": actor.url}
        request_url = reverse("api:followers-single", kwargs=kwargs)
        response = self.client.get(request_url)

        expected = actor.as_json()
        actual = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected, actual)

        # now DELETE and make sure it's gone when GET
        kwargs = {"author_id": object.id, "foreign_author_id": actor.url}
        request_url = reverse("api:followers-single", kwargs=kwargs)
        response = self.client.delete(request_url)

        self.assertEqual(204, response.status_code)
        self.assertEqual(b"", response.content)
        self.assertEqual(0, object.follows.count())

    def test_put(self):
        object = mixer.blend(LocalAuthor)
        object = LocalAuthor.objects.get(id=object.id)
        actor = mixer.blend(LocalAuthor)
        actor = LocalAuthor.objects.get(id=actor.id)

        self.assertEqual(0, object.follows.count())

        kwargs = {"author_id": object.id, "foreign_author_id": actor.url}
        
        request_url = reverse("api:followers-single", kwargs=kwargs)
        
        response = self.client.put(
            request_url,
            content_type="application/json",
            **self.basicAuthHeaders,
            data=actor.as_json()
        )

        expected = actor.as_json()
        actual = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, actual)

        self.assertEqual(1, object.follows.count())

        try:
            object.follows.get(actor=actor)
        
        except (Author.DoesNotExist, LocalAuthor.DoesNotExist):
            self.fail(f"Follower not returned by query after PUT")

    def test_put_404(self):
        object = mixer.blend(LocalAuthor)
        object = LocalAuthor.objects.get(id=object.id)
        deleted_obj_id = object.id
        object.delete()

        with self.assertRaises(LocalAuthor.DoesNotExist) as cm:
            LocalAuthor.objects.get(id=deleted_obj_id)

        actor = mixer.blend(LocalAuthor)
        actor = LocalAuthor.objects.get(id=actor.id)

        kwargs = {"author_id": deleted_obj_id, "foreign_author_id": actor.url}
        
        request_url = reverse("api:followers-single", kwargs=kwargs)
        
        response = self.client.put(
            request_url,
            content_type="application/json",
            **self.basicAuthHeaders,
            data=actor.as_json()
        )

        self.assertEqual(404, response.status_code)


class FollowersViewTests(TestCase):

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

    def test_get_followers_empty(self):

        author = mixer.blend(LocalAuthor)

        expected = {"type": "followers", "items": []}
        kwargs = {"author_id": author.id}
        response = self.client.get(reverse("api:followers", kwargs=kwargs))

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected)

    def test_get_followers(self):

        author1 = mixer.blend(LocalAuthor)
        author2 = mixer.blend(LocalAuthor)
        author3 = mixer.blend(LocalAuthor)

        author1 = LocalAuthor.objects.get(id=author1.id)
        author2 = LocalAuthor.objects.get(id=author2.id)
        author3 = LocalAuthor.objects.get(id=author3.id)

        author1.follows.create(actor=author2)
        author1.follows.create(actor=author3)

        expected = {"type": "followers", "items": [author2.as_json(), author3.as_json()]}
        kwargs = {"author_id": author1.id}
        response = self.client.get(reverse("api:followers", kwargs=kwargs))

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected)