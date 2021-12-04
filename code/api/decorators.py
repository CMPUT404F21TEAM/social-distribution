from django.http import HttpResponse
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from .models import Node
from socialDistribution.models import LocalAuthor
from .node_manager import node_manager
import base64
import logging

logger = logging.getLogger(__name__)

def validate_user(view_func):
    """
        Restrict API path to only {author_id}
    """
    def wrapper_func(request, author_id, *args, **kwargs):
        
        try:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header is None:
                return HttpResponse(status=401)
            token_type, _, receivedCredentials = auth_header.partition(' ')
            username, password = base64.b64decode(receivedCredentials).decode().split(':')

            # Django Software Foundation, "Authenticating users", 2021-12-04
            # https://docs.djangoproject.com/en/3.2/topics/auth/default/#authenticating-users
            user = authenticate(username=username, password=password)
            if token_type != 'Basic' or user is None:
                response = HttpResponse(status=401)
                response.headers['WWW-Authenticate'] = "Basic realm='myRealm', charset='UTF-8'"
                return response

            # check if user matches the requested author
            author = LocalAuthor.objects.get(user=user)
            if author.id != author_id:
                return HttpResponseForbidden()


        except Exception as e:
            return HttpResponseBadRequest()

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
            logger.error(e)
            return HttpResponseServerError()

        if not credentials or token_type != 'Basic' or receivedCredentials != expectedCredentials:
            response = HttpResponse(status=401)
            response.headers['WWW-Authenticate'] = "Basic realm='myRealm', charset='UTF-8'"
            return response

        return view_func(request, *args, **kwargs)

    return wrapper_func