from django import template
import base64
from socialDistribution.forms import PostForm
from socialDistribution.models.post import LocalPost, InboxPost
from socialDistribution.utility import make_request

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/post.html')
def post_card(post, author):
    """
        Handles "liking" and "deleting" a post
    """

    # Delete/Edit
    is_author = post.author == author
    is_public = post.is_public()
    is_friends = post.is_friends()

    # if the post is remote, need to fetch likes
    if type(post) is InboxPost:
        post_host = 'remote'
        request_url = post.public_id.strip('/') + '/likes'
        response = make_request('GET', request_url)

        if response.status_code == 200:
            likes_list = response.json()

            for like in likes_list:
                if like['author']['id'] == author.get_url_id():
                    is_liked = True
                    break

            likes = len(likes_list)

        else:
            is_liked = None
            likes = 0

    else:
        post_host = 'local'
        is_liked = post.likes.filter(author=author).exists()
        likes = post.total_likes()

    # Likes
    like_text = ''
    if is_liked:
        likes -= 1
        if likes >= 2:
            like_text = f'Liked by you and {likes} others'
        elif likes == 1:
            like_text = f'Liked by you and 1 other'
        else:
            like_text = f'Liked by you'
    else:
        if likes > 1:
            like_text = f'Liked by {likes} others'
        elif likes == 1:
            like_text = f'Liked by 1 other'

    content_media = None
    # if post.content_media is not None:
    #     content_media = post.content_media.decode('utf-8')

    return {
        'post': post, 
        'content_media': content_media,
        'post_host': post_host,
        'is_author': is_author, 
        'is_liked': is_liked, 
        'like_text': like_text,        
        'is_public': is_public,
        'is_friends': is_friends
        }
