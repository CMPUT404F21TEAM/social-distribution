from django.contrib import admin

from .models import Node

class NodeAdmin(admin.ModelAdmin):
    list_filter = ['host', 'remote_credentials']
    search_fields = ['host']

# Register your models here.
admin.site.register(Node, NodeAdmin)