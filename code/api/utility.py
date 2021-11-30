import base64
from datetime import datetime
import json
from django.http.response import HttpResponseBadRequest
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from socialDistribution.models import *

# https://docs.djangoproject.com/en/3.2/topics/pagination/ - Pagination
def getPaginated(data, page, size):
    p = Paginator(data, size)
    try:
        return p.page(page)
    except:
        return []
    
def makeLocalPost(data, author_id, post_id=None):
    """ 
    Creates a LocalPost given json data
    """
    
    # get content type of post
    contentType = data['contentType']
    content = data["content"]
    
    mime_type, subtype = contentType.split('/')
    if mime_type not in ['image', 'application', 'text']:
        raise json.decoder.JSONDecodeError(f'File type {mime_type} is not supported', '', 0)
    
    subtype = subtype.replace(';base64', '').upper()
    PNG = LocalPost.ContentType.PNG
    JPEG = LocalPost.ContentType.JPEG
    if subtype not in ['PLAIN', 'MARKDOWN', PNG, JPEG]:
        if subtype in [PNG, JPEG]:
            content = base64.b64encode(content)
        raise json.decoder.JSONDecodeError(f'Subtype {subtype} is not supported', '', 0)

    contentType = subtype
    content = content.encode('utf-8')
    

    # save the received post as a LocalPost
    received_post = LocalPost(
            author_id=author_id,
            title=data["title"],
            description=data["description"],
            content_type=contentType,
            content=content,
            visibility=LocalPost.Visibility.get_visibility_choice(data["visibility"]),
            unlisted=data["unlisted"],
    )

    # set post origin and source to itself for a new post
    received_post.origin = received_post.source = received_post.get_id()
    if post_id:
        received_post.id = post_id
    received_post.save()

    categories_to_remove = []

    for category in data["categories"]:
        if category != "":
            category_obj, cat_created = Category.objects.get_or_create(
                category__iexact=category,
                defaults={"category": category}
            )
            received_post.categories.add(category_obj)

            # loop condition is always false if post was created
            # because categories_to_remove is an empty list then
            while category_obj.category in categories_to_remove:
                categories_to_remove.remove(category_obj.category)      # don't remove this category

    # won't execute if post was created
    for category in categories_to_remove:
        category_obj = Category.objects.get(category=category)
        received_post.categories.remove(category_obj)

    return received_post
    
def makeInboxPost(data, id=None):
    """ 
    Creates an InboxPost given json data
    """
    # save the received post as an InboxPost
    
    # get content type of post
    contentType = data['contentType']
    content = data["content"]
    
    mime_type, subtype = contentType.split('/')
    if mime_type not in ['image', 'application', 'text']:
        raise json.decoder.JSONDecodeError(f'File type {mime_type} is not supported', '', 0)
    
    subtype = subtype.replace(';base64', '').upper()
    PNG = LocalPost.ContentType.PNG
    JPEG = LocalPost.ContentType.JPEG
    if subtype not in ['PLAIN', 'MARKDOWN', PNG, JPEG]:
        if subtype in [PNG, JPEG]:
            content = base64.b64encode(content)
        raise json.decoder.JSONDecodeError(f'Subtype {subtype} is not supported', '', 0)

    contentType = subtype
    content = content.encode('utf-8')
    
    received_post, post_created = InboxPost.objects.get_or_create(
        public_id=data["id"],
        defaults={
            "title": data["title"],
            "source": data["source"],
            "origin": data["origin"],
            "description": data["description"],
            "content_type": contentType,
            "content": content,
            "author": data["author"]["id"],
            "_author_json": data["author"],
            "published": datetime.fromisoformat(data['published']),
            "visibility": InboxPost.Visibility.get_visibility_choice(data["visibility"]),
            "unlisted": data["unlisted"],
        }
    )

    if not post_created:
        categories_to_remove = [category_obj.category 
            for category_obj in received_post.categories.all()]
    else:
        categories_to_remove = []

    for category in data["categories"]:
        if category != "":
            category_obj, cat_created = Category.objects.get_or_create(
                category__iexact=category,
                defaults={"category": category}
            )
            received_post.categories.add(category_obj)

            # loop condition is always false if post was created
            # because categories_to_remove is an empty list then
            while category_obj.category in categories_to_remove:
                categories_to_remove.remove(category_obj.category)      # don't remove this category

    # won't execute if post was created
    for category in categories_to_remove:
        category_obj = Category.objects.get(category=category)
        received_post.categories.remove(category_obj)

    return received_post