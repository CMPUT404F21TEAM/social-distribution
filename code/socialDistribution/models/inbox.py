from django.core.exceptions import ValidationError
from django.db import models

class Inbox(models.Model):
    '''
    Inbox model:
        author          author associated with the inbox (primary key)
        posts           posts pushed to this inbox (M2M)
        followRequests  follow requests pushed to this inbox (M2M)
    '''
    author = models.OneToOneField(
        'Author', on_delete=models.CASCADE, primary_key=True)
    posts = models.ManyToManyField(
        'Post', related_name='pushed_posts', blank=True)
    follow_requests = models.ManyToManyField(
        'Author', related_name='follow_requests', blank=True)

    def has_req_from(self, author):
        """
        Returns True if the user has a request from a specific author, False otherwise 
        """
        return self.follow_requests.filter(pk=author.id).exists()

    def add_post(self, post):
        """
        Adds a pushed post
        """
        try:
            self.posts.add(post)
        except ValidationError:
            raise