from django.db import models
from django.contrib.auth.models import User
from django_dag.models import *
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from tagforest import settings
from .exceptions import EntryParseError

import re

INVITE = 'INV'
USERS = 'USR'
ALL = 'ALL'

PUBLIC_CHOICES_STR = { 
                        INVITE: _('Only invited users'),
                        USERS:  _('Only users'),
                        ALL:    _('Everyone'),
                     }

# String that can be integrated in a sentence
PUBLIC_CHOICES_STR_SENTENCE = { 
                        INVITE: _('invited users'),
                        USERS:  _('users'),
                        ALL:    _('everyone'),
                     }

PUBLIC_CHOICES_ORDER = { 
                        INVITE: 0,
                        USERS:  1,
                        ALL:    2,
                     }

PUBLIC_CHOICES = [(choice, PUBLIC_CHOICES_STR[choice]) for choice in PUBLIC_CHOICES_STR]

ENTRY_DISPLAY_COMPACT_SMALL = 'CPS'
ENTRY_DISPLAY_COMPACT_MEDIUM = 'CPM'
ENTRY_DISPLAY_COMPACT_LARGE = 'CPL'
ENTRY_DISPLAY_LIST = 'LST'

ENTRY_DISPLAY_CHOICES_STR = {
                        ENTRY_DISPLAY_COMPACT_SMALL: _("Compact (small)"),
                        ENTRY_DISPLAY_COMPACT_MEDIUM: _("Compact (medium)"),
                        ENTRY_DISPLAY_COMPACT_LARGE: _("Compact (large)"),
                        ENTRY_DISPLAY_LIST: _("List"),
}

ENTRY_DISPLAY_CHOICES = [(choice, ENTRY_DISPLAY_CHOICES_STR[choice]) for choice in ENTRY_DISPLAY_CHOICES_STR]

## Groups

# Can represent a group of users or a single user
# Can own trees
class TreeUserGroup(models.Model):

    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255, unique=True)

    single_member = models.BooleanField()

    listed_to_public = models.CharField(
            max_length=3,
            choices=PUBLIC_CHOICES,
            default=INVITE,
    )
    visible_to_public = models.CharField(
            max_length=3,
            choices=PUBLIC_CHOICES,
            default=INVITE,
    )

    def get_listed_to_all():
        return TreeUserGroup.objects.filter(listed_to_public=ALL)
    def get_listed_to_users():
        return TreeUserGroup.objects.filter(listed_to_public=USERS)

    def is_visible_to(self, user):
        if self.visible_to_public == ALL:
            return True
        if not user.is_authenticated:
            return False
        if self.visible_to_public == USERS:
            return True
        if user.member_set.filter(group=self).exists():
            return True
        return False

    def has_write_permission_for(self, user):
        if not user.is_authenticated:
            return False
        return user.member_set.filter(group=self).filter(role__manage_entries=True).exists()
    def has_admin_permission_for(self, user):
        if not user.is_authenticated:
            return False
        return user.member_set.filter(group=self).filter(role__manage_users=True).exists()

    def listed_to_str(self):
        return PUBLIC_CHOICES_STR[self.listed_to_public]
    def visible_to_str(self):
        return PUBLIC_CHOICES_STR[self.visible_to_public]

    def listed_to_str_sentence(self):
        return PUBLIC_CHOICES_STR_SENTENCE[self.listed_to_public]
    def visible_to_str_sentence(self):
        return PUBLIC_CHOICES_STR_SENTENCE[self.visible_to_public]

    def listed_order(self):
        return PUBLIC_CHOICES_ORDER[self.listed_to_public]
    def visible_order(self):
        return PUBLIC_CHOICES_ORDER[self.visible_to_public]

# The role of a member in a group dictates its permissions in the group
class Role(models.Model):

    # Clunky way of implementing translation for roles
    def __str__(self):
        if self.name == "admin":
            return ugettext("Admin")
        elif self.name == "writer":
            return ugettext("Writer")
        elif self.name == "reader":
            return ugettext("Reader")
        else:
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

    class Meta:
        unique_together = ('user', 'group')

## Trees, Entries, Tags

# A tree contains entries and tags
class Tree(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)
    description = models.TextField('description', default="", blank=True)

    entry_display = models.CharField(
            max_length=3,
            choices=ENTRY_DISPLAY_CHOICES,
            default=ENTRY_DISPLAY_COMPACT_LARGE,
    )

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
    text = models.TextField('text', null=True)

    tags = models.ManyToManyField(Tag, blank=True)

    tree = models.ForeignKey(Tree, on_delete=models.CASCADE)
    group = models.ForeignKey(TreeUserGroup, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = ('name', 'group', 'tree')

    def export_field(field_name, field_data):
        if field_data:
            return "{}> {}\n".format(field_name, field_data)
        else:
            return ""

    def export_multiline_field(field_name, field_data):
        if field_data:
            return "{}>>>>\n{}\n<<<<\n".format(field_name, field_data.replace('\n<<<<\r\n', '\n\<<<<\n'))
        else:
            return ""

    def export(self):

        data =  Entry.export_field("name", self.name)
        data += Entry.export_field("tags", ",".join([tag.name for tag in self.tags.all()]))
        data += Entry.export_multiline_field("text", self.text)

        return data

    def field_pattern(field_name, required=False):
        pattern = fr"{field_name}>[ \t](?P<{field_name}>.*?)[\r]*?\n"
        return pattern if required else (r"(" + pattern + r")?")

    def field_multiline_pattern(field_name, required=False):
        pattern = fr"{field_name}>>>>[\r]*?\n(?P<{field_name}>[\s\S]+?)[\r]*?\n<<<<[\r]*?\n"
        return pattern if required else (r"(" + pattern + r")?")

    def parse_data(data):

        entries = []
        matched_chars = 0
        data += "\r\n"

        while matched_chars < len(data):
            pattern = re.compile(Entry.field_pattern("name", False) + Entry.field_pattern("tags") + Entry.field_multiline_pattern("text"),
                                 re.VERBOSE)
            match = pattern.match(data[matched_chars:])
            matched_string, entry_dict = match.group(), match.groupdict()
            if not matched_string:
                raise EntryParseError(data.count("\n", 0, matched_chars) + 1)
            matched_chars += len(matched_string)
            entry_dict["text"] = (entry_dict.get("text") or "").replace('\n\<<<<\r\n', '\n<<<<\n')
            entries.append(entry_dict)

        return entries


## User

class Profile(models.Model):
    def __str__(self):
        return "{}'s profile".format(self.user)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    language = models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)

    public_user = models.BooleanField(default=False)
    listed_user = models.BooleanField(default=False)

    saved_groups = models.ManyToManyField(TreeUserGroup, blank=True)

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

User.add_to_class('get_user_group', get_user_group)
User.add_to_class('get_joined_groups', get_joined_groups)
User.add_to_class('get_saved_groups', get_saved_groups)
