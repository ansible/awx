# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import json
import urllib

from django.conf.urls import *
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from ansibleworks.main.models import *
from ansibleworks.main.forms import *

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

try:
    admin.site.unregister(User)
except admin.site.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# FIXME: Hide auth.Group admin

class BaseModelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        # Automatically set created_by when saved from the admin.
        # FIXME: Doesn't handle inline model instances yet.
        if hasattr(obj, 'created_by') and obj.created_by is None:
            obj.created_by = request.user
        return super(BaseModelAdmin, self).save_model(request, obj, form, change)

class OrganizationAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    list_filter = ('active', 'tags')
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'description',)}),
        (_('Members'), {'fields': ('users', 'admins',)}),
        (_('Projects'), {'fields': ('projects',)}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by')
    filter_horizontal = ('users', 'admins', 'projects')

class InventoryHostInline(admin.StackedInline):
    
    model = Host
    extra = 0
    fields = ('name', 'description', 'active', 'tags')

class InventoryGroupInline(admin.StackedInline):

    model = Group
    extra = 0
    fields = ('name', 'description', 'active', 'parents', 'hosts', 'tags')
    filter_horizontal = ('parents', 'hosts')

class InventoryAdmin(BaseModelAdmin):

    list_display = ('name', 'organization', 'description', 'active')
    list_filter = ('organization', 'active')
    form = InventoryAdminForm
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'organization', 'description',
                           'variables')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by')
    inlines = [InventoryHostInline, InventoryGroupInline]

class JobHostSummaryInline(admin.TabularInline):

    model = JobHostSummary
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False

class JobEventInline(admin.StackedInline):

    model = JobEvent
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False

    def get_event_data_display(self, obj):
        return format_html('<pre class="json-display">{0}</pre>',
                           json.dumps(obj.event_data, indent=4))
    get_event_data_display.short_description = _('Event data')
    get_event_data_display.allow_tags = True

class JobHostSummaryInlineForHost(JobHostSummaryInline):

    fields = ('job', 'changed', 'dark', 'failures', 'ok', 'processed',
              'skipped', 'failed')
    readonly_fields = ('job', 'changed', 'dark', 'failures', 'ok', 'processed',
                       'skipped', 'failed')

class JobEventInlineForHost(JobEventInline):

    fields = ('job', 'created', 'event', 'get_event_data_display')
    readonly_fields = ('job', 'created', 'event', 'get_event_data_display')

class HostAdmin(BaseModelAdmin):

    list_display = ('name', 'inventory', 'description', 'active')
    list_filter = ('inventory', 'active')
    form = HostAdminForm
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'inventory', 'description',
                           'variables',
        )}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by')
    # FIXME: Edit reverse of many to many for groups.
    inlines = [JobHostSummaryInlineForHost, JobEventInlineForHost]

class GroupAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    form = GroupAdminForm
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'inventory', 'description',
                            'parents', 'variables')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by')
    filter_horizontal = ('parents', 'hosts')

