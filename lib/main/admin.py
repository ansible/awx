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
    filter_horizontal = ('users', 'admins', 'projects', 'tags')

class InventoryAdmin(admin.ModelAdmin):

    fields = ('name', 'organization', 'description', 'active', 'tags',
              'created_by', 'audit_trail')
    list_display = ('name', 'organization', 'description', 'active')
    list_filter = ('organization', 'active')
    filter_horizontal = ('tags',)

class TagAdmin(admin.ModelAdmin):

    list_display = ('name', )

class AuditTrailAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)
    
class HostAdmin(admin.ModelAdmin):

    fields = ('name', 'inventory', 'description', 'active', 'tags',
              'created_by', 'audit_trail')
    list_display = ('name', 'inventory', 'description', 'active')
    list_filter = ('inventory', 'active')
    filter_horizontal = ('tags',)
    # FIXME: Edit reverse of many to many for groups.

class GroupAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('parents', 'hosts', 'tags')

class VariableDataAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class CredentialAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class TeamAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('projects', 'users', 'organization', 'tags')

class ProjectAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('inventories', 'tags')

class PermissionAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class LaunchJobAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class LaunchJobStatusAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

# FIXME: Add the rest of the models...

admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(AuditTrail, AuditTrailAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(VariableData, VariableDataAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(LaunchJob, LaunchJobStatusAdmin)
admin.site.register(LaunchJobStatus, LaunchJobStatusAdmin)
