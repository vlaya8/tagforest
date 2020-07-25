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
from django.utils.translation import gettext as _

from notifications.signals import notify
from notifications.models import Notification

from ..exceptions import UserError, FormError, LoginRequired, UserPermissionError
from ..models import Entry,Tag,Tree
from ..models import TreeUserGroup, Role, Member, ENTRY_DISPLAY_CHOICES_STR
from ..forms import EntryForm, TreeForm, GroupForm, MemberInvitationForm, ProfileForm, TreeParamForm
from .utilities import *

import json

# Base views from which (almost) all views inherit from
# BaseView --> BaseTreeView

# Base View containing the logic and base methods used for all classes
#
# Handles UserError and FormError while processing post, and calls
# back the get function accordingly

class BaseView(View):

    template_name = 'tags/view_tree.html'
    redirect_url = 'tags:index'
    error_context = {}
    invalid_form = None

    def setup(self, request, **kwargs):

        super().setup(request, **kwargs)

        self.redirect_get_params = {}
        self.redirect_kwargs = {}

    def get_base_context(self, request, **kwargs):

        context = {
                    'current_page': 'index',
                  }

        context.update(self.error_context)

        if request.user.is_authenticated:

            logout_next = reverse('tags:index')

            new_notifications = [(n.verb, n.id) for n in request.user.notifications.unread()]
            new_notification_count = len(new_notifications)

            context.update({
                        'logged_in': request.user.is_authenticated,
                        'logout_next': {"next": logout_next},
                        'username': request.user.username,
                        'new_notifications': new_notifications,
                        'new_notification_count': new_notification_count,
                      })

        return context

    def get_context_data(self, request, **kwargs):
        return {}

    def get_return(self, request, context, **kwargs):

        return render(request, self.template_name, context)

    def get(self, request, **kwargs):

        kwargs.update(self.kwargs)

        context = self.get_base_context(request, **kwargs)

        try:
            context.update(self.get_context_data(request, **kwargs))

        except LoginRequired as login_required:
            return redirect_with_get_params(
                        'tags:login',
                        get_params={'next': reverse('tags:index')},
                    )

        except UserPermissionError as permission_error:
            context.update({'error_message': permission_error.message})
            return render(request, 'tags/permission_error.html', context)

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

        except LoginRequired as login_required:
            return redirect_with_get_params(
                        'tags:login',
                        get_params={'next': reverse('tags:index')},
                    )

        except UserPermissionError as permission_error:
            return render(request, 'tags/permission_error.html', {'error_message': permission_error.message})

        except UserError as user_error:
            self.error_context = {user_error.context_name: user_error.message}
            return self.get(request, **kwargs)

        except FormError as form_error:
            self.invalid_form = form_error.invalid_form
            return self.get(request, **kwargs)

        return self.post_return(request, **kwargs)

# Base View for all views handling trees
#
# Sets up the group and current_tree attributes
# Provides the context for the tree nav bar, and the necessary
# POST processing for that nav bar

