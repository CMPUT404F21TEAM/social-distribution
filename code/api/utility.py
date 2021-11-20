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
    
def makePost(author_id, data):
    # get owner of inbox
    receiving_author = get_object_or_404(LocalAuthor, id=author_id)

    # save the received post as an InboxPost
    received_post, post_created = InboxPost.objects.get_or_create(
        public_id=data["id"],
        defaults={
            "title": data["title"],
            "source": data["source"],
            "origin": data["origin"],
            "description": data["description"],
            "content_type": data["contentType"],
            "content": data["content"],
            # "categories": data["categories"],
            "author": data["author"]["id"],
            "_author_json": data["author"],
            "published": data["published"],
            "visibility": data["visibility"],
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

    # add post to inbox of author
    receiving_author.inbox_posts.add(received_post)