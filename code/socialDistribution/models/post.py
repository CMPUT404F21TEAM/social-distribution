from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, manager
from django.contrib.auth.models import User
from django.utils import timezone
import datetime as dt
import timeago

from cmput404.constants import HOST, API_PREFIX
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

    public_id = models.URLField()

    description = models.CharField(max_length=DESCRIPTION_MAXLEN)

    content_type = models.CharField(
        choices=ContentType.choices,
        max_length=4,
        default=ContentType.PLAIN
    )

    # content = models.BinaryField(
    #     max_length=CONTENT_MAXLEN,
    #     null=True,
    #     blank=True,
    # )

    content = models.CharField(
        max_length=CONTENT_MAXLEN,
        null=True,
        blank=True,
    )

    # categories = models.CharField(max_length=2000)

    count = models.PositiveSmallIntegerField(default=0)

    published = models.DateTimeField(default=timezone.now)

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    unlisted = models.BooleanField()


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

    author = models.ForeignKey('LocalAuthor', on_delete=models.CASCADE, related_name="posts")

    content_media = models.BinaryField(
        max_length=Post.CONTENT_MAXLEN,
        null=True,
        blank=True,
    )

    def get_comments_as_json(self):
        author_id = self.author.id
        comments_set = Comment.objects.filter(
            post=self.id).order_by('-pub_date')[:5]
        comment_list = [comment.as_json() for comment in comments_set]
        return {
            "type": "comments",
            "page": 1,
            "size": 5,
            "post": f"http://{HOST}/{API_PREFIX}/author/{author_id}/posts/{self.id}",
            "id": f"http://{HOST}/{API_PREFIX}/author/{author_id}/posts/{self.id}/comments",
            "comments": comment_list
        }

    def has_media(self):
        '''
        Check if post has an attached image
        '''
        return self.content_type in [
            self.ContentType.PNG,
            self.ContentType.JPEG,
            self.ContentType.BASE64
        ]

    def is_public(self):
        '''
        Check if post is public
        '''
        return self.visibility == self.Visibility.PUBLIC

    def when(self):
        '''
        Returns string describing when post the was created

        For example,
            3 days ago
            1 min ago
            5 secs ago
            etc
            ...
        '''
        now = dt.datetime.now(dt.timezone.utc)
        return timeago.format(self.published, now)

    def total_likes(self):
        """
        Returns total likes
        """
        return self.likes.count()

    def as_json(self):
        previousCategories = Category.objects.filter(post=self)
        previousCategoriesNames = [cat.category for cat in previousCategories]
        return {
            "type": "post",
            # title of a post
            "title": self.title,
            # id of the post
            "id": f"http://{HOST}/{API_PREFIX}/author/{self.author.id}/posts/{self.id}",
            # where did you get this post from?
            "source": "blah",
            # where is it actually from
            "origin": "blah",
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
            "content": self.content,
            # the author has an ID where by authors can be disambiguated
            "author": self.author.as_json(),
            # categories this post fits into (a list of strings
            "categories": previousCategoriesNames,
            # comments about the post
            # return a maximum number of comments
            # total number of comments for this post
            "count": self.count,
            # the first page of comments
            "comments": f"http://{HOST}/{API_PREFIX}/author/{self.author.id}/posts/{self.id}/comments/",
            # commentsSrc is OPTIONAL and can be missing
            # You should return ~ 5 comments per post.
            # should be sorted newest(first) to oldest(last)
            # this is to reduce API call counts
            "commentsSrc": self.get_comments_as_json(),
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

    source = models.URLField(max_length=Post.URL_MAXLEN)

    origin = models.URLField(max_length=Post.URL_MAXLEN)

    author = models.URLField(max_length=Post.URL_MAXLEN)
