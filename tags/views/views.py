from django.http import HttpResponseRedirect, Http404, JsonResponse
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
from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext as _


from notifications.signals import notify
from notifications.models import Notification

from ..exceptions import UserError, FormError, LoginRequired, UserPermissionError, EntryParseError
from ..models import Entry,Tag,Tree
from ..models import TreeUserGroup, Role, Member
from ..forms import EntryForm, TreeForm, GroupForm, MemberInvitationForm, ProfileForm, ManipulateEntriesForm, ImportForm
from .utilities import *
from .base_views import *

import json


def handler404(request, exception):

    return render(request,'tags/404.html')

def handler500(request):

    return render(request,'tags/500.html')

class SignupView(BaseView):

    template_name = 'tags/registration/signup.html'

    def get_context_data(self, request, **kwargs):

        return {
                 'form': UserCreationForm(),
                 'current_page': login,
        }

    def process_post(self, request, **kwargs):

        form = UserCreationForm(request.POST)

        if form.is_valid():

            form.save()
            self.redirect_url = 'tags:signup_success'
        else:
            raise FormError({'form': form})

class SignupSuccessView(BaseView):

    template_name = 'tags/registration/signup_success.html'

    def get_context_data(self, request, **kwargs):

        return {'current_page': 'login'}

## Index

def index(request):

    if request.user.is_authenticated:
        group = request.user.get_user_group()

        return HttpResponseRedirect(reverse('tags:view_tree', kwargs={'group_name': group.name}))
    else:
        return HttpResponseRedirect(reverse('tags:view_groups'))

@login_required
def post_login(request):

    user_language = request.user.profile.language
    translation.activate(user_language)
    response = HttpResponseRedirect(reverse('tags:index'))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)

    return response

@method_decorator(login_required, name='dispatch')
class ViewNotificationsView(BaseView):

    template_name = 'tags/view_notifications.html'

    def get_context_data(self, request, **kwargs):

        unread_notifications = [(get_notification_message(n), n.id, n.target) for n in request.user.notifications.unread()]
        unread_notification_count = len(unread_notifications)
        read_notifications = [(get_notification_message(n), n.id, n.target) for n in request.user.notifications.read()]
        read_notification_count = len(read_notifications)

        context = {
                         'unread_notifications': unread_notifications,
                         'unread_notification_count': unread_notification_count,
                         'read_notifications': read_notifications,
                         'read_notification_count': read_notification_count,
                       }
        return context

@method_decorator(login_required, name='dispatch')
class ViewNotificationView(BaseView):

    template_name = 'tags/view_notification.html'

    def get_context_data(self, request, notification_id, **kwargs):

        notification = get_object_or_404(Notification, pk=notification_id)

        if notification.target == None:
            notification.mark_as_read()
            return { 
                         'deleted_group': True,
                         'message': _("The group you were invited to got deleted"),
            }

        message = get_notification_message(notification)

        context = {
                         'deleted_group': False,
                         'notification': notification,
                         'message': message,
        }
        return context

    # Process an invitation which has been accepted or declined
    def process_post(self, request, notification_id, **kwargs):

        super().process_post(request, **kwargs)

        if 'accept_notification' in request.POST or 'decline_notification' in request.POST:

            notification = get_object_or_404(Notification, pk=notification_id)

            notification.mark_as_read()

            if 'accept_notification' in request.POST:
                Member.objects.create(user=request.user, role=notification.action_object, group=notification.target)

                self.redirect_url = 'tags:view_tree'
                self.redirect_kwargs['group_name'] = notification.target.name
            else:
                self.redirect_url = 'tags:view_notifications'

