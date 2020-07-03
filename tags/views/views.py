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

from ..exceptions import UserError
from ..models import Entry,Tag,Tree
from ..models import TreeUserGroup, Role, Member
from ..forms import EntryForm, TreeForm, GroupForm, MemberInvitationForm
from .utilities import *

import json

from enum import Enum

SpecialID = {
                'DEFAULT_ID': -1,
                'NONE': -2,
                'NEW_ID': -3,
            }

def handler404(request, exception):

    return render(request,'tags/404.html')

def handler500(request):

    return render(request,'tags/500.html')


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

    group = request.user.get_user_group()

    return redirect_with_get_params(
                'tags:view_tree',
                get_params={'selected_tags': request.GET.get('selected_tags', '')},
                kwargs={'group_name': group.name}
            )

@method_decorator(login_required, name='dispatch')
class BaseView(View):

    template_name = 'tags/view_tree.html'
    redirect_url = 'tags:index'
    error_message = None

    def setup(self, request, **kwargs):

        self.redirect_get_params = {}
        self.redirect_kwargs = {}

        super().setup(request, **kwargs)

    def get_context_data(self, request, **kwargs):

        context = {
                    'error_message': self.error_message,
                  }

        return context

    def get_return(self, request, context, **kwargs):

        return render(request, self.template_name, context)

    def get(self, request, **kwargs):

        kwargs.update(self.kwargs)

        context = self.get_context_data(request, **kwargs)

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

        return self.post_return(request, **kwargs)

@method_decorator(login_required, name='dispatch')
class UserDataView(BaseView):

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

class ViewNotificationsView(UserDataView):

    template_name = 'tags/view_notifications.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        unread_notifications = [(n.verb, n.id, n.target) for n in self.user.notifications.unread()]
        unread_notification_count = len(unread_notifications)
        read_notifications = [(n.verb, n.id, n.target) for n in self.user.notifications.read()]
        read_notification_count = len(read_notifications)

        context.update({
                         'unread_notifications': unread_notifications,
                         'unread_notification_count': unread_notification_count,
                         'read_notifications': read_notifications,
                         'read_notification_count': read_notification_count,
                       })
        return context

class ViewNotificationView(UserDataView):

    template_name = 'tags/view_notification.html'

    def get_context_data(self, request, notification_id, **kwargs):

        context = super().get_context_data(request, **kwargs)

        notification = get_object_or_404(Notification, pk=notification_id)

        context.update({
                         'notification': notification,
                      })
        return context

    # Process an invitation which has been accepted or declined
    def process_post(self, request, notification_id, **kwargs):

        super().process_post(request, **kwargs)

        if 'accept_notification' in request.POST or 'decline_notification' in request.POST:

            notification = get_object_or_404(Notification, pk=notification_id)

            notification.mark_as_read()

            if 'accept_notification' in request.POST:
                Member.objects.create(user=self.user, role=notification.action_object, group=notification.target)

                self.redirect_url = 'tags:view_tree'
                self.redirect_kwargs['group_name'] = notification.target.name
            else:
                self.redirect_url = 'tags:view_notifications'
                self.redirect_kwargs['username'] = self.user.username

class ProfileView(UserDataView):

    template_name = 'tags/registration/profile.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        has_edit_permission = (self.user.username == self.link_user.username)

        context.update({
                         'has_edit_permission': has_edit_permission,
                      })
        return context

class ChangePasswordView(auth_views.PasswordChangeView):

    success_url = reverse_lazy('tags:index')
    template_name = 'tags/registration/password_change.html'

class ManageGroupsView(UserDataView):

    template_name = 'tags/manage_groups.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        joined_group_list = self.user.get_joined_groups()
        saved_group_list = self.user.get_saved_groups()
        listed_group_list = TreeUserGroup.get_listed_groups()

        joined_groups = [(group, self.user.has_group_admin_permission(group)) for group in joined_group_list]
        saved_groups = [(group, self.user.has_group_admin_permission(group)) for group in saved_group_list]
        listed_groups = [(group, self.user.has_group_admin_permission(group)) for group in listed_group_list]

        context.update({
                         'joined_groups': joined_groups,
                         'saved_groups': saved_groups,
                         'listed_groups': listed_groups,
                      })

        return context
    
    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process a group which got deleted
        if 'delete_group_id' in request.POST:
            group_id = int(request.POST['delete_group_id'])

            group = get_object_or_404(TreeUserGroup, pk=group_id)
            if not self.user.has_group_writer_permission(group):
                raise PermissionDenied("You don't have permission to delete this group")
            group.delete()

        self.redirect_url = 'tags:manage_groups'
        self.redirect_kwargs['username'] = self.user.username

