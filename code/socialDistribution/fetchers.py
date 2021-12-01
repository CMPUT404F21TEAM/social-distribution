""" This file contains methods that asyncrohonously fetch update data for different data models """

import threading
import logging

from cmput404.constants import SCHEME, HOST
import socialDistribution.requests as api_requests
from socialDistribution.models import *
from api.models import *


logger = logging.getLogger(__name__)

# All functions are in this file are inspiried by the following example
# nbwoodward, https://stackoverflow.com/users/8894424/nbwoodward,
# "Can you perform multi-threaded tasks within Django?",
# https://stackoverflow.com/a/53327191, CC BY-SA 4.0


def fetch_remote_authors():
    """ Asynchronously fetch all authors from the API endpoints of all connected remote nodes.
    """

    for node in Node.objects.filter(remote_credentials=True).exclude(host=HOST):
        server_url = f'{SCHEME}://{node.host}{node.api_prefix}'
        logger.info(f"Starting update for all authors on {server_url}")

        # Start a thread that will get all authors for the given remote server
        t = threading.Thread(target=update_authors_for_server, args=[server_url], daemon=True)
        t.start()


def update_authors_for_server(server_url):
    """ Makes API call to get all authors on a remote server

        Parameters:
         - server_url (string): the base API endpoint for a remote server
    """

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

        Paramters:
         - author (models.Author): The author to be updated
    """

    # don't update if author already up to date
    if author.up_to_date():
        return None

    logger.info(f"Starting update for {author}")

    # Start a thread that will update data for author
    t = threading.Thread(target=update_author, args=[author.id], daemon=True)
    t.start()
    return author.id


def update_author(id):
    """ Makes API call to update author data for a given author

        Parameters:
         - id (UUID): the ID of the author to update 
    """

    try:
        author = Author.objects.get(id=id)

        # update author object
        status_code, response_body = api_requests.get(author.url.strip("/"))
        if status_code == 200 and response_body is not None:
            author.update_with_json(data=response_body)
        else:
            author.delete()

    except Exception as e:
        logger.error(e, exc_info=True)


def fetch_follow_update(follow: Follow):
    """ Asynchronously update follow data for a given follow.

        Paramters:
         - follow (models.Follow): The follow to be updated
    """

    # don't update if follow already up to date
    if follow.up_to_date():
        return None

    logger.info(f"Starting update for {follow}")
    t = threading.Thread(target=update_follow, args=[follow.id], daemon=True)
    t.start()
    return follow.id


def update_follow(id):
    """ Makes API call to update follow data for a given follow

        Parameters:
         - id: the ID of the follow object to update 
    """

    try:
        follow = Follow.objects.get(id=id)

        # make api request to see if object is a friend of actor (i.e. they are friends)
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
