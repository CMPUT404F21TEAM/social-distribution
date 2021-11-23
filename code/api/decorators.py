from django.http import HttpResponse
from django.http.response import HttpResponseServerError
from django.shortcuts import get_object_or_404
from .models import Node
from socialDistribution.models import LocalAuthor
from .node_manager import node_manager
import base64
import logging

logger = logging.getLogger(__name__)

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
        
        # extract token and decode username,password
        try:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            token_type, _, receivedCredentials = auth_header.partition(' ')
            splitCredentials = base64.b64decode(receivedCredentials).decode().split(':')
            username = splitCredentials[0]

            credentials = node_manager.get_credentials(username=username, remote_credentials=False)
            expectedCredentials = base64.b64encode(credentials).decode()
        except Exception as e:
            logger.error(str(e))
            return HttpResponseServerError()

        if not credentials or token_type != 'Basic' or receivedCredentials != expectedCredentials:
            return HttpResponse(status=401)

        return view_func(request, *args, **kwargs)

    return wrapper_func
