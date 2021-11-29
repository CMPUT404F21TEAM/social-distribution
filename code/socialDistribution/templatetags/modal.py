from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/modal.html')
def modal(*args, **kwargs):

    return {
            'user': kwargs.get('user'),
            'modal_id': kwargs['id'],
            'modal_type': kwargs['type'],
            'modal_label': kwargs['label'],
            'modal_title': kwargs['title'],
            'submit_btn_text': kwargs['btn'],
            'post_id': kwargs.get("postid"),
        }