# python manage.py test api.tests.tests.test_views

from django.test import TestCase

import logging

from socialDistribution.models import *
from socialDistribution.builders import *


class SharePostTest(TestCase):

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

    def test_share_public_post(self):
        visibility = LocalPost.Visibility.PUBLIC
        post = PostBuilder().visibility(visibility).build()
        self.client.post('socialDistribution:share-post', id=post.id)

        latestPost = LocalPost.objects.latest("published")
        self.assertEquals(latestPost.visibility, LocalPost.Visibility.PUBLIC)
        self.assertEqual(latestPost.origin, post.get_id())
        self.assertEqual(latestPost.source, post.get_id())

    def test_share_public_post_twice(self):
        visibility = LocalPost.Visibility.PUBLIC
        post = PostBuilder().visibility(visibility).build()

        self.client.post('socialDistribution:share-post', id=post.id)
        middlePost = LocalPost.objects.latest("published")
        self.client.post('socialDistribution:share-post', id=middlePost.id)
        latestPost = LocalPost.objects.latest("published")

        self.assertEquals(latestPost.visibility, LocalPost.Visibility.PUBLIC)
        self.assertEqual(latestPost.origin, post.get_id())
        self.assertEqual(latestPost.source, middlePost.get_id())

    def test_share_private_post(self):
        '''
            sharing a private post shouldn't be possible
        '''
        visibility = LocalPost.Visibility.PRIVATE
        post = PostBuilder().visibility(visibility).build()
        self.client.post('socialDistribution:share-post', id=post.id)

        latestPost = LocalPost.objects.latest("published")
        self.assertEquals(latestPost, post)
        self.assertEqual(latestPost.origin, post.get_id())
        self.assertEqual(latestPost.source, post.get_id())
