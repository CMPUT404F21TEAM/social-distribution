""" This file contains methods that asyncrohonously fetch update data for different data models """

import threading
import logging

import socialDistribution.requests as api_requests
from .models import InboxPost, Category

logger = logging.getLogger(__name__)


def fetch_inbox_post_update(post: InboxPost):
    # only need to update if public post
    if post.visibility == InboxPost.Visibility.PUBLIC:
        return None

    t = threading.Thread(target=update_inbox_post, args=[post.id], daemon=True)
    t.start()
    return t.id


def update_inbox_post(id):
    """ Fetches update about the post for an edit or delete if it is public """
    post = InboxPost.objects.get(id=id)

    # only need to update if public post
    if post.visibility != InboxPost.Visibility.PUBLIC:
        return

    # make api request
    try:
        actor_url = post.author.strip('/')
        object_url = post.public_id.split('/')[-1]
        endpoint = actor_url + '/posts/' + object_url

        status_code, response_body = api_requests.get(endpoint)

        # check if GET request came back with post object
        if status_code == 200 and response_body is not None:
            post.title = response_body['title']
            post.description = response_body['description']

            post.content = response_body['content'].encode('utf-8')
            post.visibility = InboxPost.Visibility.get_visibility_choice(response_body['visibility'])
            post.unlisted = response_body['unlisted']

            if response_body['contentType'] == 'text/plain':
                post.content_type = InboxPost.ContentType.PLAIN
            elif response_body['contentType'] == 'text/markdown':
                post.content_type = InboxPost.ContentType.MARKDOWN
            elif response_body['contentType'] == 'application/base64':
                post.content_type = InboxPost.ContentType.BASE64
            elif response_body['contentType'] == 'image/jpeg;base64':
                post.content_type = InboxPost.ContentType.JPEG
            elif response_body['contentType'] == 'image/png;base64':
                post.content_type = InboxPost.ContentType.PNG

            categories = response_body['categories']

            if categories is not None:
                categories_to_remove = [cat.category for cat in post.categories.all()]

                """
                    This implementation makes category names case-insensitive.
                    This makes handling Category objects cleaner, albeit slightly more
                    involved.
                    """
                for category in categories:
                    category_obj, created = Category.objects.get_or_create(
                        category__iexact=category,
                        defaults={'category': category}
                    )
                    post.categories.add(category_obj)

                    while category_obj.category in categories_to_remove:
                        categories_to_remove.remove(category_obj.category)     # don't remove this category

                for category in categories_to_remove:
                    category_obj = Category.objects.get(category=category)
                    post.categories.remove(category_obj)

            post.save()

        elif status_code == 400 or status_code == 404 or status_code == 410:
            post.delete()

    except Exception as e:
        logger.error(f'Error updating post: {post.title}')
        logger.error(e, exc_info=True)
