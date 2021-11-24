from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, manager
from django.contrib.auth.models import User
from django.utils import timezone
from jsonfield import JSONField
import datetime as dt
import timeago, base64
import json

from cmput404.constants import SCHEME, HOST, API_PREFIX
import socialDistribution.requests as api_requests
from .comment import Comment
from .category import Category


class PostQuerySet(models.QuerySet):

    def listed(self):
        """ Get all listed posts.
        """
        return self.filter(unlisted=False)

    def get_public(self):
        """ Get all public posts.
        """
        return self.filter(visibility=Post.Visibility.PUBLIC)

    def get_friend(self):
        """ Get all friend posts.
        """
        # Django Software Foundation, "Complex lookups with Q objects", 2021-10-30
        # https://docs.djangoproject.com/en/3.2/topics/db/queries/#complex-lookups-with-q-objects
        return self.filter(
            Q(visibility=Post.Visibility.PUBLIC) | Q(visibility=Post.Visibility.FRIENDS)
        )

    def chronological(self):
        """ Order results in chronological order in terms of published date.
        """
        for post in self.all():
            if post is InboxPost:
                post.fetch_update()
        return self.order_by('-published')[:]


class Post(models.Model):

    class Meta:
        # Django Software Foundation, "Abstract base classes", 2021-11-04,
        # https://docs.djangoproject.com/en/3.2/topics/db/models/#abstract-base-classes
        abstract = True

    class ContentType(models.TextChoices):
        MARKDOWN = 'MD', 'text/markdown'
        PLAIN = 'PL', 'text/plain'
        BASE64 = 'B64', 'application/base64'
        PNG = 'PNG', 'image/png;base64'
        JPEG = 'JPEG', 'image/jpeg;base64'

    class Visibility(models.TextChoices):
        PUBLIC = "PB", "PUBLIC"
        FRIENDS = "FR", "FRIEND"
        PRIVATE = "PR", "PRIVATE"

    TITLE_MAXLEN = 50
    DESCRIPTION_MAXLEN = 50
    CONTENT_MAXLEN = 4096
    URL_MAXLEN = 2048

    objects = PostQuerySet.as_manager()

    title = models.CharField(max_length=TITLE_MAXLEN)
    
    source = models.URLField(max_length=URL_MAXLEN, default='')

    origin = models.URLField(max_length=URL_MAXLEN, default='')

    public_id = models.URLField()

    description = models.CharField(max_length=DESCRIPTION_MAXLEN)

    categories = models.ManyToManyField('Category', blank=True)

    content_type = models.CharField(
        choices=ContentType.choices,
        max_length=4,
        default=ContentType.PLAIN
    )

    content = models.BinaryField(
        max_length=CONTENT_MAXLEN,
        null=True,
        blank=True,
    )

    published = models.DateTimeField(
        default=timezone.now
    )

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    unlisted = models.BooleanField(
        default=False
    )

    @property
    def author_as_json(self):
        """ Gets the author of the post in JSON format. """

        raise NotImplementedError("Submodel does not implement this getter")

    @property
    def comments_as_json(self):
        """ Gets the comments of the post in JSON format. """

        raise NotImplementedError("Submodel does not implement this getter")

    @property
    def decoded_content(self):
        """ Gets the decoded post content. Images are only
            utf-8 decoded and while text content is both
            base64 decoded and utf-8 decoded.
        """
        if not self.content:
            return ''

        return bytes(self.content).decode('utf-8')

    def is_image_post(self):
        """ Check if the post is an image-only post """
        return self.content_type in [
            self.ContentType.PNG,
            self.ContentType.JPEG,
            self.ContentType.BASE64
        ]

    def total_likes():
        """ Gets the total number of likes on the post. """

        raise NotImplementedError("Submodel does not implement this method")

    def is_public(self):
        """ Check if post is public. """

        return self.visibility == self.Visibility.PUBLIC
    
    def is_friends(self):
        """ Check if post is friends. """

        return self.visibility == self.Visibility.FRIENDS

    def when(self):
        """ Returns string describing when post the was created.

        For example,
            3 days ago
            1 min ago
            5 secs ago
            etc
            ...
        """

        now = dt.datetime.now(dt.timezone.utc)
        return timeago.format(self.published, now)


