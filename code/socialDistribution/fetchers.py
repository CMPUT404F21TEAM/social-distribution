""" This file contains methods that asyncrohonously fetch update data for different data models """

import threading
import logging

from cmput404.constants import SCHEME, HOST
import socialDistribution.requests as api_requests
from socialDistribution.models import *
from api.models import *


logger = logging.getLogger(__name__)


def fetch_remote_authors():
    """ Asynchronously fetch all authors from the API endpoints of all connected remote nodes.
    """

    for node in Node.objects.filter(remote_credentials=True).exclude(host=HOST):
        server_url = f'{SCHEME}://{node.host}{node.api_prefix}'
        logger.info(f"Starting update for all authors on {server_url}")
        t = threading.Thread(target=update_authors_for_server, args=[server_url], daemon=True)
        t.start()


def update_authors_for_server(server_url):
    try:
        authors_endpoint = server_url.strip('/') + '/authors/'
        res_code, res_body = api_requests.get(authors_endpoint)

        # skip node if unresponsive
        if res_body == None:
            return None

        # add remote authors to local cache
        for remote_author in res_body['items']:
            author, created = Author.objects.get_or_create(
                url=remote_author['id'],
            )
            author.update_with_json(data=remote_author)

    except Exception as e:
        logger.error(e, exc_info=True)


def fetch_author_update(author: Author):
    """ Asynchronously fetch author data for given author from the API endpoint of their home node.
    """

    # don't update if author already up to date
    if author.up_to_date():
        return None

    logger.info(f"Starting update for {author}")
    t = threading.Thread(target=update_author, args=[author.id], daemon=True)
    t.start()
    return author.id


def update_author(id):
    author = Author.objects.get(id=id)
    status_code, response_body = api_requests.get(author.url.strip("/"))
    if status_code == 200 and response_body is not None:
        author.update_with_json(data=response_body)
    else:
        author.delete()
