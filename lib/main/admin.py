# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lib.main.models import *

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

class OrganizationAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    list_filter = ('active', 'tags')
    fieldsets = (
        (None, {'fields': ('name', 'active', 'created_by', 'description',)}),
        (_('Members'), {'fields': ('users', 'admins',)}),
        (_('Projects'), {'fields': ('projects',)}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'audit_trail')
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

class InventoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'organization', 'description', 'active')
    list_filter = ('organization', 'active')
    fieldsets = (
        (None, {'fields': ('name', 'organization', 'active', 'created_by',
                           'description',)}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'audit_trail')
    filter_horizontal = ('tags',)
    inlines = [InventoryHostInline, InventoryGroupInline]

class TagAdmin(admin.ModelAdmin):

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

class HostAdmin(admin.ModelAdmin):

    list_display = ('name', 'inventory', 'description', 'active')
    list_filter = ('inventory', 'active')
    fields = ('name', 'inventory', 'description', 'active', 'tags',
              'created_by', 'audit_trail')
    filter_horizontal = ('tags',)
    # FIXME: Edit reverse of many to many for groups.
    #inlines = [VariableDataInline]

class GroupAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('parents', 'hosts', 'tags')
    #inlines = [VariableDataInline]

class VariableDataAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class CredentialAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class TeamAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('projects', 'users', 'tags')

class ProjectAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('inventories', 'tags')

class PermissionAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class LaunchJobAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    fieldsets = (
        (None, {'fields': ('name', 'active', 'created_by', 'description')}),
        (_('Job Parameters'), {'fields': ('inventory', 'project', 'credential',
                                          'user', 'job_type')}),
        (_('Tags'), {'fields': ('tags',)}),
        (_('Audit Trail'), {'fields': ('creation_date', 'audit_trail',)}),
    )
    readonly_fields = ('creation_date', 'audit_trail')
    filter_horizontal = ('tags',)

class LaunchJobStatusEventInline(admin.StackedInline):

    model = LaunchJobStatusEvent
    extra = 0
    can_delete = False
    fields = ('created', 'event', 'event_data')
    readonly_fields = ('created', 'event', 'event_data')

class LaunchJobStatusAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active', 'status')
    filter_horizontal = ('tags',)
    inlines = [LaunchJobStatusEventInline]

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
admin.site.register(LaunchJob, LaunchJobAdmin)
admin.site.register(LaunchJobStatus, LaunchJobStatusAdmin)
