from django.http.response import HttpResponseBadRequest

# https://stackoverflow.com/a/3950103 - RichieHindle
def paginate(data, size):
    """ Divides a list into 'size' pages """
    return [data[i:i+size] for i in range(0, len(data), size)]

def getPaginated(data, page, size):
    try:
        if page < 1 or size < 1:
            return HttpResponseBadRequest("Malformed query: page and size must be > 0")
    except:
        print('hi')
        return HttpResponseBadRequest("Malformed query")
    page -= 1
    # collect data based on query
    paginated = paginate(data, size)
    # return the last page if specified page is too large
    if page > len(paginated) - 1:
        data = paginated[-1]
    else:
        data = paginate(data, size)[page]
    return data