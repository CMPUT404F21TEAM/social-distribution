from django import template
from ..models import LocalPost, InboxPost

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/modal.html')
def modal(*args, **kwargs):
    postid = 0
    post_link = ''
    if 'postid' in kwargs:
        postid = kwargs['postid']
        try:
            post = LocalPost.objects.get(id=postid)
            post_link = post.get_local_shareable_link()
        except LocalPost.DoesNotExist:
            post = InboxPost.objects.get(id=postid)
            post_link = 'Remote post'
    return {
            'user': kwargs.get('user'),
            'modal_id': kwargs['id'],
            'modal_type': kwargs['type'],
            'modal_label': kwargs['label'],
            'modal_title': kwargs['title'],
            'submit_btn_text': kwargs['btn'],
            'post_id': postid,
            'post_link': post_link,
        }