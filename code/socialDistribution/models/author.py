from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from datetime import *

from cmput404.constants import HOST, API_PREFIX


class Author(models.Model):
    """ Author model which represents all authors. 

        All authors that interact with the application will be stored as an author. That is, 
        the Author model can store both remote and local authors. Methods on an Author instance primarily 
        rely on API calls to get the data corresponding to the author from a remote server.

        In the future, caching can be used with this model to reduce the number of API calls being sent out.

        When a local author is created, it must be re-fetched from the database in order to access the auto-generated author.url attribute.
    """

    url = models.URLField()

    def as_json(self):
        # This method is an example, not yet implemented
        # Makes a GET request to URL to get the Author data
        # The LocalAuthor method will override this, making it more efficient by fetching data
        # straight from the database instead of an HTTP request
        pass


class LocalAuthor(Author):
    ''' LocalAuthor model which represents an author hosted on the local server.

    Any authors hosted on the local server will be stored as a LocalAuthor instance. This class overrides
    methods defined in Author to provide more efficient, local access (no API) to author data.

    LocalAuthor model:
        user                Author's corresponding Django User (text)
        username            Author's username (text)
        displayName         Author's displayName (text)
        githubUrl           Author's github url (text)
        profileImageUrl     Author's profile image url (text)

        posts               Posts created by the author
        followers           Followers of the author (Collection of LocalAuthor objects)

        friend_requests     Authors who have requested to follow author (Collection of LocalAuthor objects)
        inbox_posts         Posts sent to the inbox of the author
    '''

    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True, blank=False)
    displayName = models.CharField(max_length=50)
    githubUrl = models.CharField(max_length=50, null=True)
    profileImageUrl = models.CharField(max_length=50, null=True)

    followers = models.ManyToManyField('LocalAuthor', blank=True)

    follow_requests = models.ManyToManyField('LocalAuthor', related_name="follow_requests_reverse")
    inbox_posts = models.ManyToManyField('Post')

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        self._set_url()

    def _set_url(self):
        """ Sets the URL of the author to be "http://{HOST}/{API_PREFIX}/author/{self.id}" if one was not set when created. This 
            sets the URL attribute of all local authors.
        """
        # Clark, https://stackoverflow.com/users/10424244/clark, "Django - How to get self.id when saving a new object?",
        # 2021-02-19, https://stackoverflow.com/a/66271445, CC BY-SA 4.0
        url = f"http://{HOST}/{API_PREFIX}/author/{self.id}"
        if self.url != url:
            Author.objects.filter(id=self.id).update(url=url)

    # temp

    def has_req_from(self, author):
        """
        Returns True if the user has a request from a specific author, False otherwise 
        """
        return self.follow_requests.filter(pk=author.id).exists()

    def add_post_to_inbox(self, post):
        """
        Adds a pushed post
        """

        try:
            self.inbox_posts.add(post)
        except ValidationError:
            raise
