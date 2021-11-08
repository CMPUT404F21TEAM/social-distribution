from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(LocalAuthor)
admin.site.register(LocalPost)
admin.site.register(Comment)
admin.site.register(Category)
