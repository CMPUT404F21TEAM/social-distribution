from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/comment.html')
def comment_card(*args, **kwargs):
    '''
        Setup comment card data
    '''
    author_type = kwargs['author_type']
    comment = kwargs['comment']

    return {
        'author_type': author_type,
        'comment': comment
    }