import requests
import json

from .models import LocalPost


def dispatch_post(post: LocalPost):
    """ Sends a post to the inbox of all followers who have permission to view the post.

    Parameters:
        post (LocalPost): the post to be sent out  
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
