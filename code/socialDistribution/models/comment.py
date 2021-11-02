from django.db import models
from datetime import *
import timeago

from cmput404.constants import HOST, API_PREFIX

class Comment(models.Model):
    '''
    Comment model:
        author              Comment author (reference to author)
        content_type        Markdown or Text
        comment             Comment content (markdown or text)
        pub_date            Published date (datetime)
        post                Post related to the comment (reference to post)
        id                  Auto-generated id
    '''
    class CommentContentType(models.TextChoices):
        PLAIN = 'PL', 'text/plain'
        MARKDOWN = 'MD', 'text/markdown'

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    content_type = models.CharField(
        max_length=2,
        choices=CommentContentType.choices
    )
    comment = models.CharField(max_length=200)

    post = models.ForeignKey('Post', on_delete=models.CASCADE)
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
            "id": f"http://{HOST}/{API_PREFIX}/author/{self.post.author.id}/posts/{self.post.id}/comments/{self.id}",
        }