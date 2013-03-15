from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lib.main.models import *

class OrganizationAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('users', 'admins', 'projects', 'tags')

class InventoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class TagAdmin(admin.ModelAdmin):

    list_display = ('name', )

class AuditTrailAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)
    

class HostAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class GroupAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('parents', 'hosts', 'tags')

class VariableDataAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'active')
    filter_horizontal = ('tags',)

class UserAdmin(admin.ModelAdmin):

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
admin.site.register(User, UserAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(LaunchJob, LaunchJobStatusAdmin)
admin.site.register(LaunchJobStatus, LaunchJobStatusAdmin)
