""" This file contains methods that asyncrohonously fetch update data for different data models """

import threading
import logging

import socialDistribution.requests as api_requests
from .models import *

logger = logging.getLogger(__name__)


def fetch_all_author_updates():
    authors = Author.objects.all()
    for author in authors:
        fetch_author_update(author)


def fetch_author_update(author: Author):
    # don't update if author already up to date
    if author.up_to_date():
        return None

    logger.info("Starting update for {author}")
    t = threading.Thread(target=update_author, args=[author.id], daemon=True)
    t.start()
    return author.id


def update_author(id):
    author = Author.objects.get(id=id)
    status_code, response_body = api_requests.get(author.url.strip("/"))
    if status_code == 200 and response_body is not None:
        author.update_with_json(data=response_body)
    else:
        author.delete()
