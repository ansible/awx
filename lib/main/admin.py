# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.


import json
import urllib

from django.conf.urls import *
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from lib.main.models import *
from lib.main.forms import *

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
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by',
                                       'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'created_by', 'audit_trail')
    filter_horizontal = ('users', 'admins', 'projects', 'tags')

class InventoryHostInline(admin.StackedInline):
    
    model = Host
    extra = 0
    fields = ('name', 'description', 'active', 'tags')
    filter_horizontal = ('tags',)

class InventoryGroupInline(admin.StackedInline):

    model = Group
    extra = 0
    fields = ('name', 'description', 'active', 'parents', 'hosts', 'tags')
    filter_horizontal = ('parents', 'hosts', 'tags')

class InventoryAdmin(BaseModelAdmin):

    list_display = ('name', 'organization', 'description', 'active')
    list_filter = ('organization', 'active')
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'organization', 'description',)}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'created_by', 'audit_trail')
    filter_horizontal = ('tags',)
    inlines = [InventoryHostInline, InventoryGroupInline]

class TagAdmin(BaseModelAdmin):

    list_display = ('name',)

#class AuditTrailAdmin(admin.ModelAdmin):
#
#    list_display = ('name', 'description', 'active')
#    not currently on model, so disabling for now.
#    filter_horizontal = ('tags',)

class VariableDataInline(admin.StackedInline):

    model = VariableData
    extra = 0
    max_num = 1
    # FIXME: Doesn't yet work as inline due to the way the OneToOne field is
    # defined.

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
              'skipped')
    readonly_fields = ('job', 'changed', 'dark', 'failures', 'ok', 'processed',
                       'skipped')

class JobEventInlineForHost(JobEventInline):

    fields = ('job', 'created', 'event', 'get_event_data_display')
    readonly_fields = ('job', 'created', 'event', 'get_event_data_display')

class HostAdmin(BaseModelAdmin):

    list_display = ('name', 'inventory', 'description', 'active')
    list_filter = ('inventory', 'active')
    #form = HostAdminForm
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'inventory', 'description', #'vdata'
        )}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'created_by', 'audit_trail')
    filter_horizontal = ('tags',)
    # FIXME: Edit reverse of many to many for groups.
    #inlines = [VariableDataInline]
    inlines = [JobHostSummaryInlineForHost, JobEventInlineForHost]

class GroupAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    fieldsets = (
        (None, {'fields': (('name', 'active'), 'inventory', 'description',
                            'parents')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'created_by', 'audit_trail')
    filter_horizontal = ('parents', 'hosts', 'tags')
    #inlines = [VariableDataInline]

class VariableDataAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class CredentialAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class TeamAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('projects', 'users', 'tags')

class ProjectAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class PermissionAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class JobTemplateAdmin(BaseModelAdmin):

    list_display = ('name', 'description', 'active', 'get_create_link_display',
                    'get_jobs_link_display')
    fieldsets = (
        (None, {'fields': ('name', 'active', 'description',
                           'get_create_link_display', 'get_jobs_link_display')}),
        (_('Job Parameters'), {'fields': ('inventory', 'project', 'credential',
                                          'job_type')}),
        #(_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by',
                                       'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'created_by', 'audit_trail',
                       'get_create_link_display', 'get_jobs_link_display')
    #filter_horizontal = ('tags',)

    def get_create_link_display(self, obj):
        info = Job._meta.app_label, Job._meta.module_name
        create_url = reverse('admin:%s_%s_add' % info,
                             current_app=self.admin_site.name)
        create_opts = {
            'job_template': obj.pk,
            'job_type': obj.job_type,
        }
        if obj.inventory:
            create_opts['inventory'] = obj.inventory.pk
        if obj.project:
            create_opts['project'] = obj.project.pk
        if obj.credential:
            create_opts['credential'] = obj.credential.pk
        #if obj.user:
        #    create_opts['user'] = obj.user.pk
        create_url += '?%s' % urllib.urlencode(create_opts)
        return format_html('<a href="{0}">{1}</a>', create_url, 'Create Job')
    get_create_link_display.short_description = _('Create Job')
    get_create_link_display.allow_tags = True

    def get_jobs_link_display(self, obj):
        info = Job._meta.app_label, Job._meta.module_name
        jobs_url = reverse('admin:%s_%s_changelist' % info,
                           current_app=self.admin_site.name)
        jobs_url += '?job_template__id__exact=%d' % obj.pk
        return format_html('<a href="{0}">{1}</a>', jobs_url, 'View Jobs')
    get_jobs_link_display.short_description = _('View Jobs')
    get_jobs_link_display.allow_tags = True

class JobHostSummaryInlineForJob(JobHostSummaryInline):

    fields = ('host', 'changed', 'dark', 'failures', 'ok', 'processed',
              'skipped')
    readonly_fields = ('host', 'changed', 'dark', 'failures', 'ok',
                       'processed', 'skipped')

class JobEventInlineForJob(JobEventInline):

    fields = ('created', 'event', 'get_event_data_display', 'host')
    readonly_fields = ('created', 'event', 'get_event_data_display', 'host')

class JobAdmin(BaseModelAdmin):

    list_display = ('name', 'job_template', 'status')
    fieldsets = (
        (None, {'fields': ('name', 'job_template', 'description')}),
        (_('Job Parameters'), {'fields': ('inventory', 'project', 'credential',
                                          'job_type')}),
        #(_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'created_by',
                            'audit_trail',)}),
        (_('Job Status'), {'fields': ('status', 'get_result_stdout_display',
                                      'get_result_stderr_display',
                                      'get_result_traceback_display',
                                      'celery_task_id')}),
    )
    readonly_fields = ('status', 'get_job_template_display',
                       'get_result_stdout_display', 'get_result_stderr_display',
                       'get_result_traceback_display', 'celery_task_id',
                       'creation_date', 'created_by', 'audit_trail',)
    filter_horizontal = ('tags',)
    inlines = [JobHostSummaryInlineForJob, JobEventInlineForJob]

    def get_readonly_fields(self, request, obj=None):
        ro_fields = list(super(JobAdmin, self).get_readonly_fields(request, obj))
        if obj and obj.pk:
            ro_fields.extend(['name', 'description', 'job_template',
                              'inventory', 'project', 'credential', 'user',
                              'job_type'])
        return ro_fields

    def get_fieldsets(self, request, obj=None):
        fsets = list(super(JobAdmin, self).get_fieldsets(request, obj))
        if not obj or not obj.pk:
            fsets = [fs for fs in fsets if
                     'creation_date' not in fs[1]['fields'] and
                     'status' not in fs[1]['fields']]
        return fsets

    def get_inline_instances(self, request, obj=None):
        if obj and obj.pk:
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

    def get_result_stderr_display(self, obj):
        return format_html('<pre class="result-display">{0}</pre>',
                           obj.result_stderr or ' ')
    get_result_stderr_display.short_description = _('Stderr')
    get_result_stderr_display.allow_tags = True

    def get_result_traceback_display(self, obj):
        return format_html('<pre class="result-display">{0}</pre>',
                           obj.result_traceback or ' ')
    get_result_traceback_display.short_description = _('Traceback')
    get_result_traceback_display.allow_tags = True

# FIXME: Add the rest of the models...

admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Tag, TagAdmin)
#admin.site.register(AuditTrail, AuditTrailAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(VariableData, VariableDataAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(JobTemplate, JobTemplateAdmin)
admin.site.register(Job, JobAdmin)
