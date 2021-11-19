from .models import LocalPost
from json import JSONDecodeError
import requests

# make an http requests and handle status codes
def make_request(method='GET', url='http://127.0.0.1:8000/', body=''):
    """
    Makes an HTTP request
    """
    r = None
    if method == 'GET':
        r = requests.get(url)
    elif method == 'POST':
        r = requests.post(url, data=body)
    
    return r


def get_post_like_info(post, author):
    """
    Returns a boolean indicating whether the author parameter
    liked the post parameter and an integer representing the
    number of likes on the post parameter

    If an error occurs, it returns None and 0
    """
    if type(post) is LocalPost:
        is_liked = post.likes.filter(author=author).exists()
        likes_count = post.total_likes()
        return is_liked, likes_count

    else:
        request_url = post.public_id.strip('/') + '/likes'
        response = make_request('GET', request_url)

        if response.status_code == 200:
            try:
                likes_list = response.json()
            except JSONDecodeError:
                return None, 0

            else:
                is_liked = False
                for like in likes_list:
                    if like['author']['id'] == author.get_url_id():
                        is_liked = True
                        break

                return is_liked, len(likes_list)

        else:
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
        likes_count  -= 1
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