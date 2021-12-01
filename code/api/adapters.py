# why does this file even need to exist

from .parsers import url_parser


def team11adapter_post(bad_json):
    """ Fix Post JSON from Team 11"""

    # Fix the following
    # {
    # "type": "post",
    # "id": "e1feee88796d44ba8ba5e94fb4a29431",
    # "contentType": "text/markdown",
    # "title": "Sample post",
    # "source": "http://cmput404fall21g11.herokuapp.com/newpost/",
    # "origin": "http://cmput404fall21g11.herokuapp.com/newpost/",
    # "description": "A post",
    # "content": "Hello everyone! **wow**",
    # "author": {
    #     "type": "author",
    #     "id": "http://cmput404fall21g11.herokuapp.com/api/author/f82aec23-03ad-42e9-8e53-19a82dfdaedf/",
    #     "uuid": "f82aec23-03ad-42e9-8e53-19a82dfdaedf",
    #     "displayName": "team04test",
    #     "profileImage": "",
    #     "email": "dbecerra@ualberta.ca",
    #     "github": "",
    #     "host": "cmput404fall21g11.herokuapp.com",
    #     "url": "http://cmput404fall21g11.herokuapp.com/api/author/f82aec23-03ad-42e9-8e53-19a82dfdaedf/"
    # },
    # "categories": "['public']",
    # "count": 0,
    # "published": "2021-11-29T02:29:02.251192Z",
    # "updated": "2021-11-29T02:29:02.251216Z",
    # "visibility": 1,
    # "image": null,
    # "comments": [],
    # "url": "http://cmput404fall21g11.herokuapp.com/api/author/f82aec23-03ad-42e9-8e53-19a82dfdaedf/posts/e1feee88796d44ba8ba5e94fb4a29431/"
    # }

    json = bad_json.copy()

    if not url_parser.is_valid_url(json.get("id")):
        if url_parser.is_valid_url(json.get("url")):
            json["id"] = json.get("url")
        else:
            # rage quit
            return None

    if type(json.get("visibility")) != str:
        json["visibility"] = "PUBLIC"

    if json.get("unlisted") is None:
        json["unlisted"] = False

    return json
