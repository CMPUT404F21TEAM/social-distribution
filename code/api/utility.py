# https://stackoverflow.com/a/3950103 - RichieHindle
def paginate(data, size):
    """ Divides a list into 'size' pages """
    return [data[i:i+size] for i in range(0, len(data), size)]