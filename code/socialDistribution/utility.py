import socialDistribution.requests as api_requests
from .models import LocalPost

import logging

logger = logging.getLogger(__name__)


def get_post_like_info(post, author):
    """
    Returns a boolean indicating whether the author parameter
    liked the post parameter and an integer representing the
    number of likes on the post parameter

    If an error occurs, it returns None and 0
    """

    try:
        if type(post) is LocalPost:
            is_liked = post.likes.filter(author=author).exists()
            likes_count = post.total_likes()
            return is_liked, likes_count

        else:
            request_url = post.public_id.strip('/') + '/likes'
            status_code, response_body = api_requests.get(request_url)

            if status_code == 200 and response_body is not None:
                likes_list = response_body["items"]

                is_liked = False
                for like in likes_list:
                    if like['id'] == author.get_url_id():
                        is_liked = True
                        break

                return is_liked, len(likes_list)

            else:
                return None, 0
    except Exception as e:
        logger.error(e, exc_info=True)
        return None, 0

def get_comment_like_info(comment_id, author):
    """
    Returns a boolean indicating whether the author parameter
    liked the comment with id of comment_id, and an integer representing the
    number of likes on the comment

    If an error occurs, it returns None and 0
    """
    try:
        print(__name__)
        request_url = comment_id.strip('/') + '/likes'
        status_code, response_body = api_requests.get(request_url)

        if status_code == 200 and response_body is not None:
            likes_list = response_body["items"]

            is_liked = False
            for like in likes_list:
                if like['author']['id'] == author.get_url_id():
                    is_liked = True
                    break

            return is_liked, len(likes_list)

        else:
            return None, 0
    except Exception as e:
        logger.error(e, exc_info=True)
        return None, 0



def get_like_text(is_liked, likes_count):
    """
    Returns a text description of the likes

    is_liked is True if the user liked the object for
    which the description is being returned

    likes_count is the number of the likes on the object
    for which the description is being returned
    """
    like_text = ''
    if is_liked:
        likes_count -= 1
        if likes_count >= 2:
            like_text = f'Liked by you and {likes_count} others'
        elif likes_count == 1:
            like_text = f'Liked by you and 1 other'
        else:
            like_text = f'Liked by you'
    else:
        if likes_count > 1:
            like_text = f'Liked by {likes_count} others'
        elif likes_count == 1:
            like_text = f'Liked by 1 other'

    return like_text