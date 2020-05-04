from django.http import HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .models import Entry, Tag
from .forms import EntryForm

# Should be moved client side
def toggle_tag(selected_tags, tag):
    tag_list = [tag for tag in selected_tags]

    if tag in selected_tags:
        tag_list.remove(tag)
    else:
        tag_list.append(tag)

    tag_list.sort()
    return ",".join(tag_list)

def index(request):

    tags_list = []

    # Get selected tags from GET url parameters
    selected_tags = []
    if request.method == 'GET':
        selected_tags = request.GET.get( 'selected_tags', '' ).split(",")
        # Filter out empty tags
        selected_tags = list(filter(lambda s:s, selected_tags))

    # Generate all the elements to be displayed in the tag list
    for tag in Tag.objects.all():

        tag_name = tag.name
        tag_count = tag.entry_set.count()
        tag_selected_tags = toggle_tag(selected_tags, tag_name)

        if tag_count > 0:
            tags_list.append((tag_count, tag_name, tag_selected_tags))

    tags_list.sort()
    tags_list.reverse()

    # Generate the entries to be displayed
    if len(selected_tags) > 0:
        entry_list = Entry.objects.none()
        
        for tag in selected_tags:
            entry_list |= Entry.objects.filter(tags__name__exact=tag)

        entry_list = entry_list.distinct()
    else:
        entry_list = Entry.objects.all()

    context = {
                'entry_list': entry_list,
                'tags_list': tags_list,
              }

    return render(request, 'tags/index.html', context)

class DetailEntryView(generic.DetailView):

  model = Entry
  template_name = 'tags/detail_entry.html'

# Parse the tags added in an entry
def parse_tags(tags_string):

    tags_list = []

    tags_string = tags_string.strip() # Remove useless spaces
    tags_string = tags_string.split(",") # Split by commas

    tags_list = filter(lambda s: len(s) > 0, tags_string)

    return tags_list

# Process an entry which got added or edited
def process_entry(request):

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

            return HttpResponseRedirect(reverse('tags:index'))


def add_entry(request):

    form = EntryForm(initial={"entry_id": -1})

    return render(request, 'tags/upsert_entry.html', {'form': form})

def edit_entry(request, entry_id):

    entry = get_object_or_404(Entry, pk=entry_id)

    tags = ",".join([tag.name for tag in entry.tags.all()])
    data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}

    form = EntryForm(initial=data)

    return render(request, 'tags/upsert_entry.html', {'form': form})

def delete_entry(request):

    try:
        entry_id = int(request.POST['entry_id'])
    except:
        print("Couldn't get post info")
    else:

        entry = get_object_or_404(Entry, pk=entry_id)
        entry.delete()

    return HttpResponseRedirect(reverse('tags:index'))

