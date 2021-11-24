from django.db import models
from django.contrib.auth.models import User

import socialDistribution.requests as api_requests
from cmput404.constants import SCHEME, HOST, API_PREFIX
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
    displayName = models.CharField(max_length=50)
    githubUrl = models.CharField(max_length=50, null=True)
    profileImageUrl = models.CharField(max_length=50, null=True)

    # true means that field data will always be up-to-date (used by LocalAuthor)
    _always_up_to_date = models.BooleanField(default=False)

    def get_inbox(self):
        """ Gets the URL of the Authors inbox. """

        return self.url.strip("/") + "/inbox"

    def as_json(self):
        if self._always_up_to_date:
            # read author data from fields
            # will do this in case of LocalAuthor
            json_data = {
                "type": "author",
                "id": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.id}",
                "host": f'{SCHEME}://{HOST}/{API_PREFIX}/',
                "displayName": self.displayName,
                "url": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.id}",
                "github": self.githubUrl,
                "profileImage": self.profileImageUrl
            }
        else:
            # make API call to get author data
            status_code, json_data = api_requests.get(self.url)
            # todo handle errors is api_request fails

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

    follow_requests = models.ManyToManyField('Author', related_name="sent_follow_requests")
    inbox_posts = models.ManyToManyField('InboxPost')

    @classmethod
    def get_local_if_exists(cls, author: Author):
        """ Given an Author record, gets the LocalAuthor record if the Author is local. If
            the Author is not local, returns the same Author object.
        """

        if cls.objects.filter(id=author.id).exists():
            return cls.objects.get(id=author.id)
        else:
            return author

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
            "id": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.id}",
            # the home host of the author
            "host": f'{SCHEME}://{HOST}/{API_PREFIX}/',
            # the display name of the author
            "displayName": self.displayName,
            # url to the authors profile
            "url": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.id}",
            # HATEOS url for Github API
            "github": self.githubUrl,
            # Image from a public domain
            "profileImage": self.profileImageUrl
        }

    def save(self, *args, **kwargs):
        self._always_up_to_date = True
        super().save(*args, **kwargs)  # Call the "real" save() method.
        self._set_url()

    def _set_url(self):
        """ Sets the URL of the author to be "http://{HOST}/{API_PREFIX}/author/{self.id}" if one was not set when created. This 
            sets the URL attribute of all local authors.
        """
        # Clark, https://stackoverflow.com/users/10424244/clark, "Django - How to get self.id when saving a new object?",
        # 2021-02-19, https://stackoverflow.com/a/66271445, CC BY-SA 4.0
        url = f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.id}"
        if self.url != url:
            Author.objects.filter(id=self.id).update(url=url)
