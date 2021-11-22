from typing import List


import socialDistribution.requests as api_requests
from .models import LocalPost, Author, LocalAuthor

def update_post(post: LocalPost, url: str):
    """ Sends a post to the given URL via a POST request. """

    data = post.as_json()
    api_requests.post(url=url, data=data, sendBasicAuthHeader=True)    


def send_post(post: LocalPost, url: str):
    """ Sends a post to the given URL via a POST request. """

    data = post.as_json()
    api_requests.post(url=url, data=data, sendBasicAuthHeader=True)

actions = {'send': send_post,
           'update': update_post
        }

def get_url(method, post, follower):
    if method == 'send':
        return follower.get_inbox()
    elif method == 'update':
        return post.id


def dispatch_post(post: LocalPost, recipients: List[LocalAuthor] = None, method='send'):
    """ Sends a post to the inbox of all followers who have permission to view the post.

    Parameters:
        post (LocalPost): the post to be sent out
        recipients (QuerySet of LocalAuthor): the list of authors to receive the post if the post is private
    """

    if post.visibility == LocalPost.Visibility.PUBLIC:
        # send posts to all followers
        for follower in post.author.get_followers():
            url = get_url(method, post, follower)
            actions[method](post, url)

    elif post.visibility == LocalPost.Visibility.FRIENDS:
        # send posts to friends
        for friend in post.author.get_friends():
            url = get_url(method, post, follower)
            actions[method](post, url)

    elif post.visibility == LocalPost.Visibility.PRIVATE:
        # send posts to private recipients
        for follower in recipients:
            url = get_url(method, post, follower)
            actions[method](post, url)

def dispatch_follow_request(actor: LocalAuthor, object: Author):
    """ Sends a follow request to the inbox of another author.

    Parameters:
        actor (LocalAuthor): the local author that is sending the request
        object (Author): the author that is receiving the request
    """

    actor_json = actor.as_json()
    object_json = object.as_json()

    object_inbox = object.get_inbox()

    data = {
        "type": "follow",
        "summary": f"{actor_json['displayName']} wants to follow {object_json['displayName']}",
        "actor": actor_json,
        "object": object_json
    }

    api_requests.post(url=object_inbox, data=data, sendBasicAuthHeader=True)
