from django.http import HttpResponseRedirect, Http404
from django.views import generic,View
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.template import RequestContext
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from notifications.signals import notify
from notifications.models import Notification

from ..exceptions import UserError, FormError
from ..models import Entry,Tag,Tree
from ..models import TreeUserGroup, Role, Member
from ..forms import EntryForm, TreeForm, GroupForm, MemberInvitationForm, ProfileForm
from .utilities import *

import json

# Base views from which (almost) all views inherit from
# BaseView --> BaseUserView --> BaseTreeView

# Base View containing the logic and base methods used for all classes
#
# Handles UserError and FormError while processing post, and calls
# back the get function accordingly

@method_decorator(login_required, name='dispatch')
class BaseView(View):

    template_name = 'tags/view_tree.html'
    redirect_url = 'tags:index'
    error_message = None
    invalid_form = None

    def setup(self, request, **kwargs):

        self.redirect_get_params = {}
        self.redirect_kwargs = {}

        super().setup(request, **kwargs)

    def get_context_data(self, request, **kwargs):

        context = {
                    'error_message': self.error_message,
                    'current_page': 'index',
                  }

        return context

    def get_return(self, request, context, **kwargs):

        return render(request, self.template_name, context)

    def get(self, request, **kwargs):

        kwargs.update(self.kwargs)

        context = self.get_context_data(request, **kwargs)

        if self.invalid_form != None:
            context.update(self.invalid_form)

        return self.get_return(request, context, **kwargs)

    def process_post(self, request, **kwargs):
        pass

    def post_return(self, request, **kwargs):

        return redirect_with_get_params(
                    self.redirect_url,
                    get_params=self.redirect_get_params,
                    kwargs=self.redirect_kwargs,
                )

    def post(self, request, **kwargs):

        kwargs.update(self.kwargs)

        try:
            self.process_post(request, **kwargs)
        except UserError as user_error:
            self.error_message = user_error.message
            return self.get(request, **kwargs)
        except FormError as form_error:
            self.invalid_form = form_error.invalid_form
            return self.get(request, **kwargs)

        return self.post_return(request, **kwargs)

# Base View for all views handling data from the logged in user
# 
# Provides user context and setups the user and link_user attribute

@method_decorator(login_required, name='dispatch')
class BaseUserView(BaseView):

    template_name = 'tags/view_tree.html'
    redirect_url = 'tags:index'

    def setup(self, request, username=None, **kwargs):

        super().setup(request, **kwargs)

        self.user = request.user
        if username == None:
            self.link_user = None
        else:
            self.link_user = get_object_or_404(User, username=username)

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        logged_in = self.user.is_authenticated
        logout_next = reverse('tags:index')

        new_notifications = [(n.verb, n.id) for n in self.user.notifications.unread()]
        new_notification_count = len(new_notifications)

        context.update({
                    'logged_in': logged_in,
                    'logout_next': {"next": logout_next},
                    'username': self.user.username,
                    'link_user': self.link_user,
                    'new_notifications': new_notifications,
                    'new_notification_count': new_notification_count,
                  })

        return context

# Base View for all views handling trees
#
# Sets up the group and current_tree attributes
# Provides the context for the tree nav bar, and the necessary
# POST processing for that nav bar

class BaseTreeView(BaseUserView):

    # Setup group and current_tree arguments
    def setup(self, request, group_name, tree_id=SpecialID['DEFAULT_ID'], **kwargs):

        super().setup(request, **kwargs)

        # Setup group argument
        self.group = get_object_or_404(TreeUserGroup, name=group_name)

        # Setup tree argument
        if tree_id == SpecialID['DEFAULT_ID']:
            self.current_tree = Tree.objects.filter(group__id=self.group.id).first()

        elif tree_id == SpecialID['NONE']:
            self.current_tree = None

        else:
            self.current_tree = get_object_or_404(Tree, pk=tree_id)

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        if not self.user.has_group_reader_permission(self.group):
            context.update({'has_reader_permission': False})
            return context

        tree_list = []
        tree_add_form = TreeForm(initial={'tree_id': SpecialID['NEW_ID'], 'delete_tree': False})
        tree_ids = []

        for tree in Tree.objects.filter(group__id=self.group.id):
            add_data = {'name': tree.name, 'tree_id': tree.id, 'delete_tree': False}
            delete_data = {'name' : 'unknown', 'tree_id': tree.id, 'delete_tree': True}
            delete_form = TreeForm(initial=delete_data)
            delete_form.fields['name'].widget = forms.HiddenInput()
            tree_list.append((tree.name, tree.id, TreeForm(initial=add_data), delete_form, (tree == self.current_tree)))
            tree_ids.append(tree.id)

        if self.current_tree == None:
            current_tree_id = SpecialID['NONE']
        else:
            current_tree_id = self.current_tree.id

        context.update({
                    'has_reader_permission': True,
                    'tree_list': tree_list,
                    'tree_add_form': tree_add_form,
                    'tree_bar_data': json.dumps({'nb_trees': len(tree_list), 'tree_ids': tree_ids}),
                    'group': self.group,
                    'current_tree_id': current_tree_id,
                    'has_tree': (current_tree_id > 0),
                    'saved_group': self.user.profile.saved_groups.filter(pk=self.group.id).exists(),
                    'single_member': self.group.single_member,
                  })
        return context

    def process_post(self, request, **kwargs):

        # Default redirect
        self.redirect_kwargs['group_name'] = self.group.name
        self.redirect_url = 'tags:view_tree'

        if not self.user.has_group_reader_permission(self.group):
            raise UserError("")

        if 'tree_form' in request.POST:
            if not self.user.has_group_writer_permission(self.group):
                raise PermissionDenied("You don't have permission to edit in this group")

            form = TreeForm(request.POST)

            if form.is_valid():

                tree_name = form.cleaned_data['name']
                delete_tree = form.cleaned_data['delete_tree']

                # If the tree needs to be edited or deleted
                if form.cleaned_data['tree_id'] != SpecialID['NEW_ID']:
                    tree = get_object_or_404(Tree, pk=form.cleaned_data['tree_id'])
                    if delete_tree:
                        tree.delete()
                        self.redirect_url = 'tags:index'
                        self.redirect_kwargs = {}
                    else:
                        tree.name = tree_name
                        tree.save()
                else:
                    tree = Tree.objects.create(name=tree_name, group=self.group)

                if not delete_tree:
                    self.redirect_kwargs['tree_id'] = tree.id
                    self.redirect_url = 'tags:view_tree'
            else:
                self.redirect_url = 'tags:index'

        elif 'save_group' in request.POST:

            self.user.profile.saved_groups.add(self.group)
            self.user.save()

        elif 'unsave_group' in request.POST:

            self.user.profile.saved_groups.remove(self.group)
            self.user.save()

