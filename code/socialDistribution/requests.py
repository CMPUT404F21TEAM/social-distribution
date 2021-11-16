import requests
import json


def get(url, params=None):
    """ Makes a GET request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)

        Returns:
         - (dict): JSON response data if status code of request is 200 OK. Otherwise, return None
    """

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def post(url, params=None, body={}):
    """ Makes a POST request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)
         - body (dict): Request parameters to send in JSON body (default is {})

        Returns:
         - (dict): JSON response data if status code of request is 200 OK. Otherwise, return None
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, params=params, json=body)

    if response.status_code == 200:
        return response.json()
    else:
        return None
