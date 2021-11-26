'''
    Manage Node Configurations of remtote groups here.
'''

from .models import Node
import logging

logger = logging.getLogger("api")

class NodeManager:

    def get_credentials(self, host=None, username=None, remote_credentials=False):
        '''
            Retrieve basic auth credentials from database.
        '''

        try:
            if(host):
                logger.info(f"Getting basic auth credentials for host: {host} and remote_credentials: {remote_credentials}")
                node = Node.objects.get(host=host, remote_credentials=remote_credentials)
            elif (username):
                logger.info(f"Getting basic auth credentials for username: {username} and remote_credentials: {remote_credentials}")
                node = Node.objects.get(username=username, remote_credentials=remote_credentials)
            else:
                logger.warn("Incoming request with no authentication header")
                raise AttributeError('Host or  username must be sent!')

            return str.encode(f'{node.username}:{node.password}')
        except Exception as e:
            logger.error(e, exc_info=True)
            return b''


node_manager = NodeManager()
