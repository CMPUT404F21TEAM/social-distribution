from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/author.html')
def card_author(*args, **kwargs):
    author = kwargs['author']
    author_type = kwargs['author_type']
    profile_card = kwargs['profile_card']
    only_following = False
    is_friend = False
    accept_friend = False
    author_is_user = False

    if profile_card:
        curr_user = kwargs['curr_user']
        only_following = curr_user.is_only_following(author)
        is_friend = curr_user.is_friends_with(author)
        accept_friend = author.is_only_following(curr_user)
        author_is_user = curr_user.id == author.id

    return {
        'author': author,
        'author_type': author_type,
        'profile_card': profile_card,
        'only_following': only_following,
        'is_friend': is_friend,
        'accept_friend': accept_friend,
        'author_is_user': author_is_user
    }