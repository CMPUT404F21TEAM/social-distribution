from django.db import models

class Category(models.Model):
    '''
    Categories model:
        id                  Auto-generated id
        category            Category name
        post                reference to post (Many-to-One relationship)
    '''
    category = models.CharField(max_length=50)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)