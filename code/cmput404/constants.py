'''
Constants for cmput404 project.

Defines some constants and path prefixes that are used throughout the project.
'''

from decouple import config

SCHEME = config("SCHEME", "http")
HOST = config("HOST", "127.0.0.1:8000")

API_PREFIX = "api"
API_PATH = API_PREFIX + "/"

CLIENT_PREFIX = "app"
CLIENT_PATH = CLIENT_PREFIX  + "/"