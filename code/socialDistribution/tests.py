from django.test import TestCase
from mixer.backend.django import mixer
from datetime import timedelta


from .models import *
# Create your tests here.

class CommentModelTests(TestCase):

    def test_when_just_now (self):
        '''
            comment.when() returns just now right after post creation
        '''
        author = mixer.blend(Author)
        post = mixer.blend(Post, author = author)
        comment = mixer.blend(Comment, author=author, post=post, pub_date = datetime.now(timezone.utc) )

        self.assertIs( comment.when() == 'just now', True)

    def test_when_10_seconds (self):
        '''
            comment.when() returns 10 seconds ago after the time has passed
        '''
        author = mixer.blend(Author)
        post = mixer.blend(Post, author = author)

        pub_date = datetime.now(timezone.utc) - timedelta(seconds=10)
        comment = mixer.blend(Comment, author=author, post=post, pub_date = pub_date  )

        self.assertIs( comment.when() == '10 seconds ago', True)



