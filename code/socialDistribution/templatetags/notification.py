from django import template

register = template.Library()

# Django Software Foundation, "Custom Template tags and Filters", 2021-10-10
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#inclusion-tags
@register.inclusion_tag('tagtemplates/notification_card.html')
def friend_card(sender):
    """
        Handle people who send you friend requests
    """
    action_link = 'socialDistribution:friend-request'

    sender_json = sender.as_json()
    
    displayName = "'Name Unavailable'"
    if sender_json and "displayName" in sender_json:
        displayName = sender_json["displayName"]

    return {
        'header': f'{displayName} wants to follow you',
        'sender': sender,
        'action_link': action_link
    }