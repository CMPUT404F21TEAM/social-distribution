from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from urllib.parse import urlsplit
from cmput404.constants import HOST, API_PREFIX

validate = URLValidator()


class UrlParser():

    def get_host(self, url):
        """ Extract host from url
        """
        o = urlsplit(url)
        host = o.netloc
        return host

    def is_local_url(self, url):
        """ Returns true if url is hosted on the local server. Otherwise, returns false.
        """
        host = self.get_host(url)
        return host == HOST

    def is_valid_url(self, url):
        """ Returns true if valid URL, false otherwise
        """

        try:
            validate(url)
            return True
        except ValidationError:
            return False

    def get_object_type(self, url):
        """ Gets the object type of the url.
        """

        o = urlsplit(url)
        path_components = o.path.strip('/').split('/')
        if path_components[0] == API_PREFIX:
            path_components.pop(0)

        if len(path_components) % 2 != 0:
            # if odd number of path components, cannot be ID of an object
            # e.g. /author/123131/post does not identify a unique post, but /author/123131/post/34423 does
            raise ValueError("URL is not a valid object ID")

        return path_components[-2]

    def parse_author(self, url):
        """ Parse the URL of a local author and return the author_id. Assumes URL is 
            hosted on the local server.
        """

        o = urlsplit(url)
        path_components = o.path.strip('/').split('/')
        if path_components[0] == API_PREFIX:
            path_components.pop(0)

        if len(path_components) != 2 or path_components[0] != "author":
            raise ValueError("URL does not match format of author ID")

        return path_components[1]

    def parse_post(self, url):
        """ Parse the URL of a local post and return the author_id, post_id. Assumes URL is 
            hosted on the local server.
        """

        o = urlsplit(url)
        path_components = o.path.strip('/').split('/')
        if path_components[0] == API_PREFIX:
            path_components.pop(0)

        if len(path_components) != 4 or path_components[0] != "author" or path_components[2] != "posts":
            raise ValueError("URL does not match format of post ID")

        return path_components[1], path_components[3]

    def parse_comment(self, url):
        """ Parse the URL of a local comment and return the author_id, post_id, comment_id. Assumes URL is 
            hosted on the local server.
        """

        o = urlsplit(url)
        path_components = o.path.strip('/').split('/')
        if path_components[0] == API_PREFIX:
            path_components.pop(0)

        if len(path_components) != 6 or path_components[0] != "author" or path_components[2] != "posts" or path_components[4] != "comments":
            raise ValueError("URL does not match format of post ID")

        return path_components[1], path_components[3], path_components[5]


url_parser = UrlParser()
