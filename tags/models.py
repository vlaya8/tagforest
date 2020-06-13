from django.db import models
from django.contrib.auth.models import User

from django_dag.models import *

## Groups

# The role of a member in a group dictates its permissions in the group
class Role(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)

    manage_users = models.BooleanField(default=False)
    manage_entries = models.BooleanField(default=False)

# A user which is part of a group
class Member(models.Model):
    def __str__(self):
        return self.name

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False)

# Can represent a group of users or a single user
# Can own trees
class TreeUserGroup(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)

    members = models.ManyToManyField(Member, blank=False)
    single_member = models.BooleanField()

## Trees, Entries, Tags

# A tree contains entries and tags
class Tree(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'user')

class Tag(node_factory('TagEdge')):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)

    tree = models.ForeignKey(Tree, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'user', 'tree')

class TagEdge(edge_factory(Tag, concrete = False)):
    pass

class Entry(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    added_date = models.DateTimeField('date added')
    text = models.TextField('text', blank=True)

    tags = models.ManyToManyField(Tag, blank=True)

    tree = models.ForeignKey(Tree, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'user', 'tree')

