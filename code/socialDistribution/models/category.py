from django.db import models

class Category(models.Model):
    '''
    Categories model:
        id                  Auto-generated id
        category            Category name
        posts                reference to post (Many-to-Many relationship)
    '''
    category = models.CharField(max_length=50)