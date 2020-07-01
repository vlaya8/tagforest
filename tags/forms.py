from django import forms
from .models import Role
from django.contrib.auth.models import User

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

    name = forms.CharField(label = "Name", max_length=255)
    text = forms.CharField(label = "Text", widget=forms.Textarea)
    tags = forms.CharField(label = "Tags", max_length=255)

    entry_id = forms.IntegerField(widget=forms.HiddenInput())

class TreeForm(forms.Form):

    name = forms.CharField(label = "Name", max_length=255)

    delete_tree = forms.BooleanField(required=False, widget=forms.HiddenInput())
    tree_id = forms.IntegerField(widget=forms.HiddenInput())

class GroupForm(forms.Form):

    name = forms.CharField(label = "Name", max_length=255)
    public_group = forms.BooleanField(required=False)
    listed_group = forms.BooleanField(required=False)

    group_id = forms.IntegerField(widget=forms.HiddenInput())

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
