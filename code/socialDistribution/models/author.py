from django.db import models
from django.contrib.auth.models import User

import socialDistribution.requests as api_requests
from cmput404.constants import HOST, API_PREFIX
from .follow import Follow


class Author(models.Model):
    """ Author model which represents all authors.

        All authors that interact with the application will be stored as an author. That is,
        the Author model can store both remote and local authors. Methods on an Author instance primarily
        rely on API calls to get the data corresponding to the author from a remote server.

        In the future, caching can be used with this model to reduce the number of API calls being sent out.

        When a local author is created, it must be re-fetched from the database in order to access the auto-generated author.url attribute.
    """

    url = models.URLField()

    def get_inbox(self):
        """ Gets the URL of the Authors inbox. """

        return self.url.strip("/") + "/inbox"

    def as_json(self):
        # Makes a GET request to URL to get the Author data
        status_code, json_data = api_requests.get(self.url)

        # could return None if something goes wrong
        # caller should handle this
        return json_data


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
        follows             Followers of the author (Collection of Follow objects)

        friend_requests     Authors who have requested to follow author (Collection of LocalAuthor objects)
        inbox_posts         Posts sent to the inbox of the author
    '''

    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=50, unique=True, blank=False)
    displayName = models.CharField(max_length=50)
    githubUrl = models.CharField(max_length=50, null=True)
    profileImageUrl = models.CharField(max_length=50, null=True)

    follow_requests = models.ManyToManyField('Author', related_name="sent_follow_requests")
    inbox_posts = models.ManyToManyField('InboxPost')

    def get_url_id(self):
        """
        Returns the id of the author in url form
        """
        return self.url

    def has_follower(self, author: Author):
        """ Returns true if author is a follower of self, false otherwise. """

        try:
            self.follows.get(actor=author)
            return True
        except Follow.DoesNotExist:
            return False

    def has_friend(self, author: Author):
        """ Returns true if author is a friend of self, false otherwise. """

        try:
            follow = self.follows.get(actor=author)
            return follow.is_friend()
        except Follow.DoesNotExist:
            return False

    def has_follow_request(self, author: Author):
        """ Returns true if self has a follow request from author, false otherwise. """

        return self.follow_requests.filter(id=author.id).exists()

    def handle_follow_request(self, author: Author, accept: bool):
        """ Removes author from follow requests (if exists) and resolves the request. If accept is 
            true, they are added as a follower of self. 
        """

        query_result = self.follow_requests.filter(id=author.id)
        if query_result.exists():
            self.follow_requests.remove(query_result.first())

        if accept == True:
            self.follows.get_or_create(actor=author)

    def get_followers(self):
        """ Gets the Authors who are followers of self. """

        follows = self.follows.all()
        followers = [f.actor for f in follows]
        return followers

    def get_friends(self):
        """ Gets the Authors who are friends of self. """

        follows = self.follows.all()
        friends = [f.actor for f in follows if self.has_friend(f.actor)]
        return friends

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
