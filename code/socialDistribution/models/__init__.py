# https://docs.djangoproject.com/en/3.2/topics/db/models/#organizing-models-in-a-package

from .common import Post, Author
from .category import Category
from .comment import Comment
from .inbox import Inbox
