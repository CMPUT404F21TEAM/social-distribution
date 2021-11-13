import requests
import json


def get(url, params=None):
    """ Makes a GET request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)
    """

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def post(url, params=None, body={}):
    """ Makes a POST request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)
         - body (dict): Request parameters to send in JSON body (default is {})
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, params=params, json=body)
    return response.json()
