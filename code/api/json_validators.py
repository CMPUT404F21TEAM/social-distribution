import logging

from .parsers import url_parser
from .adapters import team11adapter_post

logger = logging.getLogger("api")


def validate_post_json(data):
    """ Validates post JSON sent by a remote server. If JSON is valid, or we are able to adapt to it, 
        returns that JSON object. Otherwise, return None
    """
    if data is None:
        return None 

    if not url_parser.is_valid_url(data.get("id")):

        # try team 11 adapter
        adapted_data = team11adapter_post(data)
        if adapted_data is not None:
            logger.info("Used T11 adapter for posts")
            data = adapted_data
        else:
            # Can't parse this post
            return None

    if data.get("title") is None:
        data["title"] = "No title"

    return data