class CredentialAdmin(BaseModelAdmin):

    fieldsets = (
        (None, {'fields': (('name', 'active'), ('user', 'team'), 'description')}),
        (_('Auth Info'), {'fields': (('ssh_username', 'ssh_password'),
                                     'ssh_key_data', 'ssh_key_unlock',
                                     ('sudo_username', 'sudo_password'))}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by')

class TeamAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('projects', 'users')

class ProjectAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'description', 'local_path',
                            'get_playbooks_display')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by', 'get_playbooks_display')
    form = ProjectAdminForm

    def get_playbooks_display(self, obj):
        return '<br/>'.join([format_html('{0}', x) for x in
                             obj.playbooks])
    get_playbooks_display.short_description = _('Playbooks')
    get_playbooks_display.allow_tags = True

class PermissionAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')

class JobTemplateAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active', 'get_create_link_display',
                    'get_jobs_link_display')
    fieldsets = (
        (None, {'fields': ('name', 'active', 'description',
                           'get_create_link_display', 'get_jobs_link_display')}),
        (_('Job Parameters'), {'fields': ('inventory', 'project', 'playbook',
                                          'credential', 'job_type')}),
        (_('More Options'), {'fields': ('forks', 'limit', 'verbosity',
                             'extra_vars', 'job_tags', 'host_config_key'),
                             'classes': ('collapse',)}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
    )
    readonly_fields = ('created', 'created_by', 'get_create_link_display',
                       'get_jobs_link_display')
    form = JobTemplateAdminForm

    def get_create_link_display(self, obj):
        if not obj or not obj.pk:
            return ''
        info = Job._meta.app_label, Job._meta.module_name
        create_url = reverse('admin:%s_%s_add' % info,
                             current_app=self.admin_site.name)
        create_opts = {
            'job_template': obj.pk,
            'job_type': obj.job_type,
            'description': obj.description,
            'name': '%s %s' % (obj.name, now().isoformat()),
        }
        if obj.inventory:
            create_opts['inventory'] = obj.inventory.pk
        if obj.project:
            create_opts['project'] = obj.project.pk
        if obj.playbook:
            create_opts['playbook'] = obj.playbook
        if obj.credential:
            create_opts['credential'] = obj.credential.pk
        if obj.forks:
            create_opts['forks'] = obj.forks
        if obj.limit:
            create_opts['limit'] = obj.limit
        if obj.verbosity:
            create_opts['verbosity'] = obj.verbosity
        if obj.extra_vars:
            create_opts['extra_vars'] = obj.extra_vars
        if obj.job_tags:
            create_opts['job_tags'] = obj.job_tags
        create_url += '?%s' % urllib.urlencode(create_opts)
        return format_html('<a href="{0}">{1}</a>', create_url, 'Create Job')
    get_create_link_display.short_description = _('Create Job')
    get_create_link_display.allow_tags = True

    def get_jobs_link_display(self, obj):
        if not obj or not obj.pk:
            return ''
        info = Job._meta.app_label, Job._meta.module_name
        jobs_url = reverse('admin:%s_%s_changelist' % info,
                           current_app=self.admin_site.name)
        jobs_url += '?job_template__id__exact=%d' % obj.pk
        return format_html('<a href="{0}">{1}</a>', jobs_url, 'View Jobs')
    get_jobs_link_display.short_description = _('View Jobs')
    get_jobs_link_display.allow_tags = True

class JobHostSummaryInlineForJob(JobHostSummaryInline):

    fields = ('host', 'changed', 'dark', 'failures', 'ok', 'processed',
              'skipped', 'failed')
    readonly_fields = ('host', 'changed', 'dark', 'failures', 'ok',
                       'processed', 'skipped', 'failed')

class JobEventInlineForJob(JobEventInline):

    fields = ('created', 'event', 'get_event_data_display', 'failed', 'host')
    readonly_fields = ('created', 'event', 'get_event_data_display', 'failed',
                       'host')

class JobAdmin(BaseModelAdmin):

    list_display = ('name', 'job_template', 'project', 'playbook', 'status')
    list_filter = ('status',)
    fieldsets = (
        (None, {'fields': ('name', 'job_template', 'description')}),
        (_('Job Parameters'), {'fields': ('inventory', 'project', 'playbook',
                                          'credential', 'job_type')}),
        (_('More Options'), {'fields': ('forks', 'limit', 'verbosity',
                                        'extra_vars', 'job_tags'),
                             'classes': ('collapse',)}),
        (_('Start Job'), {'fields': ('start_job', 'ssh_password',
                                     'sudo_password', 'ssh_key_unlock')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit'), {'fields': ('created', 'created_by',)}),
        (_('Job Status'), {'fields': (('status', 'failed', 'cancel_job'),
                                      'get_result_stdout_display',
                                      'get_result_traceback_display',
                                      'celery_task_id')}),
    )
    readonly_fields = ('status', 'failed', 'get_job_template_display',
                       'get_result_stdout_display',
                       'get_result_traceback_display', 'celery_task_id',
                       'created', 'created_by')
    form = JobAdminForm
    inlines = [JobHostSummaryInlineForJob, JobEventInlineForJob]

    def get_readonly_fields(self, request, obj=None):
        ro_fields = list(super(JobAdmin, self).get_readonly_fields(request, obj))
        if obj and obj.pk and obj.status != 'new':
            ro_fields.extend(['name', 'description', 'job_template',
                              'inventory', 'project', 'playbook', 'credential',
                              'job_type', 'forks', 'limit',
                              'verbosity', 'extra_vars', 'job_tags'])
        return ro_fields

    def get_fieldsets(self, request, obj=None):
        fsets = list(super(JobAdmin, self).get_fieldsets(request, obj))
        if not obj or not obj.pk or obj.status == 'new':
            fsets = [fs for fs in fsets if
                     'created' not in fs[1]['fields'] and
                     'celery_task_id' not in fs[1]['fields']]
        if not obj or (obj and obj.pk and not obj.can_start):
            fsets = [fs for fs in fsets if 'start_job' not in fs[1]['fields']]
        if not obj or (obj and obj.pk and not obj.can_cancel):
            for fs in fsets:
                if 'celery_task_id' in fs[1]['fields']:
                    fs[1]['fields'] = ('status', 'get_result_stdout_display',
                                       'get_result_traceback_display',
                                       'celery_task_id')
        return fsets

    def get_inline_instances(self, request, obj=None):
        if obj and obj.pk and obj.status != 'new':
            return super(JobAdmin, self).get_inline_instances(request, obj)
        else:
            return []

    def get_job_template_display(self, obj):
        if obj.job_template:
            info = JobTemplate._meta.app_label, JobTemplate._meta.module_name
            job_template_url = reverse('admin:%s_%s_change' % info,
                                       args=(obj.job_template.pk,),
                                       current_app=self.admin_site.name)
            return format_html('<a href="{0}">{1}</a>', job_template_url,
                               obj.job_template)
        else:
            return _('(None)')
    get_job_template_display.short_description = _('Job template')
    get_job_template_display.allow_tags = True

    def get_result_stdout_display(self, obj):
        return format_html('<pre class="result-display">{0}</pre>',
                           obj.result_stdout or ' ')
    get_result_stdout_display.short_description = _('Stdout')
    get_result_stdout_display.allow_tags = True

    def get_result_traceback_display(self, obj):
        return format_html('<pre class="result-display">{0}</pre>',
                           obj.result_traceback or ' ')
    get_result_traceback_display.short_description = _('Traceback')
    get_result_traceback_display.allow_tags = True

admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Inventory, InventoryAdmin)
#admin.site.register(Tag, TagAdmin)
#admin.site.register(AuditTrail, AuditTrailAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Group, GroupAdmin)
#admin.site.register(VariableData, VariableDataAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(JobTemplate, JobTemplateAdmin)
admin.site.register(Job, JobAdmin)
