from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from .models import Author

# ref: https://www.youtube.com/watch?v=eBsc65jTKvw&list=PL-51WBLyFTg2vW-_6XBoUpE7vpmoR3ztO&index=15 - Dennis Ivy
def unauthenticated_user(view_func):
    """
        Restrict to only if user is not authenticated
    """
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            author_id = Author.objects.get(user=request.user).id
            return redirect('socialDistribution:home', author_id=author_id)
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func

def allowedUsers(allowed_roles=[]):
    """
        Authrorize user group
    """
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):

            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles or group == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse('You are not authroized to view this page.')
        
        return wrapper_func
    return decorator

def restrictOtherAuthors(view_func):
    """
        Only allow the authenticated user to access personal routes
    """
    def wrapper_func(request, *args, **kwargs):
        author_id = get_object_or_404(Author, user=request.user).id

        # proceed to view if id matches
        if (author_id == kwargs['author_id']):
            return view_func(request, *args, **kwargs)
        else:
            # Todo: Add message indicating not allowed
            return redirect('socialDistribution:home', author_id=author_id)

    return wrapper_func
