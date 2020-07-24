from django import forms
from .models import Role, TreeUserGroup
from .models import PUBLIC_CHOICES, PUBLIC_CHOICES_ORDER, PUBLIC_CHOICES_STR_SENTENCE
from .models import ENTRY_DISPLAY_CHOICES
from django.contrib.auth.models import User

from django.utils.translation import gettext as _

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

    name = forms.CharField(label = "Name", max_length=255)

    delete_tree = forms.BooleanField(required=False, widget=forms.HiddenInput())
    tree_id = forms.IntegerField(widget=forms.HiddenInput())

class ProfileForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    username = forms.CharField(label = "Username", max_length=255)

    language = forms.ChoiceField(label = "Default langue", choices=settings.LANGUAGES)

    listed_to_public = forms.ChoiceField(
                                      label = "Public to which your personal group is listed",
                                      choices = PUBLIC_CHOICES,
    )
    visible_to_public = forms.ChoiceField(
                                      label = "Public to which your personal group is accessible",
                                      choices = PUBLIC_CHOICES,
    )

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        if username != self.user.username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("{} is already taken".format(username))

        listed_to_public = cleaned_data.get("listed_to_public")
        visible_to_public = cleaned_data.get("visible_to_public")

        if PUBLIC_CHOICES_ORDER[listed_to_public] > PUBLIC_CHOICES_ORDER[visible_to_public]:
            raise forms.ValidationError("You asked to list the group to {} but it is only visible to {}".format(
                                        PUBLIC_CHOICES_STR_SENTENCE[listed_to_public],
                                        PUBLIC_CHOICES_STR_SENTENCE[visible_to_public]))

        return cleaned_data

class GroupForm(forms.Form):

    name = forms.CharField(label = "Name", max_length=255)

    listed_to_public = forms.ChoiceField(
                                      label = "Public to which the group is listed",
                                      choices = PUBLIC_CHOICES,
    )
    visible_to_public = forms.ChoiceField(
                                      label = "Public to which the group is accessible",
                                      choices = PUBLIC_CHOICES,
    )

    group_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()

        listed_to_public = cleaned_data.get("listed_to_public")
        visible_to_public = cleaned_data.get("visible_to_public")

        if PUBLIC_CHOICES_ORDER[listed_to_public] > PUBLIC_CHOICES_ORDER[visible_to_public]:
            raise forms.ValidationError("You asked to list the group to {} but it is only visible to {}".format(
                                        PUBLIC_CHOICES_STR_SENTENCE[listed_to_public],
                                        PUBLIC_CHOICES_STR_SENTENCE[visible_to_public]))
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
            raise forms.ValidationError("There is no user named {}".format(name))
        if self.group.member_set.filter(user__username=name).exists():
            raise forms.ValidationError("{} is already in {}".format(name, self.group))

        return cleaned_data

class TreeParamForm(forms.Form):

    name = forms.CharField(label = "Name", max_length=255)
    description = forms.CharField(label = "Description", widget=forms.Textarea, required=False)

    default_entry_display = forms.ChoiceField(
                                      label = "Default entry display",
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
            raise forms.ValidationError("Error when selecting entries")

        return entries_ids

