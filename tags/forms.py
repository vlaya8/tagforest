from django import forms
from .models import Role, TreeUserGroup
from .models import PUBLIC_CHOICES, PUBLIC_CHOICES_ORDER, PUBLIC_CHOICES_STR_SENTENCE
from .models import ENTRY_DISPLAY_CHOICES
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from .exceptions import EntryParseError
from .models import Entry

from tagforest import settings

def parse_tag(tags_string):

  tags_list = []

  tags_string = tags_string.strip() # Remove useless spaces
  tags_string = tags_string.split(",") # Split by commas

  tags_list = filter(lambda s: len(s) > 0, tags_string)

  return tags_list


class TagField(forms.CharField):
    def to_python(value):

      if isinstance(value, list):
        return value

      if value is None:
        return value

      return parse_tag(value)

class EntryForm(forms.Form):

    # Translators: Label for the entry form
    name_label = _("Name")
    # Translators: Label for the entry form
    text_label = _("Text (markdown formatted)")
    # Translators: Label for the entry form
    tags_label = _("Tags (separated by commas: tag1,tag2,tag3...)")

    name = forms.CharField(label = name_label, max_length=255)
    text = forms.CharField(label = text_label, widget=forms.Textarea, required=False)
    tags = forms.CharField(label = tags_label, max_length=255, required=False)

    entry_id = forms.IntegerField(widget=forms.HiddenInput())

class TreeForm(forms.Form):

    name = forms.CharField(label = _("Name"), max_length=255)

    delete_tree = forms.BooleanField(required=False, widget=forms.HiddenInput())
    tree_id = forms.IntegerField(widget=forms.HiddenInput())

class ProfileForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    username = forms.CharField(label = _("Username"), max_length=255)

    language = forms.ChoiceField(label = _("Default language"), choices=settings.LANGUAGES)

    listed_to_public = forms.ChoiceField(
                                      label = _("Public to which your personal group is listed"),
                                      choices = PUBLIC_CHOICES,
    )
    visible_to_public = forms.ChoiceField(
                                      label = _("Public to which your personal group is accessible"),
                                      choices = PUBLIC_CHOICES,
    )

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        if username != self.user.username and User.objects.filter(username=username).exists():
            raise forms.ValidationError(ugettext("%(username)s is already taken") % {'username': username})

        listed_to_public = cleaned_data.get("listed_to_public")
        visible_to_public = cleaned_data.get("visible_to_public")

        if PUBLIC_CHOICES_ORDER[listed_to_public] > PUBLIC_CHOICES_ORDER[visible_to_public]:
            raise forms.ValidationError(ugettext("You asked to list the group to %(listed_public)s but it is only visible to %(visible_public)s")
                                        % {'listed_public':  PUBLIC_CHOICES_STR_SENTENCE[listed_to_public],
                                           'visible_public': PUBLIC_CHOICES_STR_SENTENCE[visible_to_public]})

        return cleaned_data

class GroupForm(forms.Form):

    name = forms.CharField(label = _("Name"), max_length=255)

    listed_to_public = forms.ChoiceField(
                                      label = _("Public to which the group is listed"),
                                      choices = PUBLIC_CHOICES,
    )
    visible_to_public = forms.ChoiceField(
                                      label = _("Public to which the group is accessible"),
                                      choices = PUBLIC_CHOICES,
    )

    group_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()

        listed_to_public = cleaned_data.get("listed_to_public")
        visible_to_public = cleaned_data.get("visible_to_public")

        if PUBLIC_CHOICES_ORDER[listed_to_public] > PUBLIC_CHOICES_ORDER[visible_to_public]:
            raise forms.ValidationError(ugettext("You asked to list the group to %(listed_public)s but it is only visible to %(visible_public)s")
                                        % {'listed_public':  PUBLIC_CHOICES_STR_SENTENCE[listed_to_public],
                                           'visible_public': PUBLIC_CHOICES_STR_SENTENCE[visible_to_public]})
        return cleaned_data


class MemberInvitationForm(forms.Form):

    name = forms.CharField(label = "Name", max_length=255)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), empty_label=None)

    def __init__(self, group, *args, **kwargs):
        super(MemberInvitationForm, self).__init__(*args, **kwargs)
        self.group = group

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if not User.objects.filter(username=name).exists():
            raise forms.ValidationError(ugettext("There is no user named %(username)s") % {'username': name})
        if self.group.member_set.filter(user__username=name).exists():
            raise forms.ValidationError(ugettext("%(username)s is already in %(group)s") % {'username': name, 'group': self.group})

        return cleaned_data

class TreeParamForm(forms.Form):

    name = forms.CharField(label = _("Name"), max_length=255)
    description = forms.CharField(label = _("Description"), widget=forms.Textarea, required=False)

    default_entry_display = forms.ChoiceField(
                                      label = _("Default entry display"),
                                      choices = ENTRY_DISPLAY_CHOICES,
    )

class ManipulateEntriesForm(forms.Form):

    entries = forms.CharField(widget=forms.HiddenInput())

    def clean_entries(self):
        cleaned_data = super().clean()
        entries = cleaned_data.get("entries")

        try:
            entries_ids = list(map(lambda x: int(x), entries.split(";")))
        except ValueError:
            raise forms.ValidationError(ugettext("Error when selecting entries"))

        return entries_ids

class ImportForm(forms.Form):

    data_label = _("Data to import")
    data = forms.CharField(label = data_label, widget=forms.Textarea, required=True)

    def clean_data(self):
        cleaned_data = super().clean()
        data = cleaned_data.get("data")

        try:
            entries = Entry.parse_data(data)
        except EntryParseError as e:
            raise forms.ValidationError(ugettext("Parsing failed starting from line %(linenumber)s") % {'linenumber': e.line_number})

        return entries
