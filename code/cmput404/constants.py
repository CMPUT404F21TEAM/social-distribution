'''
Constants for cmput404 project.

Defines some constants and path prefixes that are used throughout the project.
'''

from decouple import config

SCHEME = config("SCHEME", "http")
HOST = config("HOST", "127.0.0.1:8000")

API_PREFIX = "api"
API_PATH = API_PREFIX + "/"
API_BASE = f"{SCHEME}://{HOST}/{API_PREFIX}"

CLIENT_PREFIX = "app"
CLIENT_PATH = CLIENT_PREFIX  + "/"
CLIENT_BASE = f"{SCHEME}://{HOST}/{CLIENT_PREFIX}"

LOCAL = "Local"
REMOTE = "Remote"
STRING_MAXLEN = 255
URL_MAXLEN = 2048

REMOTE_NODES = {
    "t08": "cmput404-bettersocial.herokuapp.com",
    "t11": "cmput404fall21g11.herokuapp.com",
    "t16": "i-connect.herokuapp.com",
    "t20": "cmput404-vgt-socialdist.herokuapp.com"
}