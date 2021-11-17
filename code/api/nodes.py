'''
    Manage Nodes Configurations of remtote groups here.
    Server Admins can add nodes adding domains to the 
    list called ALLOWED_NODES.

    Requests sent to the inbox will
    be processed only if it is from the allowed nodes.

    These credentials (should be in README.md) will be
    used by remote groups to send requests: 
        username: remotegroup
        password: topsecret!

    Requests will have to sent like this
        userAndPass = b64encode(b"remotegroup:topsecret!").decode("ascii")

        headers = { 'Authorization' : 'Basic %s' %  userAndPass }

        requests.post(
            url=author_inbox,
            headers=headers,
            ...
        )

    Test using:
        http -a remotegroup:topsecret! GET http://127.0.0.1:8000/api/authors/
'''

ALLOWED_NODES = [
    # OUR GROUP 1 - T04
    '127.0.0.1:8000',
    # REMOTE GROUP 1 - T11
    '127.0.0.1:8011',
    # REMOTE GROUP 2 - T??
    'example.com'
]