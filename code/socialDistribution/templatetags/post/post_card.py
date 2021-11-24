from django import template
import base64
from socialDistribution.models.post import Post, InboxPost
from socialDistribution.utility import get_post_like_info, get_like_text

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

    if type(post) is InboxPost:
        post_host = 'remote'
        post.fetch_update()
    else:
        post_host = 'local'
    
    is_liked, likes = get_post_like_info(post, author)
    like_text = get_like_text(is_liked, likes)
    
    return {
        'post': post,
        'post_host': post_host,
        'is_author': is_author, 
        'is_liked': is_liked, 
        'like_text': like_text,        
        'is_public': is_public,
        'is_friends': is_friends
        }
