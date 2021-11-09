from mixer.backend.django import mixer
# from datetime import datetime, timezone

from .models import *


class PostBuilder:
    """
        Creates a post (with all necessary information)
    """

    def __init__(self):
        author = mixer.blend(LocalAuthor)
        self.__post = LocalPost.objects.create(
            author_id=author.id,
            title="testPost",
            # source="",
            # origin="",
            description="testDesc",
            content_type=LocalPost.ContentType.PLAIN,
            content="testContexxt",
            visibility=LocalPost.Visibility.PUBLIC,
            unlisted=False,
            # content_media=None,
            # published=datetime.now(timezone.utc),
            count=0
        )

    def build(self):
        return self.__post

    def authorId(self, id):
        self.__post.author_id = id
        return self

    def title(self, title):
        self.__post.title = title
        return self

    def source(self, source):
        self.__post.source = source
        return self

    def origin(self, origin):
        self.__post.origin = origin
        return self

    def description(self, description):
        self.__post.description = description
        return self

    def content_type(self, content_type):
        self.__post.content_type = content_type
        return self

    def contextText(self, content_text):
        self.__post.content_text = content_text
        return self

    def visibility(self, visibility):
        self.__post.visibility = visibility
        return self

    def unlistedit(self, unlisted):
        self.__post.unlisted = unlisted
        return self

    def content_media(self, content_media):
        self.__post.content_media = content_media
        return self

    def pub_date(self, pub_date):
        self.__post.pub_date = pub_date
        return self

    def count(self, count):
        self.__post.count = count
        return self

    def likes(self, likes):
        """
            Adds a certain number of likes to total likes on a post.
        """
        for i in range(likes):
            # ensure unique by adding numbers
            author = mixer.blend(LocalAuthor, id=i+2453245, username=i+2453245)
            self.__post.likes.create(author=author)
        return self