class BaseTreeView(BaseView):

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

        context = {}

        if not self.group.is_visible_to(request.user):
            raise UserPermissionError(_("You don't have permission to view this group's trees"))

        has_writer_permission = self.group.has_write_permission_for(request.user)

        if has_writer_permission:

            tree_list = []
            tree_add_form = TreeForm(initial={'tree_id': SpecialID['NEW_ID'], 'delete_tree': False})
            tree_ids = []

            for tree in Tree.objects.filter(group__id=self.group.id):

                add_data = {'name': tree.name, 'tree_id': tree.id, 'delete_tree': False}
                delete_data = {'name' : 'unknown', 'tree_id': tree.id, 'delete_tree': True}
                delete_form = TreeForm(initial=delete_data)
                delete_form.fields['name'].widget = forms.HiddenInput()
                tree_ids.append(tree.id)

                tree_list.append((tree, TreeForm(initial=add_data), delete_form, ))

            context.update({
                        'tree_add_form': tree_add_form,
                        'tree_ids': tree_ids,
                        'nb_trees': len(tree_list),
                      })

            if self.current_tree != None:
                tree_param_form = TreeParamForm(initial={'name': self.current_tree.name,
                                                         'description': self.current_tree.description,
                                                         'default_entry_display': self.current_tree.entry_display,
                })
                context.update({'tree_param_form': tree_param_form})
        else:

            tree_list = []
            for tree in Tree.objects.filter(group__id=self.group.id):
                tree_list.append((tree, None, None))

        if self.current_tree != None:
            context.update({
                'entry_display_choices': [{'text': ENTRY_DISPLAY_CHOICES_STR[k], 'value': k} for k in ENTRY_DISPLAY_CHOICES_STR],
                'initial_entry_display': self.current_tree.entry_display
            })

        if request.user.is_authenticated:
            context.update({
                        'saved_group': request.user.profile.saved_groups.filter(pk=self.group.id).exists(),
                      })

        current_tree_id = SpecialID['NONE'] if (self.current_tree == None) else self.current_tree.id
        current_page = 'personal_tree' if (self.group.name == request.user.username) else 'groups'

        context.update({
                    'tree_list': tree_list,
                    'group': self.group,
                    'current_tree': self.current_tree,
                    'has_tree': (current_tree_id > 0),
                    'single_member': self.group.single_member,
                    'current_page': current_page,
                    'has_writer_permission': self.group.has_write_permission_for(request.user),
                  })
        return context

    def process_post(self, request, **kwargs):

        # Default redirect
        self.redirect_kwargs['group_name'] = self.group.name
        self.redirect_url = 'tags:view_tree'

        if 'tree_param_form' in request.POST:
            if not self.group.has_write_permission_for(request.user):
                raise PermissionDenied(_("You don't have permission to edit in this group"))

            form = TreeParamForm(request.POST)

            if form.is_valid():

                tree_name = form.cleaned_data['name']
                tree_description = form.cleaned_data['description']
                entry_display = form.cleaned_data['default_entry_display']

                self.current_tree.name = tree_name
                self.current_tree.description = tree_description
                self.current_tree.entry_display = entry_display

                self.current_tree.save()

            else:
                self.redirect_url = 'tags:index'

            self.redirect_url = 'tags:view_tree'
            self.redirect_kwargs['group_name'] = self.group.name
            self.redirect_kwargs['tree_id'] = self.current_tree.id

        elif 'tree_form' in request.POST:
            if not self.group.has_write_permission_for(request.user):
                raise PermissionDenied(_("You don't have permission to edit in this group"))

            form = TreeForm(request.POST)

            if form.is_valid():

                tree_name = form.cleaned_data['name']
                delete_tree = form.cleaned_data['delete_tree']

                # If the tree needs to be edited or deleted
                if form.cleaned_data['tree_id'] != SpecialID['NEW_ID']:
                    tree = get_object_or_404(Tree, pk=form.cleaned_data['tree_id'])
                    if delete_tree:
                        tree.delete()
                        self.redirect_url = 'tags:view_tree'
                    else:
                        tree.name = tree_name
                        tree.save()
                else:
                    if Tree.objects.filter(name=tree_name, group=self.group).exists():
                        raise UserError(_("Your group already contains a tree named %s(treename)s") % {'treename': tree_name}, "tree_bar_error")
                    tree = Tree.objects.create(name=tree_name, group=self.group)

                if not delete_tree:
                    self.redirect_kwargs['tree_id'] = tree.id
                    self.redirect_url = 'tags:view_tree'
            else:
                self.redirect_url = 'tags:index'

        elif 'save_group' in request.POST:

            request.user.profile.saved_groups.add(self.group)
            request.user.save()

            self.redirect_url = 'tags:view_tree'
            self.redirect_kwargs['group_name'] = self.group.name
            self.redirect_kwargs['tree_id'] = self.current_tree.id

        elif 'unsave_group' in request.POST:

            request.user.profile.saved_groups.remove(self.group)
            request.user.save()

            self.redirect_url = 'tags:view_tree'
            self.redirect_kwargs['group_name'] = self.group.name
            self.redirect_kwargs['tree_id'] = self.current_tree.id

