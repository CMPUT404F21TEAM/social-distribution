from django import template

from socialDistribution.fetchers import fetch_follow_update
from socialDistribution.models import Follow

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags


@register.inclusion_tag('tagtemplates/author.html')
def card_author(*args, **kwargs):
    """
        Returns info relevant to an author comment 
    """
    author = kwargs['author']
    author_type = kwargs['author_type']
    curr_user = kwargs['curr_user']

    is_following = curr_user.is_following(author)
    request_sent = author.has_follow_request(curr_user)
    is_friend = curr_user.has_friend(author)

    author_is_user = author.get_url_id() == curr_user.get_url_id()

    # update the follow of author on the current user if exists
    try:
        follow = curr_user.follows.get(actor=author)
        fetch_follow_update(follow)
    except Follow.DoesNotExist:
        pass

    try:
        follow = curr_user.following.get(object=author)
        fetch_follow_update(follow)
    except Follow.DoesNotExist:
        pass

    return {
        'author': author,
        'author_type': author_type,
        'is_following': is_following,
        'request_sent': request_sent,
        'is_friend': is_friend,
        'author_is_user': author_is_user
    }
