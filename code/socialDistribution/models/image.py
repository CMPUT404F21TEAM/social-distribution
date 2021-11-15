from django.db import models
from cmput404.constants import HOST
class Image(models.Model):
    '''
    Image model:
        id          Auto-generated id
        caption     Caption (Char)
        image       Image (Uploads to media/images)
    '''
    caption = models.CharField(max_length=50)
    image = models.ImageField(upload_to='images/')

    def get_url(self):
        '''
        Return url of hosted image
        '''
        return f"http://{HOST}/media/{self.image}"