""" File that contains wrapper methods for all API HTTP requests. Use this file for making GET, POST, PUT, 
    DELETE, etc requests to any social distribution API server. Functions in this file just act as a wrapper for 
    adding appropriate headers and parsing the response as JSON.
"""

import requests
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from api.node_manager import node_manager
import base64
from api.parsers import url_parser
from cmput404.constants import *

logger = logging.getLogger(__name__)

def get(url, params=None):
    """ Makes a GET request at the given URL and returns the JSON body of the HTTP response. 

        Parameters:
         - url (string): The URL endpoint for the HTTP request
         - params (dict): The query string parameters (default is None)

        Returns:
         - (dict): JSON response data if status code of request is 200 OK. Otherwise, return None
    """
    requests.adapters.HTTPAdapter
    headers = {
        "Accept": "application/json"
    }

    # ref: https://stackoverflow.com/questions/15431044/can-i-set-max-retries-for-requests-request - datashaman
    # 'Can I set max_retries for requests.request?'
    session = requests.Session()

    retries = Retry(total=2,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    
    session.mount(url, HTTPAdapter(max_retries=retries))

    response = session.get(url, headers=headers, params=params)

    # TODO Fine tune response handling, do error handling / status code checks
    if response.status_code == 200:
        return response.json()
    else:
        return None


def post(url, params=None, body={}, sendBasicAuthHeader=False):
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
        "Accept": "application/json",
        "REFERER": HOST
    }

    
    # Add Basic Auth Header specific to a node for Inbox api 
    host = url_parser.get_host(url)
    auth_credentials = node_manager.get_host_credentials(host)
    if (sendBasicAuthHeader and auth_credentials):
        authToken = base64.b64encode(auth_credentials).decode("ascii")
        headers['Authorization'] = 'Basic %s' %  authToken
    
    try:
        response = requests.post(url, headers=headers, params=params, json=body)

        if response.status_code == 200:
            return response.json() 
        
        return None
    
    except Exception as error:
        logger.error(error, exc_info=True)
    
    # TODO Fine tune response handling, do error handling / status code checks
    # caller should wrap in try and catch show error message to user