class ProfileView(BaseView):

    template_name = 'tags/registration/profile.html'

    def setup(self, request, username, **kwargs):

        super().setup(request, **kwargs)

        self.link_user = get_object_or_404(User, username=username)

    def get_context_data(self, request, form=None, **kwargs):

        context = {}

        has_edit_permission = request.user.is_authenticated and (request.user.username == self.link_user.username)

        if has_edit_permission:

            group = request.user.get_user_group()
            if form == None:
                form = ProfileForm(request.user, initial={
                                             'username': request.user.username,
                                             'language': request.user.profile.language,
                                             'listed_to_public': group.listed_to_public,
                                             'visible_to_public': group.visible_to_public,
                                           })
            context.update({'form': form})

            current_page = 'profile'
        else:

            current_page = 'other_profile'

        link_group = self.link_user.get_user_group()

        context.update({
                         'has_edit_permission': has_edit_permission,
                         'group_listed_to': link_group.listed_to_str_sentence(),
                         'group_visible_to': link_group.visible_to_str_sentence(),
                         'has_group_view_permission': link_group.is_visible_to(request.user),
                         'current_page': current_page,
                         'link_user': self.link_user,
                       })

        return context

    @method_decorator(login_required)
    def process_post(self, request, **kwargs):

        if 'edit_profile' in request.POST:

            form = ProfileForm(request.user, request.POST)

            if form.is_valid():

                if request.user.username != self.link_user.username:
                    raise PermissionDenied(_("You don't have permission to edit this profile"))


                username = form.cleaned_data['username']
                language = form.cleaned_data['language']
                listed_to_public = form.cleaned_data['listed_to_public']
                visible_to_public = form.cleaned_data['visible_to_public']

                group = request.user.get_user_group()

                group.listed_to_public = listed_to_public
                group.visible_to_public = visible_to_public
                group.name = username
                group.save()

                request.user.username = username
                request.user.save()

                request.user.profile.language = language
                request.user.profile.save()

                self.redirect_url = 'tags:profile'
                self.redirect_kwargs['username'] = request.user.username
            else:
                raise FormError({'form': form})

    @method_decorator(login_required)
    def post_return(self, request, **kwargs):


        user_language = request.user.profile.language
        translation.activate(user_language)
        response = redirect_with_get_params(
                    self.redirect_url,
                    get_params=self.redirect_get_params,
                    kwargs=self.redirect_kwargs,
                )
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)

        return response

class ChangePasswordView(auth_views.PasswordChangeView):

    success_url = reverse_lazy('tags:index')
    template_name = 'tags/registration/password_change.html'
    context = {'current_page': 'profile'}

class ViewGroupsView(BaseView):

    template_name = 'tags/view_groups.html'

    def get_context_data(self, request, **kwargs):

        listed_group_list = TreeUserGroup.get_listed_to_all()
        context = {}

        if request.user.is_authenticated:

            listed_group_list = listed_group_list.union(TreeUserGroup.get_listed_to_users())

            joined_group_list = request.user.get_joined_groups()
            saved_group_list = request.user.get_saved_groups()

            joined_groups = [(group, group.single_member, group.has_admin_permission_for(request.user)) for group in joined_group_list]
            saved_groups = [(group, group.single_member, group.has_admin_permission_for(request.user)) for group in saved_group_list]

            context.update({
                             'joined_groups': joined_groups,
                             'saved_groups': saved_groups,
                          })

        listed_groups = [(group, group.single_member, group.has_admin_permission_for(request.user)) for group in listed_group_list]

        context.update({
                         'listed_groups': listed_groups,
                         'current_page': 'groups',
                      })

        return context
    
    @method_decorator(login_required)
    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process a group which got deleted
        if 'delete_group_id' in request.POST:
            group_id = int(request.POST['delete_group_id'])

            group = get_object_or_404(TreeUserGroup, pk=group_id)

            if not group.has_write_permission_for(request.user):
                raise PermissionDenied(_("You don't have permission to delete this group"))

            if group.single_member:
                raise PermissionDenied(_("You can't delete this group"))

            group.delete()

        self.redirect_url = 'tags:view_groups'