class UpsertGroupView(UserDataView):

    template_name = 'tags/upsert_group.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        # If user wants to edit a group
        if 'group_id' in kwargs:
            group_id = kwargs['group_id']
            group = get_object_or_404(TreeUserGroup, pk=group_id)

            if not self.user.has_group_writer_permission(group):
                raise PermissionDenied("You don't have permission to edit this group")

            data = {"name": group.name, "group_id": group_id, "public_group": group.public_group, "listed_group": group.listed_group}
        # If user wants to add a group
        else:
            data = {"group_id": SpecialID['NEW_ID']}

        form = GroupForm(initial=data)

        context.update({
                         'form': form,
                     })

        return context

class ViewGroupView(UserDataView):

    template_name = 'tags/view_group.html'

    def get_context_data(self, request, group_id, invite_form=None, **kwargs):

        context = super().get_context_data(request, **kwargs)

        group = get_object_or_404(TreeUserGroup, pk=group_id)

        if not self.user.has_group_reader_permission(group):
            raise PermissionDenied("You don't have permission to view that group")

        members = group.member_set.all()

        if invite_form == None:
            invite_form = MemberInvitationForm(group, initial={})

        context.update({
                         'group': group,
                         'has_writer_permission': self.user.has_group_writer_permission(group),
                         'has_admin_permission': self.user.has_group_admin_permission(group),
                         'members': members,
                         'invite_form': invite_form,
                      })

        return context

    def process_post(self, request, group_id=SpecialID['NEW_ID'], **kwargs):

        # Process a group which got added or edited
        if 'upsert_group' in request.POST:

            form = GroupForm(request.POST)

            if form.is_valid():

                group_name = form.cleaned_data['name']
                group_id = form.cleaned_data['group_id']
                public_group = form.cleaned_data['public_group']
                listed_group = form.cleaned_data['listed_group']

                # If the group has been edited
                if group_id != SpecialID['NEW_ID']:
                    group = get_object_or_404(TreeUserGroup, pk=group_id)

                    if not self.user.has_group_writer_permission(group):
                        raise PermissionDenied("You don't have permission to edit this group")

                    group.name = group_name
                    group.public_group = public_group
                    group.listed_group = listed_group
                else:
                    group = TreeUserGroup.objects.create(name=group_name, single_member=False, public_group=public_group, listed_group=listed_group)
                    admin_role = Role.objects.filter(name="admin").first()
                    member = Member.objects.create(user=self.user, role=admin_role, group=group)

                group.save()

                self.redirect_url = 'tags:view_group'
                self.redirect_kwargs['group_id'] = group.id
                self.redirect_kwargs['username'] = self.user.username

        # If a member has been deleted
        if 'delete_member_id' in request.POST:

            group = get_object_or_404(TreeUserGroup, pk=group_id)

            if not self.user.has_group_admin_permission(group):
                raise PermissionDenied("You don't have permission to delete this member")

            if group.member_set.count() == 1:
                raise UserError("The last member of the group can't be deleted (delete the group instead)")

            member = get_object_or_404(Member, pk=request.POST['delete_member_id'])

            member.delete()

            self.redirect_url = 'tags:view_group'
            self.redirect_kwargs['group_id'] = group.id
            self.redirect_kwargs['username'] = self.user.username


    def post_return(self, request, group_id=SpecialID['NEW_ID'], **kwargs):

        # Process a member invitation
        if 'invite_member' in request.POST:

            group = get_object_or_404(TreeUserGroup, pk=group_id)
            form = MemberInvitationForm(group, request.POST)

            if form.is_valid():

                member_name = form.cleaned_data['name']
                role = form.cleaned_data['role']
                group = get_object_or_404(TreeUserGroup, pk=group_id)

                target_user = get_object_or_404(User, username=member_name)

                notify.send(self.user, recipient=target_user,
                                  verb="{} invited you to join {}".format(self.user, group),
                                  action_object=role,
                                  target=group)
            else:
                context = self.get_context_data(request, group_id, invite_form=form, **kwargs)
                return self.get_return(request, context, **kwargs)

        return super().post_return(request, **kwargs)

