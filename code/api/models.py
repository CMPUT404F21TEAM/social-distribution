from django.db import models

class Node(models.Model):
    '''
        Node for remote group credentials
    '''
    host = models.CharField(max_length=200, primary_key=True)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)

    def __str__(self):
        return self.username