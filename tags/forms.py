from django import forms

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
