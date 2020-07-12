from django.http import HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django import forms
from django.contrib.auth.models import User

from ..models import Entry, Tag, Tree
from ..forms import EntryForm, TreeForm
from .utilities import *
from urllib.parse import urlencode

SpecialID = {
                'DEFAULT_ID': -1,
                'NONE': -2,
                'NEW_ID': -3,
            }

def redirect_with_get_params(url_name, get_params={}, kwargs={}):

    url = reverse(url_name, kwargs=kwargs)
    params = urlencode(get_params)

    return HttpResponseRedirect(url + "?%s" % params)

# Get selected tags from GET url parameters
def get_selected_tag_list(request):
    selected_tags = []
    if request.method == 'GET':
        selected_tags = request.GET.get( 'selected_tags', '' ).split(",")
        # Filter out empty tags
        selected_tags = list(filter(lambda s:s, selected_tags))

    return selected_tags

# Generate all the elements to be displayed in the tag list
def get_tag_list(group, tree_id, selected_tags):
    tag_list = []

    for tag in Tag.objects.filter(tree__id=tree_id).filter(group__id=group.id):

        tag_name = tag.name
        tag_count = tag.entry_set.count()
        tag_selected_tags = toggle_tag(selected_tags, tag_name)

        if tag_count > 0:
            tag_list.append((tag_count, tag_name, tag_selected_tags))

    tag_list.sort()
    tag_list.reverse()

    return tag_list

# Should be moved client side
def toggle_tag(selected_tags, tag):
    tag_list = [tag for tag in selected_tags]

    if tag in selected_tags:
        tag_list.remove(tag)
    else:
        tag_list.append(tag)

    tag_list.sort()
    return ",".join(tag_list)

# Parse the tags added in an entry
def parse_tags(tags_string):

    tags_list = []

    tags_string = tags_string.strip() # Remove useless spaces
    tags_string = tags_string.split(",") # Split by commas

    tags_list = filter(lambda s: len(s) > 0, tags_string)

    return tags_list