class TreeView(UserDataView):

    # Setup group and current_tree arguments
    def setup(self, request, group_name, tree_id=SpecialID['DEFAULT_ID'], **kwargs):

        super().setup(request, **kwargs)

        # Setup group argument
        self.group = get_object_or_404(TreeUserGroup, name=group_name)

        if not self.user.has_group_reader_permission(self.group):
            raise PermissionDenied("You don't have permission to view this group")

        # Setup tree argument
        if tree_id == SpecialID['DEFAULT_ID']:
            self.current_tree = Tree.objects.filter(group__id=self.group.id).first()

        elif tree_id == SpecialID['NONE']:
            self.current_tree = None

        else:
            self.current_tree = get_object_or_404(Tree, pk=tree_id)

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        tree_list = []
        tree_add_form = TreeForm(initial={'tree_id': SpecialID['NEW_ID'], 'delete_tree': False})
        tree_ids = []

        for tree in Tree.objects.filter(group__id=self.group.id):
            add_data = {'name': tree.name, 'tree_id': tree.id, 'delete_tree': False}
            delete_data = {'name' : 'unknown', 'tree_id': tree.id, 'delete_tree': True}
            delete_form = TreeForm(initial=delete_data)
            delete_form.fields['name'].widget = forms.HiddenInput()
            tree_list.append((tree.name, tree.id, TreeForm(initial=add_data), delete_form))
            tree_ids.append(tree.id)

        if self.current_tree == None:
            current_tree_id = SpecialID['NONE']
        else:
            current_tree_id = self.current_tree.id

        context.update({
                    'tree_list': tree_list,
                    'tree_add_form': tree_add_form,
                    'tree_bar_data': json.dumps({'nb_trees': len(tree_list), 'tree_ids': tree_ids}),
                    'group_name': self.group.name,
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

class ViewTreeView(TreeView):

    template_name = 'tags/view_tree.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        if self.current_tree != None:

            # Get selected tags from GET url parameters
            selected_tags = get_selected_tag_list(request)
            # Generate all the elements to be displayed in the tag list
            tag_list = get_tag_list(self.group, self.current_tree.id, selected_tags)

            # Generate the entries to be displayed
            if len(selected_tags) > 0:
                entry_list = Entry.objects.all()
                
                for tag in selected_tags:
                    entry_list &= Entry.objects.filter(tags__name__exact=tag).filter(tree__id=self.current_tree.id).filter(group__id=self.group.id)

                entry_list = entry_list.distinct()
            else:
                entry_list = Entry.objects.filter(tree__id=self.current_tree.id).filter(group__id=self.group.id)
        else:

            entry_list = []
            tag_list = []

        context.update({
                    'entry_list': entry_list,
                    'tag_list': tag_list,
                    'has_writer_permission': self.user.has_group_writer_permission(self.group),
                  })

        return context

    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process an entry which got deleted
        if 'delete_entry_id' in request.POST:
            entry_id = int(request.POST['delete_entry_id'])

            entry = get_object_or_404(Entry, pk=entry_id)
            entry.delete()

class ViewEntryView(TreeView):

    template_name = 'tags/view_entry.html'

    def get_context_data(self, request, entry_id, **kwargs):
        context = super().get_context_data(request, **kwargs)

        entry = get_object_or_404(Entry, pk=entry_id)
        context.update({
                    'entry': entry,
                    'has_writer_permission': self.user.has_group_writer_permission(self.group),
                  })

        return context

    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process an entry which got added or edited
        if 'upsert_entry' in request.POST:

            form = EntryForm(request.POST)

            if form.is_valid():

                entry_name = form.cleaned_data['name']
                entry_text = form.cleaned_data['text']
                entry_id = form.cleaned_data['entry_id']

                # If the entry has been edited
                if entry_id != SpecialID['NEW_ID']:
                    entry = get_object_or_404(Entry, pk=entry_id)
                    entry.name = entry_name
                    entry.text = entry_text
                    entry.tags.clear()
                else:
                    entry = Entry.objects.create(name=entry_name, text=entry_text, tree=self.current_tree, added_date=timezone.now(), group=self.group)

                tags_name = parse_tags(form.cleaned_data['tags'])

                for tag_name in tags_name:

                    tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name, tree=self.current_tree, group=self.group)
                    tag_obj.save()

                    entry.tags.add(tag_obj)

                entry.save()

                self.redirect_url = 'tags:view_entry'
                self.redirect_kwargs['group_name'] = self.group.name
                self.redirect_kwargs['tree_id'] = self.current_tree.id
                self.redirect_kwargs['entry_id'] = entry.id

class UpsertEntryView(TreeView):

    template_name = 'tags/upsert_entry.html'

    def get_context_data(self, request, **kwargs):
        context = super().get_context_data(request, **kwargs)

        # If user wants to edit an entry
        if 'entry_id' in kwargs:
            entry_id = kwargs['entry_id']
            entry = get_object_or_404(Entry, pk=entry_id)

            tags = ",".join([tag.name for tag in entry.tags.filter(group__id=self.group.id)])
            data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}
        # If user wants to add a group
        else:
            data = {"entry_id": SpecialID['NEW_ID']}

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

