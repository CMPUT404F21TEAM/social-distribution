from typing import List
import requests
import json

from .models import LocalPost, Author, LocalAuthor


def dispatch_post(post: LocalPost, recipients: List[LocalAuthor] = None):
    """ Sends a post to the inbox of all followers who have permission to view the post.

    Parameters:
        post (LocalPost): the post to be sent out
        recipients (QuerySet of LocalAuthor): the list of authors to receive the post if the post is private
    """

    if post.visibility == LocalPost.Visibility.PUBLIC:
        # send posts to all followers
        for follower in post.author.followers.all():
            inbox = follower.url + "/inbox"
            send_post(post, inbox)

    elif post.visibility == LocalPost.Visibility.FRIENDS:
        # send posts to friends
        for friend in post.author.get_friends():
            inbox = friend.url + "/inbox"
            send_post(post, inbox)

    elif post.visibility == LocalPost.Visibility.PRIVATE:
        # send posts to private recipients
        for follower in recipients:
            inbox = follower.url + "/inbox"
            send_post(post, inbox)


def send_post(post: LocalPost, url: str):
    """ Sends a post to the given URL via a POST request. """
    
    headers = {
        "Content-Type": "application/json",
    }
    data = post.as_json()

    requests.post(
        url=url,
        headers=headers,
        data=json.dumps(data)
    )


def dispatch_follow_request(actor: LocalAuthor, object: Author):
    """ Sends a follow request to the inbox of another author.

    Parameters:
        actor (LocalAuthor): the local author that is sending the request
        object (Author): the author that is receiving the request
    """

    actor_json = actor.as_json()
    object_json = object.as_json()

    object_inbox = object.url + "/inbox"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "type": "follow",
        "summary": f"{actor_json['displayName']} wants to follow {object_json['displayName']}",
        "actor": actor_json,
        "object": object_json
    }

    requests.post(
        url=object_inbox,
        headers=headers,
        data=json.dumps(data)
    )
