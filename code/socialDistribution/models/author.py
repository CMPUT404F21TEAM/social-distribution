
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, manager
from datetime import *
import timeago

from cmput404.constants import HOST, API_PREFIX


class Author(models.Model):
    '''
    Author model:
        user                Author's corresponding Django User (text)
        username            Author's username (text)
        displayName         Author's displayName (text)
        githubUrl           Author's github url (text)
        profileImageUrl     Author's profile image url (text)

        posts               Posts created by the author
        friend_requests     fksdjfskl;jfaskdf
        followers           Author's followers (array)
    '''
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, default='', unique=True)
    displayName = models.CharField(max_length=50)
    githubUrl = models.CharField(max_length=50, null=True)
    profileImageUrl = models.CharField(max_length=50, null=True)

    followers = models.ManyToManyField('Author', blank=True)

    def has_follower(self, author):
        """
        Returns True if an author follows a user, False otherwise 
        """
        return self.followers.filter(pk=author.id).exists()

    def is_friends_with(self, author):
        """
        Returns True if an author is friends wtih a user, False otherwise 
        """
        return self.followers.filter(pk=author.id).exists() and \
            author.followers.filter(pk=self.id).exists()

    # depreciated
    # def get_visible_posts_to(self, author):
    #     """ 
    #         @depreciated due to too much coupling between posts and author
    #         author to author method yet still relies on Post

    #         Returns valid posts
    #     """
    #     visible_posts = None
    #     if author.id == self.id:
    #         visible_posts = Post.objects.filter(author__pk=author.id)
    #     elif self.is_friends_with(author):
    #         visible_posts = Post.objects.filter(
    #             author__pk=self.id).exclude(visibility=Post.PRIVATE)
    #     else:
    #         visible_posts = Post.objects.filter(
    #             author__pk=self.id, visibility=Post.PUBLIC)

    #     return visible_posts.order_by('-pub_date')[:]

    def __str__(self):
        return self.displayName

    def as_json(self):
        return {
            "type": "author",
            # ID of the Author
            "id": f"http://{HOST}/{API_PREFIX}/author/{self.id}",
            # the home host of the author
            "host": f'http://{HOST}/{API_PREFIX}/',
            # the display name of the author
            "displayName": self.displayName,
            # url to the authors profile
            "url": f"http://{HOST}/{API_PREFIX}/author/{self.id}",
            # HATEOS url for Github API
            "github": self.githubUrl,
            # Image from a public domain
            # #TODO
            "profileImage": self.profileImageUrl
        }
