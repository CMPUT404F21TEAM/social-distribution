from django.db import models
from datetime import *
import timeago
import uuid

from cmput404.constants import API_BASE, STRING_MAXLEN, URL_MAXLEN

class Comment(models.Model):
    '''
    Comment model:
        id                  Auto-generated id
        author              Comment author (reference to LocalAuthor)
        content_type        Markdown or Text
        comment             Comment content (markdown or text)
        pub_date            Published date (datetime)
        post                Post related to the comment (reference to post)
        likes               Likes created by Authors that liked this comment
    '''

    class CommentContentType(models.TextChoices):
        PLAIN = 'PL', 'text/plain'
        MARKDOWN = 'MD', 'text/markdown'

    # Django Software Foundation, https://docs.djangoproject.com/en/dev/ref/models/fields/#uuidfield
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    content_type = models.CharField(
        max_length=STRING_MAXLEN,
        choices=CommentContentType.choices,
        default=CommentContentType.PLAIN
    )
    comment = models.CharField(max_length=STRING_MAXLEN)

    post = models.ForeignKey('LocalPost', on_delete=models.CASCADE)
    pub_date = models.DateTimeField()

    def when(self):
        '''
        Returns string describing when the comment was created
        '''
        now = datetime.now(timezone.utc)
        return timeago.format(self.pub_date, now)

    def as_json(self):
        return {
            "type": "comment",
            "author": self.author.as_json(),
            "comment": self.comment,
            "contentType": "text/markdown",
            "published": str(self.pub_date),
            "id": f"{API_BASE}/author/{self.post.author.id}/posts/{self.post.id}/comments/{self.id}",
        }

    def total_likes(self):
        '''
            Returns total likes
        '''
        return self.likes.count()