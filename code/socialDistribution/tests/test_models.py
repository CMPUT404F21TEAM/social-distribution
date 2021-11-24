# python manage.py test api.tests.tests.test_models

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test.testcases import LiveServerTestCase, LiveServerThread
from mixer.backend.django import mixer

from datetime import datetime, timedelta, timezone
import logging

from socialDistribution.models import *
from socialDistribution.builders import *
from cmput404.constants import API_BASE

class AuthorTests(LiveServerTestCase):
    """ Unit tests for Author. """

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

    def test_create_author(self):
        url = "http://notmyserver.com/author/839028403"

        author = Author.objects.create(url=url)

        id = author.id

        fetched = Author.objects.get(id=id)
        self.assertEqual(url, fetched.url)

    # a bit more work needed to get this to correctly find the debug server
    # def test_get_author_json(self):
    #     # makes an API call, server must be running
    #     local = mixer.blend(LocalAuthor)
    #     remote = Author.objects.get(id=local.id)

    #     print(self.live_server_url)
    #     print(socket.gethostname())
    #     author_json = remote.as_json()
    #     print(author_json)


class LocalAuthorTests(TestCase):
    """ Unit tests for LocalAuthor """

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

    def test_create_local_author(self):
        author = mixer.blend(LocalAuthor)

        fetched = LocalAuthor.objects.get(username=author.username)

        self.assertEqual(author.id, fetched.id)
        self.assertEqual(author.user, fetched.user)
        self.assertEqual(author.username, fetched.username)
        self.assertEqual(author.displayName, fetched.displayName)
        self.assertEqual(author.githubUrl, fetched.githubUrl)
        self.assertEqual(author.profileImageUrl, fetched.profileImageUrl)
        self.assertEqual(f"{API_BASE}/author/{author.id}", fetched.url)

        vanilla_author = Author.objects.get(id=author.id)
        self.assertEqual(f"{API_BASE}/author/{author.id}", vanilla_author.url)


class PostTest(TestCase):

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

    def test_post_is_public(self):
        visibility = LocalPost.Visibility.FRIENDS
        post = PostBuilder().visibility(visibility).build()
        self.assertFalse(post.is_public())

    def test_post_is_friends(self):
        visibility = LocalPost.Visibility.FRIENDS
        post = PostBuilder().visibility(visibility).build()
        self.assertTrue(post.is_friends())

    def test_post_when(self):
        time = datetime.now(timezone.utc)
        post = PostBuilder().pub_date(time).build()
        self.assertTrue(post.when() == 'just now')

    def test_post_total_likes(self):
        likes = 25
        post = PostBuilder().likes(likes).build()
        self.assertTrue(post.total_likes() == likes)

    # TODO test all PostQuerySet methods


class CommentModelTests(TestCase):

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

    def test_when_just_now(self):
        '''
            comment.when() returns just now right after post creation
        '''
        author = mixer.blend(LocalAuthor)
        post = mixer.blend(LocalPost, author=author)
        comment = mixer.blend(Comment, author=author, post=post, pub_date=datetime.now(timezone.utc))

        self.assertIs(comment.when() == 'just now', True)

    def test_when_10_seconds(self):
        '''
            comment.when() returns 10 seconds ago after the time has passed
        '''
        author = mixer.blend(LocalAuthor)
        post = mixer.blend(LocalPost, author=author)

        pub_date = datetime.now(timezone.utc) - timedelta(seconds=10)
        comment = mixer.blend(Comment, author=author, post=post, pub_date=pub_date)

        self.assertIs(comment.when() == '10 seconds ago', True)


class LikeTests(TransactionTestCase):
    """ Unit tests for Likes, PostLikes and CommentLikes. """

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

    def test_post_like(self):
        """ Test successfully liking a Post """

        post = mixer.blend(LocalPost)
        author = mixer.blend(Author)

        # like a post
        post.likes.create(author=author)
        self.assertEqual(1, post.likes.count())
        self.assertEqual(author, post.likes.first().author)

    def test_comment_like(self):
        """ Test successfully liking a Comment """

        comment = mixer.blend(Comment)
        author = mixer.blend(Author)

        # like a comment
        comment.likes.create(author=author)
        self.assertEqual(1, comment.likes.count())
        self.assertEqual(author, comment.likes.first().author)

    def test_no_author(self):
        """ Test creating a Like with no Author """

        post = mixer.blend(LocalPost)
        with self.assertRaises(IntegrityError):
            post.likes.create()

    def test_no_post(self):
        """ Test creating a like with no object """
        with self.assertRaises(IntegrityError):
            author = mixer.blend(Author)
            PostLike.objects.create(author=author)

        with self.assertRaises(IntegrityError):
            author = mixer.blend(Author)
            CommentLike.objects.create(author=author)

    def test_double_like(self):
        """ Test liking a post multiple times """

        post = mixer.blend(LocalPost)
        author = mixer.blend(Author)

        # add a like
        like = post.likes.create(author=author)
        self.assertEqual(1, post.likes.count())

        # adding another like should raise an error
        with self.assertRaisesMessage(IntegrityError, "UNIQUE constraint failed"):
            post.likes.create(author=author)

        # should be able to remove and like again
        like.delete()
        self.assertEqual(0, post.likes.count())
        post.likes.create(author=author)
        self.assertEqual(1, post.likes.count())
