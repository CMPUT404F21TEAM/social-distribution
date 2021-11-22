from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/comment.html')
def comment_card(*args, **kwargs):
    '''
        Setup comment card data
    '''
    author = kwargs['author']
    author_type = kwargs['author_type']
    comment = kwargs['comment']
    post = kwargs['post']
    is_friend = author.has_friend(comment.author)

    # manage comment like data
    is_liked = comment.likes.filter(author=author).exists()

    like_text = ''
    likes = comment.total_likes()
    if is_liked:
        likes -= 1
        if likes >= 2:
            like_text = f'Liked by you and {likes} others'
        elif likes == 1:
            like_text = f'Liked by you and 1 other'
        else:
            like_text = f'Liked by you'
    else:
        likes = comment.likes.count()
        if likes > 1:
            like_text = f'Liked by {likes} others'
        elif likes == 1:
            like_text = f'Liked by 1 other'

    return {
        'author': author,
        'author_type': author_type,
        'comment': comment,
        'post': post,
        'is_friend': is_friend,
        'is_liked': is_liked,
        'like_text': like_text
    }