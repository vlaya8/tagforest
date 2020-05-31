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

import json

def redirect_with_get_params(url_name, get_params, kwargs):
    url = reverse(url_name, kwargs=kwargs)
    params = urlencode(get_params)
    return HttpResponseRedirect(url + "?%s" % params)

def get_user(request, username):
    if username == "":
        return request.user
    else:
        return User.objects.get(username=username)

def get_base_context(request):

    logged_in = request.user.is_authenticated
    logout_next = reverse('tags:index')

    context = {
                'logged_in': logged_in,
                'logout_next': {"next": logout_next},
                'username': request.user.username,
              }

    return context

def get_tree_bar_context(user):

    tree_list = []
    tree_add_form = TreeForm(initial={'tree_id': -1, 'delete_tree': False})
    tree_ids = []

    for tree in Tree.objects.filter(user__id=user.id):
        add_data = {'name': tree.name, 'tree_id': tree.id, 'delete_tree': False}
        delete_data = {'name' : 'unknown', 'tree_id': tree.id, 'delete_tree': True}
        delete_form = TreeForm(initial=delete_data)
        delete_form.fields['name'].widget = forms.HiddenInput()
        tree_list.append((tree.name, tree.id, TreeForm(initial=add_data), delete_form))
        tree_ids.append(tree.id)

    context = {
                'tree_list': tree_list,
                'tree_add_form': tree_add_form,
                'tree_bar_data': json.dumps({'nb_trees': len(tree_list), 'tree_ids': tree_ids}),
              }

    return context


# Get selected tags from GET url parameters
def get_selected_tag_list(request):
    selected_tags = []
    if request.method == 'GET':
        selected_tags = request.GET.get( 'selected_tags', '' ).split(",")
        # Filter out empty tags
        selected_tags = list(filter(lambda s:s, selected_tags))

    return selected_tags

# Generate all the elements to be displayed in the tag list
def get_tag_list(user, tree_id, selected_tags):
    tag_list = []

    for tag in Tag.objects.filter(tree__id=tree_id).filter(user__id=user.id):

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

