from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from datetime import *

from cmput404.constants import HOST, API_PREFIX

class Category(models.Model):
    '''
    Categories model:
        id                  Auto-generated id
        category            Category name
        post                reference to post (Many-to-One relationship)
    '''
    category = models.CharField(max_length=50)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)