class LocalPost(Post):
    '''
    Post model:
        id (default)        Auto-generated id
        title               Title for the post

        source              Where the post was obtained (a URL)
        origin              original source (a URL)
        description         Post description (a Text)

        content_type        Type of post's content:
                                - markdown
                                - plain text (default)
                                - png
                                - jpeg
                                - base64 (binary data)

        content_text        Actual text-type content (markdown or plain text)
        content_media       Any attached images (base64 encoded image; png or jpeg)

        author              Post author (reference to author)
        count               total number of comments (small integer)
        pub_date            Post published date (datetime)
        visibility          PUBLIC or FRIENDS
        unlisted            Boolean indicating whether post is listed or not
        likes               Likes created by Authors that liked this post

    '''

    # reference to LocalAuthor that created this post
    author = models.ForeignKey('LocalAuthor', on_delete=models.CASCADE, related_name="posts")

    @property
    def author_as_json(self):
        """ Gets the author of the post in JSON format. """

        return self.author.as_json()

    @property
    def comments_as_json(self):
        """ Gets the comments of the post in JSON format. """

        author_id = self.author.id
        return {
            "type": "comments",
            "page": None,
            "size": None,
            "post": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{author_id}/posts/{self.id}",
            "id": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{author_id}/posts/{self.id}/comments",
            "comments": self.comments_json_as_list()
        }

    def comments_json_as_list(self):
        """ Gets the comments of the post format. """
        comments_set = self.comments()
        comment_list = [comment.as_json() for comment in comments_set]
        return comment_list
    
    def comments(self):
        """ Gets the comments of the post """
        return Comment.objects.filter(post=self.id).order_by('-pub_date')

    def total_likes(self):
        """ Gets the total number of likes on the post. """

        return self.likes.count()

    def get_id(self):
        return f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.author.id}/posts/{self.id}"

    def as_json(self):
        previousCategories = self.categories.all()
        previousCategoriesNames = [cat.category for cat in previousCategories]
        return {
            "type": "post",
            # title of a post
            "title": self.title,
            # id of the post
            "id": self.get_id(),
            # where did you get this post from?
            "source": self.source,
            # where is it actually from
            "origin": self.origin,
            # a brief description of the post
            "description": self.description,
            # The content type of the post
            # assume either
            # text/markdown -- common mark
            # text/plain -- UTF-8
            # application/base64
            # image/png;base64 # this is an embedded png -- images are POSTS. So you might have a user make 2 posts if a post includes an image!
            # image/jpeg;base64 # this is an embedded jpeg
            # for HTML you will want to strip tags before displaying
            "contentType": self.get_content_type_display(),
            "content": self.decoded_content,
            # the author has an ID where by authors can be disambiguated
            "author": self.author.as_json(),
            # categories this post fits into (a list of strings
            "categories": previousCategoriesNames,
            # comments about the post
            # return a maximum number of comments
            # total number of comments for this post
            "count": 0,
            # the first page of comments
            "comments": f"{SCHEME}://{HOST}/{API_PREFIX}/author/{self.author.id}/posts/{self.id}/comments/",
            # commentsSrc is OPTIONAL and can be missing
            # You should return ~ 5 comments per post.
            # should be sorted newest(first) to oldest(last)
            # this is to reduce API call counts
            "commentsSrc": self.comments_as_json,
            # ISO 8601 TIMESTAMP
            "published": self.published.isoformat(),
            # visibility ["PUBLIC","FRIENDS"]
            "visibility": self.get_visibility_display(),
            # for visibility PUBLIC means it is open to the wild web
            # FRIENDS means if we're direct friends I can see the post
            # FRIENDS should've already been sent the post so they don't need this
            "unlisted": self.unlisted
            # unlisted means it is public if you know the post name -- use this for images, it's so images don't show up in timelines
        }


class InboxPost(Post):
    '''
    InboxPost model:
        title               Title of the post
        public_id           URL id of the post when it was recieved
        source              Location from which the post was received (a URL)
        origin              Location from which the post originated (a URL)
        description         Text description
        content_type        Type of post's content:
                                - markdown
                                - plain text
                                - png
                                - jpeg
                                - base64

        content             Content of the post
        categories          Categories encoded as a JSON array
        author              Author of the post
        count               Total number of comments (small integer)
        published           Post published date (datetime)
        visibility          PUBLIC or FRIENDS
        unlisted            Boolean indicating whether post is listed or not

    '''

    author = models.URLField(max_length=Post.URL_MAXLEN)

    _author_json = JSONField()

    @property
    def author_as_json(self):
        """ Gets the author of the post in JSON format. """
        return self._author_json
    
    def fetch_update(self):
        """ Fetches update about the post for an edit or delete """
        # make api request
        try:
            actor_url = self.author.url.strip('/')
            object_url = self.public_id.strip('/')
            endpoint = actor_url + '/posts/' + object_url
            status_code, response_body = api_requests.get(endpoint)

            # check if GET request came back with post object
            if status_code == 200 and response_body is not None and response_body.get("id") == object_url:
                data = json.loads(response_body)
                self.title = data['title']
                self.description = data['description']
                self.content_type = data['contentType']
                self.content = data['content'].encode('utf-8')
                self.visibility = data['visibility']
                self.unlisted = data['unlisted']
                
                categories = data['categories']
                
                if categories is not None:
                    categories_to_remove = [ cat.category for cat in self.categories.all()]

                    """
                    This implementation makes category names case-insensitive.
                    This makes handling Category objects cleaner, albeit slightly more
                    involved.
                    """
                    for category in categories:
                        category_obj, created = Category.objects.get_or_create(
                            category__iexact=category,
                            defaults={'category': category}
                        )
                        self.categories.add(category_obj)
                        
                        while category_obj.category in categories_to_remove:
                            categories_to_remove.remove(category_obj.category)     # don't remove this category

                    for category in categories_to_remove:
                        category_obj = Category.objects.get(category=category)
                        self.categories.remove(category_obj)

                self.save()
            elif status_code == 400 or status_code == 410:
                self.delete()
        except:
            print(f'Error updating post: {self.id}')