from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/author.html')
def card_author(*args, **kwargs):
    author = kwargs['author']
    profile_card = kwargs['profile_card']
    followed = False
    friend = False
    author_is_user = False

    if profile_card:
        curr_user = kwargs['curr_user']
        followed = curr_user.is_following(author)
        friend = curr_user.is_friends_with(author)
        author_is_user = curr_user.id == author.id

    return {
        'author': author,
        'profile_card': profile_card,
        'followed': followed,
        'friend': friend,
        'author_is_user': author_is_user
    }