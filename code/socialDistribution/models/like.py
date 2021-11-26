from django.db import models
from datetime import datetime, timezone
import timeago

from cmput404.constants import HOST, API_PREFIX


class Like(models.Model):
    '''
    Like model:
        id                  Auto-generated id
        author              Author who created the Like (reference to Author)
        object              Object related to the like (should be immplemented by child class)
    '''

    class Meta:
        # Django Software Foundation, "Abstract base classes", 2021-11-04,
        # https://docs.djangoproject.com/en/3.2/topics/db/models/#abstract-base-classes
        abstract = True

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    pub_date = models.DateTimeField(auto_now_add=True, blank=True)

    def when(self):
        '''
        Returns string describing when the like was created
        '''
        now = datetime.now(timezone.utc)
        return timeago.format(self.pub_date, now)

    def as_json(self):
        return {
            "type": "Like",
        }


class PostLike(Like):
    '''
    PostLike model:
        id                  Auto-generated id
        author              Like author (reference to Author)
        object              Post related to the like (reference to Post)
    '''

    class Meta:
        # Django Software Foundation, "UniqueConstraint", 2021-11-06,
        # https://docs.djangoproject.com/en/3.2/ref/models/constraints/#uniqueconstraint
        constraints = [
            # do not allow author to like same object more than once
            models.UniqueConstraint(fields=['author', 'object'], name='unique_post_like'),
        ]

    object = models.ForeignKey('LocalPost', on_delete=models.CASCADE, related_name="likes")


class CommentLike(Like):
    '''
    CommentLike model:
        id                  Auto-generated id
        author              Like author (reference to Author)
        object              Comment related to the like (reference to Comment)
    '''

    class Meta:
        # Django Software Foundation, "UniqueConstraint", 2021-11-06,
        # https://docs.djangoproject.com/en/3.2/ref/models/constraints/#uniqueconstraint
        constraints = [
            # do not allow author to like same object more than once
            models.UniqueConstraint(fields=['author', 'object'], name='unique_comment_like')
        ]

    object = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name="likes")
