from django.http import HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import views as auth_views

from ..models import Entry, Tag
from ..forms import EntryForm, TreeForm
from .utilities import *

import json

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('tags:index'))
    else:
        form = UserCreationForm()
    return render(request, 'tags/registration/signup.html', {'form': form})

class ProfileView(auth_views.PasswordChangeView):

    success_url = reverse_lazy('tags:index')

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)

        context.update(get_base_context(self.request))

        return context

    template_name = 'tags/registration/profile.html'

## Index

def index(request):

    default_tree = Tree.objects.first()

    return redirect_with_get_params('tags:view_tree', get_params={'selected_tags': request.GET.get('selected_tags', '')}, kwargs={'tree_id': default_tree.id})

@login_required
def view_tree(request, tree_id):

    if request.user.is_authenticated:
        print("User is authenticated")
        print(request.user)

    # Get selected tags from GET url parameters
    selected_tags = get_selected_tag_list(request)

    # Generate all the elements to be displayed in the tag list
    tag_list = get_tag_list(request.user, tree_id, selected_tags)

    # Generate the entries to be displayed
    if len(selected_tags) > 0:
        entry_list = Entry.objects.none()
        
        for tag in selected_tags:
            entry_list |= Entry.objects.filter(tags__name__exact=tag).filter(tree__id=tree_id).filter(user__id=request.user.id)

        entry_list = entry_list.distinct()
    else:
        entry_list = Entry.objects.filter(tree__id=tree_id).filter(user__id=request.user.id)

    context = {
                'entry_list': entry_list,
                'tag_list': tag_list,
                'current_tree_id': tree_id,
              }

    context.update(get_tree_bar_context(request.user))
    context.update(get_base_context(request))

    return render(request, 'tags/index.html', context)

@login_required
def process_tree(request):

    form = TreeForm(request.POST)

    if form.is_valid():

        tree_name = form.cleaned_data['name']
        delete_tree = form.cleaned_data['delete_tree']

        # If the tree has been edited
        if form.cleaned_data['tree_id'] != -1:
            tree = get_object_or_404(Tree, pk=form.cleaned_data['tree_id'])
            if delete_tree:
                tree.delete()
                return HttpResponseRedirect(reverse('tags:index'))
            else:
                tree.name = tree_name
                tree.save()
        else:
            tree = Tree.objects.create(name=tree_name, user=request.user)

        return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'tree_id': tree.id}))
    else:
        return HttpResponseRedirect(reverse('tags:index'))

## Entries

# Process an entry which got added or edited
@login_required
def process_entry(request, tree_id):

    if request.method == 'POST':

        form = EntryForm(request.POST)

        if form.is_valid():

            entry_name = form.cleaned_data['name']
            entry_text = form.cleaned_data['text']

            # If the entry has been edited
            if form.cleaned_data['entry_id'] != -1:
                entry = get_object_or_404(Entry, pk=form.cleaned_data['entry_id'])
                entry.name = entry_name
                entry.text = entry_text
                entry.tags.clear()
            else:
                entry = Entry.objects.create(name=entry_name, text=entry_text, tree_id=tree_id, added_date=timezone.now(), user=request.user)

            tags_name = parse_tags(form.cleaned_data['tags'])

            for tag_name in tags_name:

                tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name, tree_id=tree_id, user=request.user)
                tag_obj.save()

                entry.tags.add(tag_obj)

            entry.save()

    return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'tree_id': tree_id}))

@login_required
def detail_entry(request, tree_id, entry_id):

    entry = get_object_or_404(Entry, pk=entry_id)
    
    context = {
                'entry': entry,
                'current_tree_id': tree_id,
              }
    context.update(get_tree_bar_context(request.user))
    context.update(get_base_context(request))

    return render(request, 'tags/detail_entry.html', context)

@login_required
def add_entry(request, tree_id):

    form = EntryForm(initial={"entry_id": -1})

    context = {
                'form': form,
                'current_tree_id': tree_id,
              }
    context.update(get_tree_bar_context(request.user))
    context.update(get_base_context(request))

    return render(request, 'tags/upsert_entry.html', context)

@login_required
def edit_entry(request, tree_id, entry_id):

    entry = get_object_or_404(Entry, pk=entry_id)

    tags = ",".join([tag.name for tag in entry.tags.filter(user__id=request.user.id)])
    data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}

    form = EntryForm(initial=data)

    context = {
                'form': form,
                'current_tree_id': tree_id,
              }
    context.update(get_tree_bar_context(request.user))
    context.update(get_base_context(request))

    return render(request, 'tags/upsert_entry.html', context)

@login_required
def delete_entry(request, tree_id):

    try:
        entry_id = int(request.POST['entry_id'])
    except:
        print("Couldn't get post info")
    else:

        entry = get_object_or_404(Entry, pk=entry_id)
        entry.delete()

    return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'tree_id': tree_id}))

## Tags

@login_required
def manage_tags(request, tree_id):

    context = {
                'current_tree_id': tree_id,
              }
    context.update(get_tree_bar_context(request.user))
    context.update(get_base_context(request))

    return render(request, 'tags/manage_tags.html', context)

@login_required
def manage_tags_default(request):

    default_tree = Tree.objects.first()

    return HttpResponseRedirect(reverse('tags:manage_tags', kwargs={'tree_id': default_tree.id}))

## About

class AboutView(generic.TemplateView):
    template_name = 'tags/about.html'
    context = {}

