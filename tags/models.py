from django.db import models
from django.contrib.auth.models import User

from django_dag.models import *

## Groups

# Can represent a group of users or a single user
# Can own trees
class TreeUserGroup(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255, unique=True)
    single_member = models.BooleanField()
    public_group = models.BooleanField(default=False)
    listed_group = models.BooleanField(default=False)

    def get_listed_groups():
        return TreeUserGroup.objects.filter(listed_group=True)

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
        return "({})".format(",".join([self.role.name, self.user.username]))

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False)

    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)

## Trees, Entries, Tags

# A tree contains entries and tags
class Tree(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('name', 'group')

class Tag(node_factory('TagEdge')):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)

    tree = models.ForeignKey(Tree, on_delete=models.CASCADE)
    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('name', 'group', 'tree')

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
    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('name', 'group', 'tree')

## User

class Profile(models.Model):
    def __str__(self):
        return "{}'s profile".format(self.user)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    public_user = models.BooleanField(default=False)
    listed_user = models.BooleanField(default=False)

    saved_groups = models.ManyToManyField(TreeUserGroup)

### User methods

def get_user_group(user):

    return TreeUserGroup.objects.filter(name=user.username).filter(single_member=True).first()

def get_joined_groups(user):

    groups = []
    user_members = Member.objects.filter(user=user)

    for member in user_members:
        if not member.group.single_member:
            groups.append(member.group)

    return groups

def get_saved_groups(user):

    return user.profile.saved_groups.all()

def has_group_reader_permission(user, group):
    return group.public_group or group.member_set.filter(user=user).exists()

def has_group_writer_permission(user, group):
    return group.member_set.filter(user=user).filter(role__manage_entries=True).exists()

def has_group_admin_permission(user, group):
    return group.member_set.filter(user=user).filter(role__manage_users=True).exists()

User.add_to_class('get_user_group', get_user_group)
User.add_to_class('get_joined_groups', get_joined_groups)
User.add_to_class('get_saved_groups', get_saved_groups)
User.add_to_class('has_group_reader_permission', has_group_reader_permission)
User.add_to_class('has_group_writer_permission', has_group_writer_permission)
User.add_to_class('has_group_admin_permission', has_group_admin_permission)
