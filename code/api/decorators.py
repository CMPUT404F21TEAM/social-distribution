from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from socialDistribution.models import LocalAuthor
from .nodes import ALLOWED_NODES
import base64


def authenticate_request(view_func):
    """
        Restrict API path to only {author_id}
    """
    def wrapper_func(request, author_id, *args, **kwargs):
        # check if user f authenticated
        if not request.user.is_authenticated:
            return HttpResponse(status=401)

        author = get_object_or_404(LocalAuthor, user=request.user)

        # check if user is allowed to view resource
        requestId = str(author.id)
        authorId = str(author_id)
        if requestId != authorId:
            return HttpResponse(status=403)

        return view_func(request, author_id, *args, **kwargs)

    return wrapper_func

def validate_node(view_func):
    """
        Restrict to allowed nodes
    """
    def wrapper_func(request, *args, **kwargs):

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_type, _, receivedCredentials = auth_header.partition(' ')

        expectedCredentials = base64.b64encode(b'remotegroup:topsecret!').decode()

        print('\n\n\n\n', request.META['HTTP_HOST'], '\n\n\n\n')
        if request.META['HTTP_HOST'] not in list(ALLOWED_NODES) or token_type != 'Basic' or receivedCredentials != expectedCredentials:
            return HttpResponse(status=401)

        return view_func(request, *args, **kwargs)

    return wrapper_func
