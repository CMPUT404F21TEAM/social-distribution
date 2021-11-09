import requests, timeago
from datetime import timezone, datetime
from .github_events import EventFactory

REQUEST_URL = "https://api.github.com/users/{github_user}/events"

event_factory = EventFactory()

def get_event_description(event_name, event_data):
    github_event = event_factory.get_event(event_name)
    github_event.set_event_data(event_data)
    
    return github_event.get_description(), github_event.time_ago()


def pull_github_events(github_user):
    response = requests.get(
            REQUEST_URL.format(github_user = github_user),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "request"
                }
        )

    if response.status_code == 200:
        events_json = response.json()
        return [get_event_description(
            event.get("type"),
            event
        ) for event in events_json]

    return None