""" This file contains methods that asyncrohonously fetch update data for different data models """

import threading
import logging

from cmput404.constants import SCHEME, HOST
import socialDistribution.requests as api_requests
from socialDistribution.models import *
from api.models import *


logger = logging.getLogger(__name__)

# nbwoodward, https://stackoverflow.com/users/8894424/nbwoodward,
# "Can you perform multi-threaded tasks within Django?",
# https://stackoverflow.com/a/53327191, CC BY-SA 4.0


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
    try:
        author = Author.objects.get(id=id)

        # update author object
        status_code, response_body = api_requests.get(author.url.strip("/"))
        if status_code == 200 and response_body is not None:
            author.update_with_json(data=response_body)
        else:
            author.delete()

        # update only if local
        if LocalAuthor.objects.filter(id=id).exists():
            for follow in author.follows.all():
                fetch_follow_update(follow)

    except Exception as e:
        logger.error(e, exc_info=True)


def fetch_follow_update(follow: Follow):
    # don't update if follow already up to date
    if follow.up_to_date():
        return None

    logger.info(f"Starting update for {follow}")
    t = threading.Thread(target=update_follow, args=[follow.id], daemon=True)
    t.start()
    return follow.id


def update_follow(id):
    try:
        follow = Follow.objects.get(id=id)

        # make api request
        actor_url = follow.actor.url.strip('/')
        object_url = follow.object.url.strip('/')
        endpoint = actor_url + '/followers/' + object_url
        status_code, response_body = api_requests.get(endpoint)

        # check if GET request came back with author object
        if status_code == 200 and response_body is not None and response_body.get("id") == object_url:
            follow._is_friend = True
        else:
            follow._is_friend = False
        
        follow.save()

    except Exception as e:
        logger.error(e, exc_info=True)
