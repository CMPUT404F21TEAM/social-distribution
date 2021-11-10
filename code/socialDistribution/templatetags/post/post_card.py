from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/post.html')
def post_card(post, author):
    """
        Handles "liking" and "deleting" a post
    """

    # Delete/Edit
    isAuthor = post.author == author
    isPublic = post.is_public()

    # Likes
    isLiked = post.likes.filter(author=author).exists()
    likeText = ''
    likes = post.total_likes()
    if isLiked:
        likes -= 1
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

    content_media = None
    if post.content_media is not None:
        content_media = post.content_media.decode('utf-8')

    return {
        'post': post, 
        'content_media': content_media, 
        'isAuthor': isAuthor, 
        'isLiked': isLiked, 
        'likeText': likeText,        
        'isPublic': isPublic,
        }
