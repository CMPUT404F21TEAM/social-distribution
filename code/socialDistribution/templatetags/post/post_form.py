from django import template
from socialDistribution.forms import PostForm

register = template.Library()

@register.inclusion_tag('tagtemplates/post_form.html')
def post_form(user_id, post_id):
    '''
        Returns Post Form
    '''
    form = PostForm(user_id=user_id, post_id=post_id)
    return {'form': form}
