'''
    Manage Node Configurations of remtote groups here.
'''

from .models import Node
import logging

logger = logging.getLogger(__name__)

class NodeManager:

    def get_credentials(self, host=None, username=None, remote_credentials=False):
        '''
            Retrieve basic auth credentials from database.
        '''

        try:
            if(host):
                node = Node.objects.get(host=host, remote_credentials=remote_credentials)
            elif (username):
                node = Node.objects.get(username=username, remote_credentials=remote_credentials)
            else:
                raise AttributeError('host or  username must be sent!')

            return str.encode(f'{node.username}:{node.password}')
        except Exception as e:
            logger.error(str(e))
            return ''


node_manager = NodeManager()
