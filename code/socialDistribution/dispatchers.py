from typing import List
from typing_extensions import ParamSpecArgs
import requests
import json

from .models import LocalPost, LocalAuthor


def dispatch_post(post: LocalPost, recipients: List[LocalAuthor] = None):
    """ Sends a post to the inbox of all followers who have permission to view the post.

    Parameters:
        post (LocalPost): the post to be sent out  
        recipients (QuerySet of LocalAuthor): the list of authors to receive the post if the post is private
    """

    if post.visibility == LocalPost.Visibility.PUBLIC:
        # send posts to all followers
        for follower in post.author.followers.all():
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

    elif post.visibility == LocalPost.Visibility.FRIENDS:
        # TODO
        pass

    elif post.visibility == LocalPost.Visibility.PRIVATE:
        for follower in recipients:
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
