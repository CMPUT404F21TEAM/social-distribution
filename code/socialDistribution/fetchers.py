""" This file contains methods that asyncrohonously fetch update data for different data models """

from django.db import connection
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

    # Start a thread that will get all remote authors
    t = threading.Thread(target=update_remote_authors, args=[], daemon=True)
    t.start()


def update_remote_authors():
    """ Makes series of API calls to get all authors on remote servers.

    """

    try:
        logger.info(f"Starting fetch for all remote authors")

        # check remote nodes
        for node in Node.objects.filter(remote_credentials=True).exclude(host=HOST):
            server_url = f'{SCHEME}://{node.host}{node.api_prefix}'
            authors_endpoint = server_url.strip('/') + '/authors/'
            res_code, res_body = api_requests.get(authors_endpoint)

            # skip node if unresponsive
            if res_body is not None and res_body.get("items") is not None:

                # add remote authors to local cache
                for remote_author in res_body['items']:
                    author, created = Author.objects.get_or_create(
                        url=remote_author['id'],
                    )
                    author.update_with_json(data=remote_author)

        # check for deleted authors 
        for author in Author.objects.all():
            if not author.up_to_date():
                author_url = author.url.strip("/")
                res_code, res_data = api_requests.get(author_url)
                if res_code == 404 or res_code == 410:
                    author.delete()

    except Exception as e:
        logger.error(e, exc_info=True)
    
    finally:
        logger.info(f"Finished remote authors fetch for all servers")
        connection.close()


def fetch_author_update(author: Author):
    """ Asynchronously fetch author data for given author from the API endpoint of their home node.

        Paramters:
         - author (models.Author): The author to be updated
    """

    # don't update if author already up to date
    if author.up_to_date():
        return None

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
        logger.info(f"Starting update for {author}")

        # update author object
        status_code, response_body = api_requests.get(author.url.strip("/"))
        if status_code == 200 and response_body is not None:
            author.update_with_json(data=response_body)

        elif status_code == 404 or status_code == 410:
            author.delete()

    except Exception as e:
        logger.error(e, exc_info=True)

    finally:
        logger.info(f"Finished author update for {author}")
        connection.close()


def fetch_follow_update(actor: Author, object: Author):
    """ Asynchronously checks if actor is following object. If actor is following object, a Follow
        object is created (if does not already exist). If actor is not following object, the corresponding
        Follow object is deleted (if it exists).

        Parameters:
         - actor (Author): The author that might be a follower of object
         - object (Author): The author that might have actor as a follower
    """

    # check if follow exists and whether it is up to date
    try:
        follow = Follow.objects.get(actor_id=actor.id, object_id=object.id)
        if follow.up_to_date():
            return None  # no update needed for now
    except Follow.DoesNotExist:
        pass


    # Start a thread that will update follow
    t = threading.Thread(target=update_follow, args=[actor.id, object.id], daemon=True)
    t.start()
    return actor.id, object.id


def update_follow(actor_id, object_id):
    """ Makes API call to check if actor author is following object author. 

        Parameters:
         - actor_id: The id of the author that might be a follower of object
         - object_id: The id of the author that might have actor as a follower

    """

    try:
        actor = Author.objects.get(id=actor_id)
        object = Author.objects.get(id=object_id)
        logger.info(f"Starting follow update for {actor} --> {object}")
        actor_url = actor.url.strip('/')
        object_url = object.url.strip('/')

        # make api request to see if actor is a follower of object
        endpoint = object_url + '/followers'
        status_code, response_body = api_requests.get(endpoint)

        # check if GET request came back with author object
        if status_code >= 200 and status_code <= 299 and response_body is not None:

            # search list of followers for actor
            found = False
            items = response_body.get("items")
            for author_json in items:
                id = author_json.get("id", "").strip("/")
                if id == actor_url:
                    found = True
                    break


            # record that follow if not already in the system
            if found and not Follow.objects.filter(object=object, actor=actor).exists():
                Follow.objects.create(object=object, actor=actor)
            elif not found and Follow.objects.filter(object=object, actor=actor).exists():
                Follow.objects.filter(object=object, actor=actor).delete()

    except Exception as e:
        logger.error(e, exc_info=True)

    finally:
        logger.info(f"Finished follow update for {actor} --> {object}")
        connection.close()
