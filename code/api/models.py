from django.db import models

class Node(models.Model):
    '''
        Node for remote group credentials
    '''
    host = models.CharField(max_length=200, primary_key=True)
    basic_auth_credentials = models.CharField(max_length=200)

    def __str__(self):
        return self.host