@method_decorator(login_required, name='dispatch')
class UpsertGroupView(BaseView):

    template_name = 'tags/upsert_group.html'

    def get_context_data(self, request, **kwargs):

        # If user wants to edit a group
        if 'group_id' in kwargs:
            group_id = kwargs['group_id']
            group = get_object_or_404(TreeUserGroup, pk=group_id)

            if not group.has_write_permission_for(request.user):
                raise PermissionDenied(_("You don't have permission to edit this group"))

            data = {
                     "name": group.name,
                     "listed_to_public": group.listed_to_public,
                     "visible_to_public": group.visible_to_public,
                     "group_id": group_id
                   }
        # If user wants to add a group
        else:
            data = {"group_id": SpecialID['NEW_ID']}

        form = GroupForm(initial=data)

        context = {
                         'form': form,
                         'current_page': 'groups',
                     }

        return context

    def process_post(self, request, **kwargs):

        # Process a group which got added or edited
        if 'upsert_group' in request.POST:

            form = GroupForm(request.POST)

            if form.is_valid():

                group_name = form.cleaned_data['name']
                listed_to_public = form.cleaned_data['listed_to_public']
                visible_to_public = form.cleaned_data['visible_to_public']
                group_id = form.cleaned_data['group_id']

                # If the group has been edited
                if group_id != SpecialID['NEW_ID']:
                    group = get_object_or_404(TreeUserGroup, pk=group_id)

                    if not group.has_write_permission_for(request.user):
                        raise PermissionDenied(_("You don't have permission to edit this group"))

                    group.name = group_name
                    group.listed_to_public = listed_to_public
                    group.visible_to_public = visible_to_public
                else:
                    group = TreeUserGroup.objects.create(name=group_name, single_member=False,
                                                         listed_to_public=listed_to_public,
                                                         visible_to_public=visible_to_public)
                    admin_role = Role.objects.filter(name="admin").first()
                    member = Member.objects.create(user=request.user, role=admin_role, group=group)

                group.save()

                self.redirect_url = 'tags:view_group'
                self.redirect_kwargs['group_id'] = group.id
            else:
                raise FormError({'form': form})

class ViewGroupView(BaseView):

    template_name = 'tags/view_group.html'

    def get_context_data(self, request, group_id, invite_form=None, **kwargs):

        group = get_object_or_404(TreeUserGroup, pk=group_id)

        if not group.is_visible_to(request.user):
            raise UserPermissionError(_("You don't have permission to view this group"))

        members = group.member_set.all()

        if invite_form == None:
            invite_form = MemberInvitationForm(group, initial={})

        context = {
                         'group': group,
                         'has_writer_permission': group.has_write_permission_for(request.user),
                         'has_admin_permission': group.has_admin_permission_for(request.user),
                         'members': members,
                         'invite_form': invite_form,
                         'group_listed_to': group.listed_to_str_sentence(),
                         'group_visible_to': group.visible_to_str_sentence(),
                         'current_page': 'groups',
                      }

        return context

    @method_decorator(login_required)
    def process_post(self, request, group_id, **kwargs):

        group = get_object_or_404(TreeUserGroup, pk=group_id)

        if not group.has_admin_permission_for(request.user):
            raise PermissionDenied(_("You don't have admin permission for this group"))

        # If a member has been deleted
        if 'delete_member_id' in request.POST:

            if group.member_set.count() == 1:
                raise UserError(_("The last member of the group can't be deleted (delete the group instead)"), "group_error")

            member = get_object_or_404(Member, pk=request.POST['delete_member_id'])

            member.delete()

            self.redirect_url = 'tags:view_group'
            self.redirect_kwargs['group_id'] = group.id

        # Process a member invitation
        if 'invite_member' in request.POST:

            form = MemberInvitationForm(group, request.POST)

            if form.is_valid():

                member_name = form.cleaned_data['name']
                role = form.cleaned_data['role']
                group = get_object_or_404(TreeUserGroup, pk=group_id)

                target_user = get_object_or_404(User, username=member_name)

                notify.send(request.user, recipient=target_user,
                                  verb="",
                                  action_object=role,
                                  target=group)
            else:
                raise FormError({'invite_form': form})

