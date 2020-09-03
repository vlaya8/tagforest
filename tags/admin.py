from django.contrib import admin
from tags.models import Tree, Entry, Tag
from tags.models import TreeUserGroup, Member, Role
from tags.models import Profile
from tags.models import Task, TaskGroup

# Trees

admin.site.register(Tree)
admin.site.register(Entry)
admin.site.register(Tag)

# Groups

admin.site.register(TreeUserGroup)
admin.site.register(Member)
admin.site.register(Role)

admin.site.register(Profile)

# Tasks

admin.site.register(TaskGroup)
admin.site.register(Task)
