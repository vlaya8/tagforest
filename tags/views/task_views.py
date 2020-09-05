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
from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext as _

from ..exceptions import UserError, FormError, LoginRequired, UserPermissionError, EntryParseError
from ..models import Entry,Tag,Tree
from ..models import Task, TaskGroup
from ..forms import EntryForm, TreeForm, GroupForm, MemberInvitationForm, ProfileForm, ManipulateEntriesForm, ImportForm, TaskGroupForm, TaskForm
from .utilities import *
from .base_views import *

from ..models import TASK_COMPLETED, TASK_INPROGRESS, TASK_TOSTART

@method_decorator(login_required, name='dispatch')
class ViewTaskGroupsView(BaseView):
    template_name = 'tags/tasks/view_task_groups.html'

    def get_context_data(self, request, **kwargs):

        groups = [(group, *group.get_stats(), TaskGroupForm(initial={'name': group.name, 'group_id': group.id}))
                  for group in TaskGroup.objects.filter(user=request.user)]

        return {
                         'groups': groups,
                         'add_grouptask_form': TaskGroupForm(initial={'group_id': SpecialID['NEW_ID']}),
                         'current_page': 'view_task_groups',
        }

    def process_post(self, request, **kwargs):

        super().process_post(request, **kwargs)

        self.redirect_url = 'tags:view_task_groups'
        self.redirect_kwargs['username'] = request.user.username

        # Process a group which got deleted
        if 'delete_group_id' in request.POST:

            group_id = int(request.POST['delete_group_id'])
            group = get_object_or_404(TaskGroup, pk=group_id)
            group.delete()


        # Process a group which got added or edited
        if 'upsert_group' in request.POST:

            form = TaskGroupForm(request.POST)

            if form.is_valid():

                group_name = form.cleaned_data['name']
                group_id = form.cleaned_data['group_id']



                # If the group has been edited
                if group_id != SpecialID['NEW_ID']:
                    group = get_object_or_404(TaskGroup, pk=group_id)

                    # Check user doesn't already have a group with this name
                    if TaskGroup.objects.filter(name=group_name).filter(user=request.user).exclude(pk=group.id).exists():
                        raise UserError(_("You already have a group named %(group_name)s ") % {'group_name': group_name}, "group_error")

                    group.name = group_name
                else:

                    # Check user doesn't already have a group with this name
                    if TaskGroup.objects.filter(name=group_name).filter(user=request.user).exists():
                        raise UserError(_("You already have a group named %(group_name)s ") % {'group_name': group_name}, "group_error")

                    group = TaskGroup.objects.create(name=group_name, user=request.user)

                group.save()

            else:
                raise FormError({'form': form})

@method_decorator(login_required, name='dispatch')
class ViewTasksView(BaseView):
    template_name = 'tags/tasks/view_tasks.html'

    def get_context_data(self, request, group_name, **kwargs):

        group = get_object_or_404(TaskGroup, name=group_name, user=request.user)
        tasks = [(task, task.statusClass(), TaskForm(initial={'name': task.name, 'task_id': task.id})) for task in Task.objects.filter(group=group)]

        (total_inprogress_tasks,
        total_completed_tasks,
        total_tasks,
        total_inprogress_prc,
        total_completed_prc) = group.get_stats()

        return {
                'current_page': 'view_task_groups',
                'tasks': tasks,
                'group': group,
                'add_task_form': TaskForm(initial={'task_id': SpecialID['NEW_ID']}),
                'total_inprogress_tasks': total_inprogress_tasks,
                'total_completed_tasks': total_completed_tasks,
                'total_tasks': total_tasks,
                'total_inprogress_prc': total_inprogress_prc,
                'total_completed_prc': total_completed_prc,
        }

    def process_post(self, request, group_name, **kwargs):

        super().process_post(request, **kwargs)

        group = get_object_or_404(TaskGroup, name=group_name, user=request.user)
        self.redirect_url = 'tags:view_tasks'
        self.redirect_kwargs['group_name'] = group_name
        self.redirect_kwargs['username'] = request.user.username

        # Process a task which got deleted
        if 'delete_task_id' in request.POST:
            task_id = int(request.POST['delete_task_id'])

            task = get_object_or_404(Task, pk=task_id)

            task.delete()

        # Process a task which got added or edited
        if 'upsert_task' in request.POST:

            form = TaskForm(request.POST)

            if form.is_valid():

                task_name = form.cleaned_data['name']
                task_id = form.cleaned_data['task_id']

                # If the task has been edited
                if task_id != SpecialID['NEW_ID']:
                    task = get_object_or_404(Task, pk=task_id)

                    task.name = task_name
                else:
                    task = Task.objects.create(name=task_name, added_date=timezone.now(), group=group)

                task.save()

            else:
                raise FormError({'form': form})

        # Set task as completed
        if 'task_completed_id' in request.POST:

            task_id = int(request.POST['task_completed_id'])
            task = get_object_or_404(Task, pk=task_id)
            task.state = TASK_COMPLETED
            task.save()

        # Set task as in progress
        if 'task_inprogress_id' in request.POST:

            task_id = int(request.POST['task_inprogress_id'])
            task = get_object_or_404(Task, pk=task_id)
            task.state = TASK_INPROGRESS
            task.save()

        # Set task as to start
        if 'task_tostart_id' in request.POST:

            task_id = int(request.POST['task_tostart_id'])
            task = get_object_or_404(Task, pk=task_id)
            task.state = TASK_TOSTART
            task.save()


