import requests
import json

def get(url):
    """ Makes a GET request at the given URL. """
    
    response = requests.get(url)
    json_data = json.loads(response.content)
    return json_data