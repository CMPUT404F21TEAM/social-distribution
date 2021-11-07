from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/github_event_card.html')
def card_gh_event(github_event):
    return {'github_event_descr': github_event[0], 'timeago': github_event[1]}