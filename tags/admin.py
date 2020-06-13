from django.contrib import admin
from tags.models import Tree, Entry, Tag
from tags.models import TreeUserGroup, Member, Role

# Trees

admin.site.register(Tree)
admin.site.register(Entry)
admin.site.register(Tag)

# Groups

admin.site.register(TreeUserGroup)
admin.site.register(Member)
admin.site.register(Role)