def apiTreeEntries(request):


    tree_name = request.GET.get( 'tree', '' )
    tree = get_object_or_404(Tree, name=tree_name)
    group_name = request.GET.get( 'group', '' )
    group = get_object_or_404(Tree, name=group_name)

    if not group.is_visible_to(request.user):
        return JsonResponse({'error': "You don't have permission to view this group's trees"})

    if tree != None:

        # Get selected tags from GET url parameters
        selected_tags_dirty = get_selected_tag_list(request)
        selected_tags = []

        # Check if all the tags exist
        for tag in selected_tags_dirty:
            if not Tag.objects.filter(name__exact=tag).exists():
                self.error_context.update({"tag_error": _("The tag %(tagname)s does not exist") % {'tagname': tag}})
            else:
                selected_tags.append(tag)

        selected_tags_distinct = list(set(selected_tags))

        self.redirect_to_distinct_tags = len(selected_tags_distinct) != len(selected_tags)
        if self.redirect_to_distinct_tags:
            return {'selected_tags': selected_tags_distinct}
        selected_tags = selected_tags_distinct

        # Generate all the elements to be displayed in the tag list
        tag_list, entry_list = get_tag_entry_list(self.group, self.current_tree, selected_tags)

    else:

        tag_list, entry_list = [], []
        selected_tags = []

    entry_titles = {entry.pk: entry.name for entry in entry_list}

    context.update({
                'entry_list': entry_list,
                'entry_titles': json.dumps(entry_titles),
                'tag_list': tag_list,
                'selected_tags': ",".join(selected_tags),
                'selected_entries_form': ManipulateEntriesForm(initial={"entries": ""}),
                'quick_add_form': EntryForm(initial={"entry_id": SpecialID['NEW_ID']}),
              })

    return JsonResponse(data)


class ViewTreeView(BaseTreeView):

    template_name = 'tags/view_tree.html'

    def get_return(self, request, context, **kwargs):

        if self.redirect_to_distinct_tags:
            return redirect_with_get_params(
                        'tags:view_tree',
                        get_params={"selected_tags": ",".join(context['selected_tags'])},
                        kwargs={"group_name": self.group.name, "tree_id": self.current_tree.id},
                    )

        return super().get_return(request, context, **kwargs)

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        if self.current_tree != None:

            # Get selected tags from GET url parameters
            selected_tags_dirty = get_selected_tag_list(request)
            selected_tags = []

            # Check if all the tags exist
            for tag in selected_tags_dirty:
                if not Tag.objects.filter(name__exact=tag).exists():
                    self.error_context.update({"tag_error": _("The tag %(tagname)s does not exist") % {'tagname': tag}})
                else:
                    selected_tags.append(tag)

            selected_tags_distinct = list(set(selected_tags))

            self.redirect_to_distinct_tags = len(selected_tags_distinct) != len(selected_tags)
            if self.redirect_to_distinct_tags:
                return {'selected_tags': selected_tags_distinct}
            selected_tags = selected_tags_distinct

            # Generate all the elements to be displayed in the tag list
            tag_list, entry_list = get_tag_entry_list(self.group, self.current_tree, selected_tags)

        else:

            tag_list, entry_list = [], []
            selected_tags = []

        entry_titles = {entry.pk: entry.name for entry in entry_list}

        context.update({
                    'entry_list': entry_list,
                    'entry_titles': json.dumps(entry_titles),
                    'tag_list': tag_list,
                    'selected_tags': ",".join(selected_tags),
                    'selected_entries_form': ManipulateEntriesForm(initial={"entries": ""}),
                    'quick_add_form': EntryForm(initial={"entry_id": SpecialID['NEW_ID']}),
                  })

        return context

    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process an entry which got deleted
        if 'delete_entries' in request.POST:

            form = ManipulateEntriesForm(request.POST)

            if form.is_valid():

                entries_ids = form.cleaned_data['entries']

                for pk in entries_ids:
                    entry = get_object_or_404(Entry, pk=pk)
                    entry.delete()

                self.redirect_url = 'tags:view_tree'
                self.redirect_kwargs['group_name'] = self.group.name
                self.redirect_kwargs['tree_id'] = self.current_tree.id

            else:
                raise FormError({'selected_entries_form': form})

        # Process an entry got added
        if 'add_entry' in request.POST:

            form = EntryForm(request.POST)

            if form.is_valid():

                entry_name = form.cleaned_data['name']
                entry_id = form.cleaned_data['entry_id']

                # Check if an entry with the same name in the same tree already exists
                if Entry.objects.filter(tree=self.current_tree).filter(name=entry_name).exists():
                    raise UserError(_("You already have an entry named %(entryname)s") % {'entryname': entry_name}, "entry_upsert_error")

                entry = Entry.objects.create(name=entry_name, tree=self.current_tree, added_date=timezone.now(), group=self.group)

                tags_name = parse_tags(form.cleaned_data['tags'])

                for tag_name in tags_name:

                    tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name, tree=self.current_tree, group=self.group)
                    tag_obj.save()

                    entry.tags.add(tag_obj)

                entry.save()

                self.redirect_url = 'tags:view_tree'
                self.redirect_kwargs['group_name'] = self.group.name
                self.redirect_kwargs['tree_id'] = self.current_tree.id

            else:
                raise FormError({'quick_add_form': form})


