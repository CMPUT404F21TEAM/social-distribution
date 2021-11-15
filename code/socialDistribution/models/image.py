from django.db import models

class Image(models.Model):
    '''
    Image model:
        id          Auto-generated id
        caption     Caption (Char)
        image       Image (Uploads to media/images)
    '''
    caption = models.CharField(max_length=50)
    image = models.ImageField(upload_to='images/')