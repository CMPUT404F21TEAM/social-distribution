from django.db import models
from cmput404.constants import STRING_MAXLEN, URL_MAXLEN

class Node(models.Model):
    '''
        Node model:
            id                      Auto-generated id
            host                    Hostname of server
            username                Basic Auth Username
            password                Basic Auth Password
            remote_credentials      Boolean to indicate if credentials are to connect 
                                    to remote group or allow remote group to connect.
    '''
    host = models.CharField(max_length=URL_MAXLEN, null=False)
    api_prefix = models.CharField(max_length=STRING_MAXLEN, default='/api', blank=True)
    username = models.CharField(max_length=STRING_MAXLEN, null=False)
    password = models.CharField(max_length=STRING_MAXLEN, null=False)
    remote_credentials = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.host} - remote:{self.remote_credentials}'

    def get_credentials(self):
        ''' get username and password encoded
        '''
        return str.encode(f'{self.username}:{self.password}')
