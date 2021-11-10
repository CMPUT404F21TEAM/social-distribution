from django import template

register = template.Library()

# 'How to concatenate strings in django templates?'
# https://stackoverflow.com/questions/4386168/how-to-concatenate-strings-in-django-templates/23783666#23783666 - Roger Dahl
@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)