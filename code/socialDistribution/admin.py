from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Author)
admin.site.register(LocalAuthor)
admin.site.register(LocalPost)
admin.site.register(InboxPost)
admin.site.register(Comment)
admin.site.register(PostLike)
admin.site.register(CommentLike)
admin.site.register(Category)
admin.site.register(Image)