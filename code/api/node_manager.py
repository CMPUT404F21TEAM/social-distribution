'''
    Manage Node Configurations of remtote groups here.

    Server Admins can add Nodes objects from the admin 
    panel with the following attributes for example:
        host = 'example.com' 
        basic_auth_credentials = 'remotegroup2:meow!'

    Requests sent to the inbox will
    be processed only from existing allowed nodes.

    These credentials (should be in README.md) will be
    used by remote groups to send requests: 
        username: remotegroup
        password: topsecret!

    Requests will have to sent like this
        userAndPass = b64encode(b"remotegroup:topsecret!").decode("ascii")

        headers = { 'Authorization' : 'Basic %s' %  userAndPass }

        requests.post(
            url=author_inbox,
            headers=headers,
            ...
        )

    Test using:
        http -a remotegroup:topsecret! GET http://example.com/
'''

from .models import Node
import logging

logger = logging.getLogger(__name__)

class NodeManager:

    def get_credentials(self, host=None, username=None):
        '''
            Retrieve basic auth credentials from database.
        '''

        try:
            if(host):
                node = Node.objects.get(host=host)
            elif (username):
                node = Node.objects.get(username=username)
            else:
                raise AttributeError('host or  username must be sent!')

            return str.encode(f'{node.username}:{node.password}')
        except Exception as e:
            logger.error(str(e))
            return ''


node_manager = NodeManager()
