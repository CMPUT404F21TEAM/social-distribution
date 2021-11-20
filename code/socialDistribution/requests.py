""" File that contains wrapper methods for all API HTTP requests. Use this file for makeing GET, POST, PUT, 
    DELETE, etc requests to any social distribution API server. Functions in this file just act as a wrapper for 
    adding appropriate headers and parsing the response as JSON.
"""

import requests
import json
import logging 

# Django Software Foundation, "Logging", https://docs.djangoproject.com/en/3.2/topics/logging/
logger = logging.getLogger(__name__)


def get(url, params=None):
    """ Makes a GET request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)

        Returns:
         - (int): Status code to the HTTP response
         - (dict): JSON response data if status code of request is 200 OK and JSON parsing was successful. Otherwise, return None
    """

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=params)

    # parse JSON response if OK
    try:
        if response.status_code == 200:
            response_data = response.json()
        else:
            response_data = None
    except json.decoder.JSONDecodeError:
        response_data = None

    logger.info(f"API GET request to {url} and received {response.status_code}")

    return response.status_code, response_data


def post(url, params=None, data={}):
    """ Makes a POST request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)
         - data (dict): Request parameters to send in JSON body (default is {})

        Returns:
         - (int): Status code to the HTTP response
         - (dict): JSON response data if status code of request is 200 OK and JSON parsing was successful. Otherwise, return None
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    
    # parse JSON response if OK
    try:
        if response.status_code == 200:
            response_data = response.json()
        else:
            data = None
    except json.decoder.JSONDecodeError:
        response_data = None
    
    logger.info(f"API POST request to {url} and received {response.status_code}")

    return response.status_code, response_data
