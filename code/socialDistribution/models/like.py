from django.db import models
from datetime import *
import timeago

from cmput404.constants import HOST, API_PREFIX


class PostLike(models.Model):
    '''
    Like model:
        id                  Auto-generated id
        author              Like author (reference to Author)
        post                Post related to the like (reference to Post)
    '''

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    object = models.ForeignKey('Post', on_delete=models.CASCADE, related_name="likes")

    pub_date = models.DateTimeField(auto_now_add=True, blank=True)

    def when(self):
        '''
        Returns string describing when the like was created
        '''
        now = datetime.now(timezone.utc)
        return timeago.format(self.pub_date, now)

    def as_json(self):
        return {
            "type": "like",
        }


class CommentLike(models.Model):
    '''
    Like model:
        id                  Auto-generated id
        author              Like author (reference to Author)
        object              Comment related to the like (reference to Comment)
    '''

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    object = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name="likes")

    pub_date = models.DateTimeField(auto_now_add=True, blank=True)

    def when(self):
        '''
        Returns string describing when the like was created
        '''
        now = datetime.now(timezone.utc)
        return timeago.format(self.pub_date, now)

    def as_json(self):
        return {
            "type": "like",
        }
