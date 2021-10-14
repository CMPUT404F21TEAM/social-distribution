from django import template

register = template.Library()


@register.inclusion_tag('tagtemplates/post.html')
def card_post(post, author):
    isLiked = False
    likeText = ''
    likes = post.total_likes()
    if post.likes.filter(id=author.id).exists():
        likes -= 1
        isLiked = True
        if likes >= 2:
            likeText = f'Liked by you and {likes} others'
        elif likes == 1:
            likeText = f'Liked by you and 1 other'
        else:
            likeText = f'Liked by you'
    else:
        likes = post.likes.count()
        if likes > 1:
            likeText = f'Liked by {likes} others'
        elif likes == 1:
            likeText = f'Liked by 1 other'
    return {'post': post, 'isLiked': isLiked, 'likeText': likeText}


@register.inclusion_tag('tagtemplates/post_form.html')
def post_form():
    return {}
