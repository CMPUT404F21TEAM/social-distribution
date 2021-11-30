from django.db import models
from cmput404.constants import STRING_MAXLEN
class Category(models.Model):
    '''
    Categories model:
        id                  Auto-generated id
        category            Category name
        posts                reference to post (Many-to-Many relationship)
    '''
    category = models.CharField(max_length=STRING_MAXLEN)
