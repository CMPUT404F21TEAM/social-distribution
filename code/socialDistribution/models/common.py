from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, manager
from datetime import *
import timeago

from cmput404.constants import HOST, API_PREFIX
from .comment import Comment
from .category import Category


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
    def get_visible_posts_to(self, author):
        """ 
            @depreciated due to too much coupling between posts and author
            author to author method yet still relies on Post

            Returns valid posts
        """
        visible_posts = None
        if author.id == self.id:
            visible_posts = Post.objects.filter(author__pk=author.id)
        elif self.is_friends_with(author):
            visible_posts = Post.objects.filter(
                author__pk=self.id).exclude(visibility=Post.PRIVATE)
        else:
            visible_posts = Post.objects.filter(
                author__pk=self.id, visibility=Post.PUBLIC)

        return visible_posts.order_by('-pub_date')[:]

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

class PostQuerySet(models.QuerySet):

    def listed(self):
        """ Get all listed posts.
        """
        return self.filter(unlisted=False)

    def get_public(self):
        """ Get all public posts.
        """
        return self.filter(visibility=Post.PUBLIC)

    def get_friend(self):
        """ Get all friend posts.
        """
        # Django Software Foundation, https://docs.djangoproject.com/en/dev/topics/db/queries/#complex-lookups-with-q-objects
        return self.filter(
            Q(visibility=Post.PUBLIC) | Q(visibility=Post.PRIVATE)
        )

    def chronological(self):
        """ Order results in chronological order in terms of published date.
        """
        self.order_by('-pub_date')[:]

class Post(models.Model):
    '''
    Post model:
        title               Post title (a Text)
        id (default)        Auto-generated id

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
        likes               Authors that liked this post

    '''

    objects = PostQuerySet.as_manager()

    class PostContentType(models.TextChoices):
        MARKDOWN = 'MD', 'text/markdown'
        PLAIN = 'PL', 'text/plain'
        BASE64 = 'B64', 'application/base64'
        PNG = 'PNG', 'image/png;base64'
        JPEG = 'JPEG', 'image/jpeg;base64'

    TITLE_MAXLEN = 50
    DESCRIPTION_MAXLEN = 50
    CONTEXT_TEXT_MAXLEN = 200
    CONTENT_MEDIA_MAXLEN = 1000
    URL_MAXLEN = 2048

    title = models.CharField(max_length=TITLE_MAXLEN)
    source = models.URLField(max_length=URL_MAXLEN)
    origin = models.URLField(max_length=URL_MAXLEN)
    description = models.CharField(max_length=DESCRIPTION_MAXLEN)

    content_type = models.CharField(
        choices=PostContentType.choices,
        max_length=4,
        default=PostContentType.PLAIN
    )

    content_text = models.TextField(max_length=CONTEXT_TEXT_MAXLEN)

    # Base64 encoded binary field (image/png, image/jpg, application/base64)
    content_media = models.BinaryField(
        max_length=CONTENT_MEDIA_MAXLEN, null=True, blank=True)
    author = models.ForeignKey('Author', on_delete=models.CASCADE, related_name="posts")

    count = models.PositiveSmallIntegerField(default=0)
    pub_date = models.DateTimeField()

    PUBLIC = "PB"
    FRIENDS = "FRD"
    PRIVATE = "PR"
    VISIBILITY_CHOICES = (
        (PUBLIC, 'PUBLIC'),
        (FRIENDS, 'FRIENDS'),
        (PRIVATE, 'PRIVATE')
    )

    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default=PUBLIC)
    unlisted = models.BooleanField()
    likes = models.ManyToManyField('Author', related_name="liked_post", blank=True)

    # REFACTOR --? Move to author.get_friends_friend_posts
    @classmethod
    def get_all_friends_posts(cls, author):
        '''
        Get the posts created by friends of author
        '''
        followed_author_set = Author.objects.filter(followers__id=author.id)
        follower_author_set = author.followers.all()
        friends_set = followed_author_set and follower_author_set   # friends set
        return cls.objects.filter(
            unlisted=False,
            author__in=friends_set,
            visibility=Post.FRIENDS,
        )

    @classmethod
    def get_latest_posts(cls, author):
        '''
        Get the author's posts and all the posts created by
        author's friends
        '''
        # public posts not created by user
        public_posts_set = cls.objects.filter(
            unlisted=False,
            visibility=Post.PUBLIC
        ).exclude(author=author)

        # all listed posts created by user
        user_posts_set = cls.objects.filter(
            unlisted=False,
            author=author
        )

        friends_posts_set = cls.get_all_friends_posts(author)
        return public_posts_set.union(
            friends_posts_set,
            user_posts_set
        ).order_by("-pub_date")[:]

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
            self.PostContentType.PNG,
            self.PostContentType.JPEG,
            self.PostContentType.BASE64
        ]

    def is_public(self):
        '''
        Check if post is public
        '''
        return self.visibility == self.PUBLIC

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
        now = datetime.now(timezone.utc)
        return timeago.format(self.pub_date, now)

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
            "contentType": self.content_type,
            "content": self.content_text,
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
            "published": str(self.pub_date),
            # visibility ["PUBLIC","FRIENDS"]
            "visibility": self.visibility,
            # for visibility PUBLIC means it is open to the wild web
            # FRIENDS means if we're direct friends I can see the post
            # FRIENDS should've already been sent the post so they don't need this
            "unlisted": self.unlisted
            # unlisted means it is public if you know the post name -- use this for images, it's so images don't show up in timelines
        }
