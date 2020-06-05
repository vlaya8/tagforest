from django.http import HttpResponseRedirect
from django.views import generic,View
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy

from django.utils import timezone
from django.utils.decorators import method_decorator

from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from ..models import Entry,Tag,Tree
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

## Index

@login_required
def index(request):

    default_tree = Tree.objects.first()

    return redirect_with_get_params(
                'tags:view_tree',
                get_params={'selected_tags': request.GET.get('selected_tags', '')},
                kwargs={'tree_id': default_tree.id, 'username': request.user.username}
            )

@method_decorator(login_required, name='dispatch')
class UserDataView(View):

    template_name = 'tags/index.html'
    redirect_url = 'tags:index'

    def setup(self, request, username, **kwargs):

        self.redirect_get_params = {}
        self.redirect_kwargs = {}

        super().setup(request, username=username, **kwargs)
        self.kwargs['user'] = get_object_or_404(User, username=username)

    def get_context_data(self, request, user, **kwargs):

        logged_in = user.is_authenticated
        logout_next = reverse('tags:index')

        context = {
                    'logged_in': logged_in,
                    'logout_next': {"next": logout_next},
                    'username': user.username,
                  }

        return context

    def process_post(self, request, user, **kwargs):
        pass

    def get(self, request, **kwargs):

        kwargs.update(self.kwargs)
        del kwargs['username']

        context = self.get_context_data(request, **kwargs)

        return render(request, self.template_name, context)

    def post(self, request, **kwargs):

        kwargs.update(self.kwargs)
        del kwargs['username']

        self.process_post(request, **kwargs)

        return redirect_with_get_params(
                    self.redirect_url,
                    get_params=self.redirect_get_params,
                    kwargs=self.redirect_kwargs,
                )

class ProfileView(UserDataView):

    template_name = 'tags/registration/profile.html'

class ChangePasswordView(auth_views.PasswordChangeView):

    success_url = reverse_lazy('tags:index')
    template_name = 'tags/registration/password_change.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        return context

class TreeView(UserDataView):

    def setup(self, request, username, tree_id, **kwargs):

        super().setup(request, username=username, **kwargs)
        self.kwargs['current_tree'] = get_object_or_404(Tree, pk=tree_id)

    def get_context_data(self, request, user, current_tree, **kwargs):

        context = super().get_context_data(request, user=user, **kwargs)

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

        context.update({
                    'tree_list': tree_list,
                    'tree_add_form': tree_add_form,
                    'tree_bar_data': json.dumps({'nb_trees': len(tree_list), 'tree_ids': tree_ids}),
                    'current_tree_id': current_tree.id,
                  })
        return context

    def process_post(self, request, user, current_tree, **kwargs):

        # Default redirect
        self.redirect_kwargs['username'] = user.username
        self.redirect_kwargs['tree_id'] = current_tree.id
        self.redirect_url = 'tags:view_tree'

        if 'tree_form' in request.POST:
            form = TreeForm(request.POST)

            if form.is_valid():

                tree_name = form.cleaned_data['name']
                delete_tree = form.cleaned_data['delete_tree']

                # If the tree needs to be edited or deleted
                if form.cleaned_data['tree_id'] != -1:
                    tree = get_object_or_404(Tree, pk=form.cleaned_data['tree_id'])
                    if delete_tree:
                        tree.delete()
                        self.redirect_url = 'tags:index'
                        self.redirect_kwargs = {}
                    else:
                        tree.name = tree_name
                        tree.save()
                else:
                    tree = Tree.objects.create(name=tree_name, user=user)

                if not delete_tree:
                    self.redirect_kwargs['tree_id'] = tree.id
                    self.redirect_url = 'tags:view_tree'
            else:
                self.redirect_url = 'tags:index'

class ViewTreeView(TreeView):

    template_name = 'tags/index.html'

    def get_context_data(self, request, user, current_tree, **kwargs):

        context = super().get_context_data(request, user=user, current_tree=current_tree, **kwargs)

        # Get selected tags from GET url parameters
        selected_tags = get_selected_tag_list(request)
        # Generate all the elements to be displayed in the tag list
        tag_list = get_tag_list(user, current_tree.id, selected_tags)

        # Generate the entries to be displayed
        if len(selected_tags) > 0:
            entry_list = Entry.objects.none()
            
            for tag in selected_tags:
                entry_list |= Entry.objects.filter(tags__name__exact=tag).filter(tree__id=current_tree.id).filter(user__id=user.id)

            entry_list = entry_list.distinct()
        else:
            entry_list = Entry.objects.filter(tree__id=current_tree.id).filter(user__id=user.id)

        context.update({
                    'entry_list': entry_list,
                    'tag_list': tag_list,
                    'current_tree_id': current_tree.id,
                  })

        return context

    def process_post(self, request, user, current_tree, **kwargs):

        super().process_post(request, user=user, current_tree=current_tree, **kwargs)

        # Process an entry which got deleted
        if 'delete_entry_id' in request.POST:
            entry_id = int(request.POST['delete_entry_id'])

            entry = get_object_or_404(Entry, pk=entry_id)
            entry.delete()

class ViewEntryView(TreeView):

    template_name = 'tags/detail_entry.html'

    def get_context_data(self, request, user, current_tree, entry_id, **kwargs):
        context = super().get_context_data(request, user=user, current_tree=current_tree, **kwargs)

        entry = get_object_or_404(Entry, pk=entry_id)
        context.update({
                    'entry': entry,
                  })

        return context

    def process_post(self, request, user, current_tree, **kwargs):

        super().process_post(request, user=user, current_tree=current_tree, **kwargs)

        # Process an entry which got added or edited
        if 'upsert_entry' in request.POST:

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
                    entry = Entry.objects.create(name=entry_name, text=entry_text, tree=current_tree, added_date=timezone.now(), user=user)

                tags_name = parse_tags(form.cleaned_data['tags'])

                for tag_name in tags_name:

                    tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name, tree=current_tree, user=user)
                    tag_obj.save()

                    entry.tags.add(tag_obj)

                entry.save()

                self.redirect_url = 'tags:view_entry'
                self.redirect_kwargs['entry_id'] = entry.id

class UpsertEntryView(TreeView):

    template_name = 'tags/upsert_entry.html'

    def get_context_data(self, request, user, current_tree, **kwargs):
        context = super().get_context_data(request, user=user, current_tree=current_tree, **kwargs)

        if 'entry_id' in kwargs:
            entry_id = kwargs['entry_id']
            entry = get_object_or_404(Entry, pk=entry_id)

            tags = ",".join([tag.name for tag in entry.tags.filter(user__id=user.id)])
            data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}
        else:
            data = {"entry_id": -1}

        form = EntryForm(initial=data)

        context.update({
                    'form': form,
                  })

        return context

## Tags

class ManageTagsView(TreeView):

    template_name = 'tags/manage_tags.html'

## About

class AboutView(generic.TemplateView):
    template_name = 'tags/about.html'
    context = {}

