from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

import datetime
import uuid

import socialDistribution.requests as api_requests
from cmput404.constants import API_BASE
from .follow import Follow


class Author(models.Model):
    """ Author model which represents all authors.

        All authors that interact with the application will be stored as an author. That is,
        the Author model can store both remote and local authors. Methods on an Author instance primarily
        rely on API calls to get the data corresponding to the author from a remote server.

        In the future, caching can be used with this model to reduce the number of API calls being sent out.

        When a local author is created, it must be re-fetched from the database in order to access the auto-generated author.url attribute.
    """
    
    # Django Software Foundation, https://docs.djangoproject.com/en/dev/ref/models/fields/#uuidfield
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    url = models.URLField()
    displayName = models.CharField(max_length=50, default="Anonymous User")
    githubUrl = models.CharField(max_length=50, null=True)
    profileImageUrl = models.CharField(max_length=50, null=True)

    created_date = models.DateTimeField(auto_now_add=True)

    # timestamp of when the object was last updated
    # will need later for caching
    _last_updated = models.DateTimeField(auto_now=True)

    # true means that field data will always be up-to-date (used by LocalAuthor)
    _always_up_to_date = models.BooleanField(default=False)

    def get_url_id(self):
        """ Returns the id of the author in url form """
        return self.url

    def has_follower(self, author):
        """ Over-ridden in LocalAuthor. Returns True if author is a follower of self, False otherwise """
        res_code, res_body = api_requests.get(self.url.strip("/") + "/followers")

        if res_code == 200 and res_body:
            for follower in res_body["items"]:
                if follower["id"] == author.get_url_id():
                    return True
        else:
            return False

    def has_follow_request(self, author):
        """ Over-ridden in LocalAuthor. Always returns False """
        # No endpoint give us follow request objects
        # Even if we GET against their inbox, we'll get back a list of posts
        # The alternative would be to keep track of outgoing follow requests
        return False

    def get_inbox(self):
        """ Gets the URL of the Authors inbox. """

        return self.url.strip("/") + "/inbox/"

    def as_json(self):
        """ GET JSON representation of author. If local or a remote that was saved recently, return that JSON.
            Otherwise, make an API call to update JSON.
        """

        was_recent_update = self._last_updated < timezone.now()-datetime.timedelta(seconds=10)
        json_data = {
            "type": "author",
            "id": f"{API_BASE}/author/{self.id}",
            "host": f'{API_BASE}/',
            "displayName": self.displayName,
            "url": f"{API_BASE}/author/{self.id}",
            "github": self.githubUrl,
            "profileImage": self.profileImageUrl
        }

        if self._always_up_to_date:
            # read author data from fields
            # will do this in case of LocalAuthor
            return json_data

        else:
            # make API call to get author data
            status_code, response_body = api_requests.get(self.url.strip("/"))
            if status_code == 200 and response_body is not None:
                self.update_with_json(data=response_body)
                return response_body
            else:
                # delete the record if there was a problem
                self.delete()
                # don't return None
                return json_data

    def update_with_json(self, data):
        '''
            Add or update Author model data
            Had to move here from utility.py due to import errors
        '''
        try:
            self.displayName = data['displayName']
            self.githubUrl = data['github']
            self.profileImageUrl = data['profileImage']
            self.save()
        except:
            return

    def __str__(self) -> str:
        return f"Author: {self.url}"


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
        url = f"{API_BASE}/author/{self.id}"
        if self.url != url:
            Author.objects.filter(id=self.id).update(url=url)