class ViewEntryView(BaseTreeView):

    template_name = 'tags/view_entry.html'

    def get_context_data(self, request, entry_id, **kwargs):

        context = super().get_context_data(request, **kwargs)

        if not self.group.is_visible_to(request.user):
            return context

        entry = get_object_or_404(Entry, pk=entry_id)
        context.update({
                    'entry': entry,
                    'has_writer_permission': self.group.has_write_permission_for(request.user),
                  })

        return context

class UpsertEntryView(BaseTreeView):

    template_name = 'tags/upsert_entry.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        if not self.group.has_write_permission_for(request.user):
            return context

        # If user wants to edit an entry
        if 'entry_id' in kwargs:
            entry_id = kwargs['entry_id']
            entry = get_object_or_404(Entry, pk=entry_id)

            tags = ",".join([tag.name for tag in entry.tags.filter(group__id=self.group.id)])
            data = {"name": entry.name, "text": entry.text, "tags": tags, "entry_id": entry_id}

            context.update({'entry': entry})

        # If user wants to add an entry
        else:
            data = {"entry_id": SpecialID['NEW_ID']}

        form = EntryForm(initial=data)

        context.update({
                         'form': form,
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

                    # Check if an entry with the same name in the same tree already exists
                    if entry.name != entry_name:
                        if Entry.objects.filter(tree=self.current_tree).filter(name=entry_name).exists():
                            raise UserError(_("You already have an entry named %(entryname)s") % {'entryname': entry_name}, "entry_upsert_error")

                    entry.name = entry_name
                    entry.text = entry_text
                    entry.tags.clear()
                else:

                    # Check if an entry with the same name in the same tree already exists
                    if Entry.objects.filter(tree=self.current_tree).filter(name=entry_name).exists():
                        raise UserError(_("You already have an entry named %(entryname)s") % {'entryname': entry_name}, "entry_upsert_error")

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

            else:
                raise FormError({'form': form})

class ImportEntriesView(BaseTreeView):

    template_name = 'tags/import_entries.html'

    def get_context_data(self, request, **kwargs):

        context = super().get_context_data(request, **kwargs)

        form = ImportForm(initial={})

        context.update({
                         'form': form
        })

        return context

    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        # Process an entry which got deleted
        if 'import_entries' in request.POST:

            form = ImportForm(request.POST)

            if form.is_valid():

                entries = form.cleaned_data['data']

                for entry_dict in entries:

                    # Check if an entry with the same name in the same tree already exists
                    if Entry.objects.filter(tree=self.current_tree).filter(name=entry_dict["name"]).exists():
                        raise UserError(_("You already have an entry named %(entryname)s") % {'entryname': entry_dict["name"]}, "entry_upsert_error")

                for entry_dict in entries:

                    entry = Entry.objects.create(name=entry_dict["name"], text=entry_dict.get("text","aaa"), tree=self.current_tree, added_date=timezone.now(), group=self.group)

                    tags_name = parse_tags(entry_dict.get("tags") or "")

                    for tag_name in tags_name:

                        tag_obj, tag_exists = Tag.objects.get_or_create(name=tag_name, tree=self.current_tree, group=self.group)
                        tag_obj.save()

                        entry.tags.add(tag_obj)

                    entry.save()

                self.redirect_url = 'tags:view_tree'
                self.redirect_kwargs['group_name'] = self.group.name
                self.redirect_kwargs['tree_id'] = self.current_tree.id

            else:
                raise FormError({'form': form})

class ExportEntriesView(BaseTreeView):

    template_name = 'tags/export_entries.html'

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

        export_str = ""

        for entry in entry_list:
            export_str += entry.export()

        context.update({
                         'export_str': export_str
        })

        return context

## About

class AboutView(BaseView):
    template_name = 'tags/about.html'

    def get_context_data(self, request, **kwargs):

        context = {'current_page': 'about'}
        return context

