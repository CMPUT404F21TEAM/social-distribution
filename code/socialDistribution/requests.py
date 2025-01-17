""" File that contains wrapper methods for all API HTTP requests. Use this file for making GET, POST, PUT,
    DELETE, etc requests to any social distribution API server. Functions in this file just act as a wrapper for
    adding appropriate headers and parsing the response as JSON.
"""

import requests
import json
import logging
import base64

from api.node_manager import node_manager
from api.parsers import url_parser

TIMEOUT = 5

def parse_res_to_dict(response):
    """ 
    Checks if response is a list.
    If it is list, converts it to an object with an 'items' field
    that has the list as value. Finally, returns the object

    Otherwise, returns response
    """

    if type(response) is list:
        return { "items": response }

    else:
        return response

# Django Software Foundation, "Logging", https://docs.djangoproject.com/en/3.2/topics/logging/
logger = logging.getLogger(__name__)

def add_auth_header(url, headers):
    '''
        Add Auth Header for node to headers dict
    '''
    host = url_parser.get_host(url)
    auth_credentials = node_manager.get_credentials(host=host, remote_credentials=True)
    if (auth_credentials):
        authToken = base64.b64encode(auth_credentials).decode("ascii")
        headers['Authorization'] = 'Basic %s' % authToken


def get(url, params=None, send_basic_auth_header=True):
    """ Makes a GET request at the given URL and returns the JSON body of the HTTP response.

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)

        Returns:
         - (int): Status code of the HTTP response
         - (dict): JSON response data if status code of request is 200 OK and JSON parsing was successful. Otherwise, return None
    """

    headers = {
        "Accept": "application/json"
    }

    # Add Basic Auth Header
    if send_basic_auth_header:
        add_auth_header(url, headers)

    # ref: https://stackoverflow.com/questions/15431044/can-i-set-max-retries-for-requests-request - datashaman
    # 'Can I set max_retries for requests.request?'
    try:
        logger.info(f"Trying to do GET request to {url}")

        # timeout here since may need to wake up other groups heroku servers
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        # parse JSON response if OK
        if response.status_code == 200:
            try:
                response_data = response.json()
            except json.decoder.JSONDecodeError:
                response_data = None
        else:
            response_data = None

        logger.info(f"API GET request to {url} and received {response.status_code}")

    except Exception as error:
        logger.error(f"Something went wrong GET'ing {url}")
        logger.error(error, exc_info=True)
        status_code = 500
        response_data = None
        return status_code, response_data

    # caller should check status codes show error message to user (if needed)
    return response.status_code, parse_res_to_dict(response_data)


def post(url, params=None, data={}, send_basic_auth_header=True):
    """ Makes a POST request at the given URL and returns the JSON body of the HTTP response.

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)
         - data (dict): Request parameters to send in JSON body (default is {})

        Returns:
         - (int): Status code of the HTTP response
         - (dict): JSON response data if status code of request is 200 OK and JSON parsing was successful. Otherwise, return None
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Add Basic Auth Header specific to a node for Inbox api
    if send_basic_auth_header:
        add_auth_header(url, headers)

    try:
        logger.info(f"Trying to do POST request to {url}")
        response = requests.post(url, headers=headers, params=params, json=data, timeout=TIMEOUT)

        # parse JSON response if OK
        if response.status_code == 200:
            try:
                response_data = response.json()
            except json.decoder.JSONDecodeError:
                response_data = None
        else:
            response_data = None

        logger.info(f"API POST request to {url} and received {response.status_code}")

    except Exception as error:
        logger.error(f"Something went wrong POST'ing {url}")
        logger.error(error, exc_info=True)
        status_code = 500
        response_data = None
        return status_code, response_data

    # caller should check status codes show error message to user (if needed)
    return response.status_code, response_data

def delete(url, params=None, send_basic_auth_header=True):
    """ Makes a DELETE request at the given URL and returns the JSON body of the HTTP response.

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)

        Returns:
         - (int): Status code of the HTTP response
         - (dict): JSON response data if status code of request is 200 OK and JSON parsing was successful. Otherwise, return None
    """

    headers = {
        "Accept": "application/json"
    }

    # Add Basic Auth Header specific to a node for Inbox api
    if send_basic_auth_header:
        add_auth_header(url, headers)

    try:
        # ref: https://stackoverflow.com/questions/15431044/can-i-set-max-retries-for-requests-request - datashaman
        # 'Can I set max_retries for requests.request?'
        response = requests.delete(url, headers=headers, params=params, timeout=TIMEOUT)

        # parse JSON response if OK
        if response.status_code == 200:
            try:
                response_data = response.json()
            except json.decoder.JSONDecodeError:
                response_data = None
        else:
            response_data = None

        logger.info(f"API DELETE request to {url} and received {response.status_code}")

    except Exception as error:
        logger.error(f"Something went wrong DELETE'ing {url}")
        logger.error(error, exc_info=True)
        status_code = 500
        response_data = None
        return status_code, response_data

    # caller should check status codes show error message to user (if needed)
    return response.status_code, response_data
