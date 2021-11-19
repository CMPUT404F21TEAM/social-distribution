'''
    Manage Node Configurations of remtote groups here.
    
    Server Admins can add nodes by adding domain and remote basic
    auth username/passowrd as an attribute of to the 
    dictionary called ALLOWED_NODES.

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
        http -a remotegroup:topsecret! GET http://example.com/
'''

ALLOWED_NODES = {
    # OUR GROUP 1 - T04
    '127.0.0.1:8000': b'remotegroup:topsecret!',
    # REMOTE GROUP 1 - T11
    '127.0.0.1:8011': b'remotegroup11:anothaSecret!',
    # REMOTE GROUP 2 - T??
    'example.com': b'remotegroup2:meow!'
}
