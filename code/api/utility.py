from django.http.response import HttpResponseBadRequest
from django.core.paginator import Paginator

# https://docs.djangoproject.com/en/3.2/topics/pagination/ - Pagination
def getPaginated(data, page, size):
    try:
        if page < 1 or size < 1:
            return HttpResponseBadRequest("Malformed query: page and size must be > 0")
    except:
        return HttpResponseBadRequest("Malformed query")
    p = Paginator(data, size)
    return p.page(page)
