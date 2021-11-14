from typing import List
from typing_extensions import ParamSpecArgs
import requests
import json

from .models import LocalPost, LocalAuthor

def send(post, follower):
    author_inbox = follower.url + "/inbox"
    headers = {
        "Content-Type": "application/json",
    }
    data = post.as_json()

    requests.post(
        url=author_inbox,
        headers=headers,
        data=json.dumps(data)
    )


def dispatch_post(post: LocalPost, recipients: List[LocalAuthor] = None):
    """ Sends a post to the inbox of all followers who have permission to view the post.

    Parameters:
        post (LocalPost): the post to be sent out  
        recipients (QuerySet of LocalAuthor): the list of authors to receive the post if the post is private
    """

    if post.visibility == LocalPost.Visibility.PUBLIC:
        # send posts to all followers
        for follower in post.author.followers.all():
            send(post, follower)

    elif post.visibility == LocalPost.Visibility.FRIENDS:
        print(post.author.friends())
        for friend in post.author.friends():
            send(post, friend)

    elif post.visibility == LocalPost.Visibility.PRIVATE:
        for follower in recipients:
            send(post, follower)
