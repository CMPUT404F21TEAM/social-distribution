from django import template

from socialDistribution.utility import get_comment_like_info, get_like_text

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/comment.html')
def comment_card(*args, **kwargs):
    '''
        Setup comment card data
    '''
    # current user (LocalAuthor)
    author = kwargs['author']

    # comment json (dict)
    comment = kwargs['comment']

    # author of the comment (Author)
    comment_author = comment["comment_author_object"]

    # reference post (InboxPost or LocalPost)
    post = kwargs['post']

    # is current user friends with the commenter?
    is_friend = author.has_friend(comment_author)

    # comment like data
    is_liked, likes = get_comment_like_info(comment["id"], author)
    like_text = get_like_text(is_liked, likes)

    return {
        'author': author,
        'comment': comment,
        'post': post,
        'is_friend': is_friend,
        'is_liked': is_liked,
        'like_text': like_text
    }