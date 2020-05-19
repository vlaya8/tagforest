from django.http import HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from ..models import Entry, Tag
from ..forms import EntryForm, TreeForm
from .utilities import *

import json

def detail_entry(request, tree_id, entry_id):

    entry = get_object_or_404(Entry, pk=entry_id)
    
    context = {
                'entry': entry,
                'tree_list': get_tree_list(),
                'current_tree_id': tree_id,
              }

    return render(request, 'tags/detail_entry.html', context)

class AboutView(generic.TemplateView):
    template_name = 'tags/about.html'
    context = {'tree_list': get_tree_list(),}

def index(request):

    default_tree = Tree.objects.first()

    return redirect_with_get_params('tags:view_tree', get_params={'selected_tags': request.GET.get('selected_tags', '')}, kwargs={'tree_id': default_tree.id})

def view_tree(request, tree_id):

    # Get selected tags from GET url parameters
    selected_tags = get_selected_tag_list(request)

    # Generate all the elements to be displayed in the tag list
    tag_list = get_tag_list(tree_id, selected_tags)

    # Generate the entries to be displayed
    if len(selected_tags) > 0:
        entry_list = Entry.objects.none()
        
        for tag in selected_tags:
            entry_list |= Entry.objects.filter(tags__name__exact=tag)

        entry_list = entry_list.distinct()
    else:
        entry_list = Entry.objects.all()

    tree_list = get_tree_list()

    tree_form = TreeForm()

    context = {
                'entry_list': entry_list,
                'tag_list': tag_list,
                'tree_list': tree_list,
                'current_tree_id': tree_id,
                'tree_form': tree_form,
              }

    return render(request, 'tags/index.html', context)

def process_tree(request):

    form = TreeForm(request.POST)

    if form.is_valid():
        tree_name = form.cleaned_data['name']
        new_tree = Tree.objects.create(name=tree_name)

    return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'tree_id': new_tree.id}))

# Process an entry which got added or edited
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
                entry = Entry(name=entry_name, text=entry_text, added_date=timezone.now())
                entry.save()

            tags_name = parse_tags(form.cleaned_data['tags'])

            for tag_name in tags_name:

                tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name)
                tag_obj.save()

                entry.tags.add(tag_obj)

            entry.save()

    return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'tree_id': tree_id}))


def add_entry(request, tree_id):

    form = EntryForm(initial={"entry_id": -1})

    context = {
                'form': form,
                'tree_list': get_tree_list(),
                'current_tree_id': tree_id,
              }

    return render(request, 'tags/upsert_entry.html', context)

def edit_entry(request, tree_id, entry_id):

    entry = get_object_or_404(Entry, pk=entry_id)

    tags = ",".join([tag.name for tag in entry.tags.all()])
    data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}

    form = EntryForm(initial=data)

    context = {
                'form': form,
                'tree_list': get_tree_list(),
                'current_tree_id': tree_id,
              }

    return render(request, 'tags/upsert_entry.html', context)

def delete_entry(request, tree_id):

    try:
        entry_id = int(request.POST['entry_id'])
    except:
        print("Couldn't get post info")
    else:

        entry = get_object_or_404(Entry, pk=entry_id)
        entry.delete()

    return HttpResponseRedirect(reverse('tags:view_tree', kwargs={tree_id: tree_id}))

def manage_tags(request, tree_id):

    context = {
                'tree_list': get_tree_list(),
                'current_tree_id': tree_id,
              }

    return render(request, 'tags/manage_tags.html', context)

