from django.db import models
from uuid import uuid4

# Create your models here.

class Post(models.Model):
    '''
    Post model:
        type            Post type, character field (max length = 20)

        base_url        Base url to which uu_id can be appended to obtain
                        full path to post object
        uu_id           UUID, serves as primary key for Post model, uses uuid4
                        non-editable

        source          Where the post was obtained
        origin          original source
        description     Post description

        content_type    Type of post's content:
                            - markdown
                            - plain text (default)
                            - png
                            - jpeg
                            - base64 (binary data)

        content_text    Actual text-type content
        content_media   Any attached images
        
    '''
    class PostContentType(models.TextChoices):
        MARKDOWN = 'MD', 'text/markdown'
        PLAIN = 'PL', 'text/plain'
        BASE64 = 'B64', 'application/base64'
        PNG = 'PNG', 'image/png;base64'
        JPEG = 'JPEG', 'image/jpeg;base64'

    type = models.CharField(max_length=20)
    base_url = models.URLField(max_length=200)
    uu_id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    source = models.URLField(max_length=200)
    origin = models.URLField(max_length=200)
    description = models.CharField(max_length=50)

    content_type = models.CharField(
        choices=PostContentType.choices, 
        max_length=4,
        default=PostContentType.PLAIN
    )
    
    content_text = models.TextField(_(""))

    # Uploads to MEDIA ROOT uploads/ YEAR/ MONTH
    content_media = models.ImageField(upload_to="uploads/% Y/% m")

    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    categories = models.JSONField(default=list)

    count = models.PositiveSmallIntegerField(default=0)
    size = models.PositiveSmallIntegerField(default=0)
    

    def has_media(self):
        '''
        Check if post has an attached image
        '''
        return self.content_type in [
            self.PostContentType.PNG,
            self.PostContentType.JPEG
        ]