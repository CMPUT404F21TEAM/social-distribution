# python manage.py test api.tests.test_utilities

from django.test import TestCase

import datetime
from datetime import timezone
import logging

from api.utility import makeInboxPost


class UtilityYests(TestCase):

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

    def test_creat_post_alt_iso_time_format(self):
        post_json = {
            "type": "post",
            "title": "DID YOU READ MY POST YET?",
            "id": "http://127.0.0.1:5454/author/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/999999983dda1e11db47671c4a3bbd9e",
            "source": "http://lastplaceigotthisfrom.com/posts/yyyyy",
            "origin": "http://whereitcamefrom.com/posts/zzzzz",
            "description": "Whatever",
            "contentType": "text/plain",
            "content": "Are you even reading my posts Arjun?",
            "author": {
                  "type": "author",
                  "id": "http://127.0.0.1:5454/author/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
                  "host": "http://127.0.0.1:5454/",
                  "displayName": "Lara Croft",
                  "url": "http://127.0.0.1:5454/author/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
                  "github": "http://github.com/laracroft",
                  "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
            },
            "categories": ["web", "tutorial"],
            "comments": "http://127.0.0.1:5454/author/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/de305d54-75b4-431b-adb2-eb6b9e546013/comments",
            "published": "2010-05-08T23:41:54.000Z",  # here
            "visibility": "FRIENDS",
            "unlisted": False
        }

        expected = datetime.datetime(2010, 5, 8, 23, 41, 54, tzinfo=timezone.utc)
        post = makeInboxPost(post_json)

        self.assertEqual(post.published, expected)
