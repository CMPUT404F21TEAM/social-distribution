import requests, base64

# make an http requests and handle status codes
def make_request(method='GET', url='http://127.0.0.1:8000/', body='', headers=None):
    """
    Makes an HTTP request
    """
    r = None
    if method == 'GET':
        r = requests.get(url)
    elif method == 'POST':
        authToken = base64.b64encode(b"remotegroup:topsecret!").decode("ascii")

        if headers:
            headers['Authorization'] = 'Basic %s' %  authToken
        
        r = requests.post(url, data=body, headers=headers)
    #todo: handle status codes