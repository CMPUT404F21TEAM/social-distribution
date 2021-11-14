from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from mixer.backend.django import mixer

from datetime import datetime, timedelta, timezone
from .models import *
from .builders import *


class AuthorTests(TestCase):
    """ Unit tests for Author. """

    def test_create_author(self):
        url = "http://notmyserver.com/author/839028403"

        author = Author.objects.create(url=url)

        id = author.id

        fetched = Author.objects.get(id=id)
        self.assertEqual(url, fetched.url)


class LocalAuthorTests(TestCase):
    """ Unit tests for LocalAuthor """

    def test_create_local_author(self):
        author = mixer.blend(LocalAuthor)

        fetched = LocalAuthor.objects.get(username=author.username)

        self.assertEqual(author.id, fetched.id)
        self.assertEqual(author.user, fetched.user)
        self.assertEqual(author.username, fetched.username)
        self.assertEqual(author.displayName, fetched.displayName)
        self.assertEqual(author.githubUrl, fetched.githubUrl)
        self.assertEqual(author.profileImageUrl, fetched.profileImageUrl)
        self.assertEqual(f"http://127.0.0.1:8000/api/author/{author.id}", fetched.url)

        vanilla_author = Author.objects.get(id=author.id)
        self.assertEqual(f"http://127.0.0.1:8000/api/author/{author.id}", vanilla_author.url)



class PostTest(TestCase):
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
    
class SharePostTest(TestCase):
    def test_share_public_post(self):
        visibility = LocalPost.Visibility.PUBLIC
        post = PostBuilder().visibility(visibility).build()
        self.client.post('socialDistribution:sharePost', id=post.id)
        self.assertEquals(LocalPost.objects.latest("published").visibility, LocalPost.Visibility.PUBLIC)
        
    def test_share_private_post(self):
        '''
            sharing a private post shouldn't be possible
        '''
        visibility = LocalPost.Visibility.PRIVATE
        post = PostBuilder().visibility(visibility).build()
        self.client.post('socialDistribution:sharePost', id=post.id)
        self.assertEquals(LocalPost.objects.latest("published"), post)


class CommentModelTests(TestCase):

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
