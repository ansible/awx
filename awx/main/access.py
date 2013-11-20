# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import sys
import logging

# Django
from django.db.models import F, Q
from django.contrib.auth.models import User

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied

# AWX
from awx.main.utils import *
from awx.main.models import *
from awx.main.licenses import LicenseReader

__all__ = ['get_user_queryset', 'check_user_access']

PERMISSION_TYPES = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_READ,
    PERM_INVENTORY_WRITE,
    PERM_INVENTORY_DEPLOY,
    PERM_INVENTORY_CHECK,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_READ = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_WRITE,
    PERM_INVENTORY_READ,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE = [
    PERM_INVENTORY_ADMIN,
    PERM_INVENTORY_WRITE,
]

PERMISSION_TYPES_ALLOWING_INVENTORY_ADMIN = [
    PERM_INVENTORY_ADMIN,
]

logger = logging.getLogger('awx.main.access')

access_registry = {
    # <model_class>: [<access_class>, ...],
    # ...
}

def register_access(model_class, access_class):
    access_classes = access_registry.setdefault(model_class, [])
    access_classes.append(access_class)

def get_user_queryset(user, model_class):
    '''
    Return a queryset for the given model_class containing only the instances
    that should be visible to the given user.
    '''
    querysets = []
    for access_class in access_registry.get(model_class, []):
        access_instance = access_class(user)
        querysets.append(access_instance.get_queryset())
    if not querysets:
        return model_class.objects.none()
    elif len(querysets) == 1:
        return querysets[0]
    else:
        queryset = model_class.objects.all()
        for qs in querysets:
            queryset = queryset.filter(pk__in=qs.values_list('pk', flat=True))
        return queryset

def check_user_access(user, model_class, action, *args, **kwargs):
    '''
    Return True if user can perform action against model_class with the
    provided parameters.
    '''
    for access_class in access_registry.get(model_class, []):
        access_instance = access_class(user)
        access_method = getattr(access_instance, 'can_%s' % action, None)
        if not access_method:
            continue
        result = access_method(*args, **kwargs)
        logger.debug('%s.%s %r returned %r', access_instance.__class__.__name__,
                     access_method.__name__, args, result)
        if result:
            return result
    return False

def get_pk_from_dict(_dict, key):
    '''
    Helper for obtaining a pk from user data dict or None if not present.
    '''
    try:
        return int(_dict[key])
    except (TypeError, KeyError, ValueError):
        return None

class BaseAccess(object):
    '''
    Base class for checking user access to a given model.  Subclasses should
    define the model attribute, override the get_queryset method to return only
    the instances the user should be able to view, and override/define can_*
    methods to verify a user's permission to perform a particular action.
    '''

    model = None

    def __init__(self, user):
        self.user = user

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.all()
        else:
            return self.model.objects.none()

    def can_read(self, obj):
        return bool(obj and self.get_queryset().filter(pk=obj.pk).count())

    def can_add(self, data):
        return self.user.is_superuser

    def can_change(self, obj, data):
        return self.user.is_superuser

    def can_write(self, obj, data):
        # Alias for change.
        return self.can_change(obj, data)

    def can_admin(self, obj, data):
        # Alias for can_change.  Can be overridden if admin vs. user change
        # permissions need to be different.
        return self.can_change(obj, data)

    def can_delete(self, obj):
        return self.user.is_superuser

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if skip_sub_obj_read_check:
            return self.can_change(obj, None)
        else:
            return bool(self.can_change(obj, None) and
                        self.user.can_access(type(sub_obj), 'read', sub_obj))

    def can_unattach(self, obj, sub_obj, relationship):
        return self.can_change(obj, None)

class UserAccess(BaseAccess):
    '''
    I can see user records when:
     - I'm a superuser.
     - I'm that user.
     - I'm their org admin.
     - I'm in an org with that user.
     - I'm on a team with that user.
    I can change some fields for a user (mainly password) when I am that user.
    I can change all fields for a user (admin access) or delete when:
     - I'm a superuser.
     - I'm their org admin.
    '''

    model = User

    def get_queryset(self):
        qs = self.model.objects.filter(is_active=True).distinct()
        if self.user.is_superuser:
            return qs
        return qs.filter(
            Q(pk=self.user.pk) |
            Q(organizations__in=self.user.admin_of_organizations.all()) |
            Q(organizations__in=self.user.organizations.all()) |
            Q(teams__in=self.user.teams.all())
        ).distinct()

    def can_add(self, data):
        return bool(self.user.is_superuser or
                    self.user.admin_of_organizations.count())

    def can_change(self, obj, data):
        # A user can be changed if they are themselves, or by org admins or
        # superusers.  Change permission implies changing only certain fields
        # that a user should be able to edit for themselves.
        return bool(self.user == obj or self.can_admin(obj, data))

    def can_admin(self, obj, data):
        # Admin implies changing all user fields.
        if self.user.is_superuser:
            return True
        return bool(obj.organizations.filter(admins__in=[self.user]).count())

    def can_delete(self, obj):
        if obj == self.user:
            # cannot delete yourself
            return False
        super_users = User.objects.filter(is_active=True, is_superuser=True)
        if obj.is_superuser and super_users.count() == 1:
            # cannot delete the last active superuser
            return False
        return bool(self.user.is_superuser or 
                    obj.organizations.filter(admins__in=[self.user]).count())

class OrganizationAccess(BaseAccess):
    '''
    I can see organizations when:
     - I am a superuser.
     - I am an admin or user in that organization.
    I can change or delete organizations when:
     - I am a superuser.
     - I'm an admin of that organization.
    '''

    model = Organization

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by')
        if self.user.is_superuser:
            return qs
        return qs.filter(Q(admins__in=[self.user]) | Q(users__in=[self.user]))

    def can_change(self, obj, data):
        return bool(self.user.is_superuser or
                    self.user in obj.admins.all())

    def can_delete(self, obj):
        return self.can_change(obj, None)

class InventoryAccess(BaseAccess):
    '''
    I can see inventory when:
     - I'm a superuser.
     - I'm an org admin of the inventory's org.
     - I have read, write or admin permissions on it.
    I can change inventory when:
     - I'm a superuser.
     - I'm an org admin of the inventory's org.
     - I have write or admin permissions on it.
    I can delete inventory when:
     - I'm a superuser.
     - I'm an org admin of the inventory's org.
     - I have admin permissions on it.
    '''

    model = Inventory

    def get_queryset(self, allowed=None):
        allowed = allowed or PERMISSION_TYPES_ALLOWING_INVENTORY_READ
        qs = Inventory.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'organization')
        if self.user.is_superuser:
            return qs
        admin_of = qs.filter(organization__admins__in=[self.user]).distinct()
        has_user_perms = qs.filter(
            permissions__user__in=[self.user],
            permissions__permission_type__in=allowed,
        ).distinct()
        has_team_perms = qs.filter(
            permissions__team__users__in=[self.user],
            permissions__permission_type__in=allowed,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

    def has_permission_types(self, obj, allowed):
        return bool(obj and self.get_queryset(allowed).filter(pk=obj.pk).count())

    def can_read(self, obj):
        return self.has_permission_types(obj, PERMISSION_TYPES_ALLOWING_INVENTORY_READ)

    def can_add(self, data):
        # If no data is specified, just checking for generic add permission?
        if not data:
            return bool(self.user.is_superuser or self.user.admin_of_organizations.count())
        # Otherwise, verify that the user has access to change the parent
        # organization of this inventory.
        if self.user.is_superuser:
            return True
        else:
            org_pk = get_pk_from_dict(data, 'organization')
            org = get_object_or_400(Organization, pk=org_pk)
            if self.user.can_access(Organization, 'change', org, None):
                return True
        return False

    def can_change(self, obj, data):
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            org = get_object_or_400(Organization, pk=org_pk)
            if not self.user.can_access(Organization, 'change', org, None):
                return False
        # Otherwise, just check for write permission.
        return self.has_permission_types(obj, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)

    def can_admin(self, obj, data):
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            org = get_object_or_400(Organization, pk=org_pk)
            if not self.user.can_access(Organization, 'change', org, None):
                return False
        # Otherwise, just check for admin permission.
        return self.has_permission_types(obj, PERMISSION_TYPES_ALLOWING_INVENTORY_ADMIN)

    def can_delete(self, obj):
        return self.can_admin(obj, None)

class HostAccess(BaseAccess):
    '''
    I can see hosts whenever I can see their inventory.
    I can change or delete hosts whenver I can change their inventory.
    '''

    model = Host

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'inventory',
                               'last_job__job_template',
                               'last_job_host_summary')
        qs = qs.prefetch_related('groups')
        inventories_qs = self.user.get_queryset(Inventory)
        return qs.filter(inventory__in=inventories_qs)

    def can_read(self, obj):
        return obj and self.user.can_access(Inventory, 'read', obj.inventory)

    def can_add(self, data):
        if not data or not 'inventory' in data:
            return False

        # Checks for admin or change permission on inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = get_object_or_400(Inventory, pk=inventory_pk)
        if not self.user.can_access(Inventory, 'change', inventory, None):
           return False

        # Check to see if we have enough licenses
        reader = LicenseReader()
        validation_info = reader.from_file()

        if 'test' in sys.argv:
            # this hack is in here so the test code can function
            # but still go down *most* of the license code path.
            validation_info['free_instances'] = 99999999

        if validation_info.get('free_instances', 0) > 0:
            # BOOKMARK
            return True
        instances = validation_info.get('available_instances', 0)
        raise PermissionDenied("license range of %s instances has been exceed" % instances)

    def can_change(self, obj, data):
        # Prevent moving a host to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied('Unable to change inventory on a host')
        # Checks for admin or change permission on inventory, controls whether
        # the user can edit variable data.
        return obj and self.user.can_access(Inventory, 'change', obj.inventory, None)

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if not super(HostAccess, self).can_attach(obj, sub_obj, relationship,
                                                  data, skip_sub_obj_read_check):
            return False
        # Prevent assignments between different inventories.
        if obj.inventory != sub_obj.inventory:
            raise ParseError('Cannot associate two items from different inventories')
        return True

class GroupAccess(BaseAccess):
    '''
    I can see groups whenever I can see their inventory.
    I can change or delete groups whenever I can change their inventory.
    '''

    model = Group

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'inventory')
        qs = qs.prefetch_related('parents', 'children')
        inventories_qs = self.user.get_queryset(Inventory)
        return qs.filter(inventory__in=inventories_qs)

    def can_read(self, obj):
        return obj and self.user.can_access(Inventory, 'read', obj.inventory)

    def can_add(self, data):
        if not data or not 'inventory' in data:
            return False
        # Checks for admin or change permission on inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = get_object_or_400(Inventory, pk=inventory_pk)
        return self.user.can_access(Inventory, 'change', inventory, None)

    def can_change(self, obj, data):
        # Prevent moving a group to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied('Unable to change inventory on a group')
        # Checks for admin or change permission on inventory, controls whether
        # the user can attach subgroups or edit variable data.
        return obj and self.user.can_access(Inventory, 'change', obj.inventory, None)

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if not super(GroupAccess, self).can_attach(obj, sub_obj, relationship,
                                                   data, skip_sub_obj_read_check):
            return False
        # Prevent assignments between different inventories.
        if obj.inventory != sub_obj.inventory:
            raise ParseError('Cannot associate two items from different inventories')
        # Prevent group from being assigned as its own (grand)child.
        if type(obj) == type(sub_obj):
            parent_pks = set(obj.all_parents.values_list('pk', flat=True))
            parent_pks.add(obj.pk)
            child_pks = set(sub_obj.all_children.values_list('pk', flat=True))
            child_pks.add(sub_obj.pk)
            #print parent_pks, child_pks
            if parent_pks & child_pks:
                return False
        return True

class InventorySourceAccess(BaseAccess):
    '''
    I can see inventory sources whenever I can see their group or inventory.
    I can change inventory sources whenever I can change their group.
    '''

    model = InventorySource

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'group')
        inventories_qs = self.user.get_queryset(Inventory)
        return qs.filter(Q(inventory__in=inventories_qs) |
                         Q(group__inventory__in=inventories_qs))

    def can_read(self, obj):
        if obj and obj.group:
            return self.user.can_access(Group, 'read', obj.group)
        elif obj and obj.inventory:
            return self.user.can_access(Inventory, 'read', obj.inventory)
        else:
            return False

    def can_add(self, data):
        # Automatically created from group or management command.
        return False

    def can_change(self, obj, data):
        # Checks for admin or change permission on group.
        if obj and obj.group:
            return self.user.can_access(Group, 'change', obj.group, None)
        # Can't change inventory sources attached to only the inventory, since
        # these are created automatically from the management command.
        else:
            return False

class InventoryUpdateAccess(BaseAccess):
    '''
    I can see inventory updates when I can see the inventory source.
    I can change inventory updates whenever I can change their source.
    '''

    model = InventoryUpdate

    def get_queryset(self):
        qs = InventoryUpdate.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'group')
        inventory_sources_qs = self.user.get_queryset(InventorySource)
        return qs.filter(inventory_source__in=inventory_sources_qs)

class CredentialAccess(BaseAccess):
    '''
    I can see credentials when:
     - I'm a superuser.
     - It's a user credential and it's my credential.
     - It's a user credential and I'm an admin of an organization where that
       user is a member of admin of the organization.
     - It's a team credential and I'm an admin of the team's organization.
     - It's a team credential and I'm a member of the team.
    I can change/delete when:
     - I'm a superuser.
     - It's my user credential.
     - It's a user credential for a user in an org I admin.
     - It's a team credential for a team in an org I admin.
    '''

    model = Credential

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'user', 'team')
        if self.user.is_superuser:
            return qs
        orgs_as_admin = self.user.admin_of_organizations.all()
        return qs.filter(
            Q(user=self.user) |
            Q(user__organizations__in=orgs_as_admin) |
            Q(user__admin_of_organizations__in=orgs_as_admin) |
            Q(team__organization__in=orgs_as_admin) |
            Q(team__users__in=[self.user])
        )

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        if 'user' in data:
            user_pk = get_pk_from_dict(data, 'user')
            user_obj = get_object_or_400(User, pk=user_pk)
            return self.user.can_access(User, 'change', user_obj, None)
        if 'team' in data:
            team_pk = get_pk_from_dict(data, 'team')
            team_obj = get_object_or_400(Team, pk=team_pk)
            return self.user.can_access(Team, 'change', team_obj, None)
        return False

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        if self.user == obj.created_by:
            return True
        if obj.user:
            if self.user == obj.user:
                return True
            if obj.user.organizations.filter(admins__in=[self.user]).count():
                return True
            if obj.user.admin_of_organizations.filter(admins__in=[self.user]).count():
                return True
        if obj.team:
            if self.user in obj.team.organization.admins.all():
                return True
        return False

    def can_delete(self, obj):
        # Unassociated credentials may be marked deleted by anyone, though we
        # shouldn't ever end up with those.
        if obj.user is None and obj.team is None:
            return True
        return self.can_change(obj, None)

class TeamAccess(BaseAccess):
    '''
    I can see a team when:
     - I'm a superuser.
     - I'm an admin of the team's organization.
     - I'm a member of that team.
    I can create/change a team when:
     - I'm a superuser.
     - I'm an org admin for the team's org.
    '''

    model = Team

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'organization')
        if self.user.is_superuser:
            return qs
        return qs.filter(
            Q(organization__admins__in=[self.user]) |
            Q(users__in=[self.user])
        )

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        else:
            org_pk = get_pk_from_dict(data, 'organization')
            org = get_object_or_400(Organization, pk=org_pk)
            if self.user.can_access(Organization, 'change', org, None):
                return True
        return False

    def can_change(self, obj, data):
        # Prevent moving a team to a different organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            raise PermissionDenied('Unable to change organization on a team')
        if self.user.is_superuser:
            return True
        if self.user in obj.organization.admins.all():
            return True
        return False

    def can_delete(self, obj):
        return self.can_change(obj, None)

class ProjectAccess(BaseAccess):
    '''
    I can see projects when:
     - I am a superuser.
     - I am an admin in an organization associated with the project.
     - I am a user in an organization associated with the project.
     - I am on a team associated with the project.
     - I have been explicitly granted permission to run/check jobs using the
       project.
     - I created it (for now?).
    I can change/delete when:
     - I am a superuser.
     - I am an admin in an organization associated with the project.
     - I created it (for now?).
    '''

    model = Project

    def get_queryset(self):
        qs = Project.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'current_update', 'last_update')
        if self.user.is_superuser:
            return qs
        allowed = [PERM_INVENTORY_DEPLOY, PERM_INVENTORY_CHECK]
        return qs.filter(
            Q(created_by=self.user) |
            Q(organizations__admins__in=[self.user]) |
            Q(organizations__users__in=[self.user]) |
            Q(teams__users__in=[self.user]) |
            Q(permissions__user=self.user, permissions__permission_type__in=allowed) |
            Q(permissions__team__users__in=[self.user], permissions__permission_type__in=allowed)
        )

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        if self.user.admin_of_organizations.count():
            return True
        return False

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        if obj.created_by == self.user:
            return True
        if obj.organizations.filter(admins__in=[self.user]).count():
            return True
        return False

    def can_delete(self, obj):
        return self.can_change(obj, None)

class ProjectUpdateAccess(BaseAccess):
    '''
    I can see project updates when I can see the project.
    I can change when I can change the project.
    '''

    model = ProjectUpdate

    def get_queryset(self):
        qs = ProjectUpdate.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'project')
        projects_qs = self.user.get_queryset(Project)
        return qs.filter(project__in=projects_qs)

class PermissionAccess(BaseAccess):
    '''
    I can see a permission when:
     - I'm a superuser.
     - I'm an org admin and it's for a user in my org.
     - I'm an org admin and it's for a team in my org.
     - I'm a user and it's assigned to me.
     - I'm a member of a team and it's assigned to the team.
    I can create/change/delete when:
     - I'm a superuser.
     - I'm an org admin and the team/user is in my org and the inventory is in
       my org and the project is in my org.
    '''

    model = Permission

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'user', 'team', 'inventory',
                               'project')
        if self.user.is_superuser:
            return qs
        orgs_as_admin = self.user.admin_of_organizations.all()
        return qs.filter(
            Q(user__organizations__in=orgs_as_admin) |
            Q(user__admin_of_organizations__in=orgs_as_admin) |
            Q(team__organization__in=orgs_as_admin) |
            Q(user=self.user) |
            Q(team__users__in=[self.user])
        )

    def can_add(self, data):
        if not data:
            return True # generic add permission check
        user_pk = get_pk_from_dict(data, 'user')
        team_pk = get_pk_from_dict(data, 'team')
        if user_pk:
            user = get_object_or_400(User, pk=user_pk)
            if not self.user.can_access(User, 'admin', user, None):
                return False
        elif team_pk:
            team = get_object_or_400(Team, pk=team_pk)
            if not self.user.can_access(Team, 'admin', team, None):
                return False
        else:
            return False
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if inventory_pk:
            inventory = get_object_or_400(Inventory, pk=inventory_pk)
            if not self.user.can_access(Inventory, 'admin', inventory, None):
                return False
        project_pk = get_pk_from_dict(data, 'project')
        if project_pk:
            project = get_object_or_400(Project, pk=project_pk)
            if not self.user.can_access(Project, 'admin', project, None):
                return False
        # FIXME: user/team, inventory and project should probably all be part
        # of the same organization.
        return True

    def can_change(self, obj, data):
        # Prevent assigning a permission to a different user.
        user_pk = get_pk_from_dict(data, 'user')
        if obj and user_pk and obj.user and obj.user.pk != user_pk:
            raise PermissionDenied('Unable to change user on a permission')
        # Prevent assigning a permission to a different team.
        team_pk = get_pk_from_dict(data, 'team')
        if obj and team_pk and obj.team and obj.team.pk != team_pk:
            raise PermissionDenied('Unable to change team on a permission')
        if self.user.is_superuser:
            return True
        # If changing inventory, verify access to the new inventory.
        new_inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and new_inventory_pk and obj.inventory and obj.inventory.pk != new_inventory_pk:
            inventory = get_object_or_400(Inventory, pk=new_inventory_pk)
            if not self.user.can_access(Inventory, 'admin', inventory, None):
                return False
        # If changing project, verify access to the new project.
        new_project = get_pk_from_dict(data, 'project')
        if obj and new_project and obj.project and obj.project.pk != new_project:
            project = get_object_or_400(Project, pk=new_project)
            if not self.user.can_access(Project, 'admin', project, None):
                return False
        # Check for admin access to the user or team.
        if obj.user and self.user.can_access(User, 'admin', obj.user, None):
            return True
        if obj.team and self.user.can_access(Team, 'admin', obj.team, None):
            return True
        return False

    def can_delete(self, obj):
        return self.can_change(obj, None)

class JobTemplateAccess(BaseAccess):
    ''' 
    I can see job templates when:
     - I am a superuser.
     - I can read the inventory, project and credential (which means I am an
       org admin or member of a team with access to all of the above).
     - I have permission explicitly granted to check/deploy with the inventory
       and project.

    This does not mean I would be able to launch a job from the template or
    edit the template.
    '''

    model = JobTemplate

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'inventory', 'project',
                               'credential')
        if self.user.is_superuser:
            return qs
        credential_qs = self.user.get_queryset(Credential)
        base_qs = qs.filter(
            Q(credential__in=credential_qs) | Q(credential__isnull=True),
        )
        org_admin_qs = base_qs.filter(
            project__organizations__admins__in=[self.user]
        )
        allowed = [PERM_INVENTORY_CHECK, PERM_INVENTORY_DEPLOY]
        perm_qs = base_qs.filter(
            Q(inventory__permissions__user=self.user) | Q(inventory__permissions__team__users__in=[self.user]),
            Q(project__permissions__user=self.user) | Q(project__permissions__team__users__in=[self.user]),
            inventory__permissions__permission_type__in=allowed,
            project__permissions__permission_type__in=allowed,
            inventory__permissions__pk=F('project__permissions__pk'),
        )
        # FIXME: I *think* this should work... needs more testing.
        return org_admin_qs | perm_qs

    def can_read(self, obj):
        # you can only see the job templates that you have permission to launch.
        data = dict(
            inventory = obj.inventory.pk,
            project = obj.project.pk,
            job_type = obj.job_type,
        )
        if obj.credential:
            data['credential'] = obj.credential.pk
        return self.can_add(data)

    def can_add(self, data):
        '''
        a user can create a job template if they are a superuser, an org admin
        of any org that the project is a member, or if they have user or team
        based permissions tying the project to the inventory source for the
        given action.  users who are able to create deploy jobs can also make
        check (dry run) jobs.
        '''
        if not data or '_method' in data:  # So the browseable API will work?
            return True
        if self.user.is_superuser:
            return True

        # If a credential is provided, the user should have read access to it.
        credential_pk = get_pk_from_dict(data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            if not self.user.can_access(Credential, 'read', credential):
                return False

        # Check that the given inventory ID is valid.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = get_object_or_400(Inventory, pk=inventory_pk)
        
        # If the user has admin access to the project (as an org admin), should
        # be able to proceed without additional checks.
        project_pk = get_pk_from_dict(data, 'project')
        project = get_object_or_400(Project, pk=project_pk)
        if self.user.can_access(Project, 'admin', project, None):
            return True

        # Otherwise, check for explicitly granted permissions for the project
        # and inventory.
        has_perm = False
        permission_qs = Permission.objects.filter(
            Q(user=self.user) | Q(team__users__in=[self.user]),
            inventory=inventory,
            project=project,
            permission_type__in=[PERM_INVENTORY_CHECK, PERM_INVENTORY_DEPLOY],
        )
        job_type = data.get('job_type', None)
        for perm in permission_qs:
            # if you have run permissions, you can also create check jobs
            if job_type == PERM_INVENTORY_CHECK:
                has_perm = True
            # you need explicit run permissions to make run jobs
            elif job_type == PERM_INVENTORY_DEPLOY and perm.permission_type == PERM_INVENTORY_DEPLOY:
                has_perm = True
        if not has_perm:
            return False

        # shouldn't really matter with permissions given, but make sure the user
        # is also currently on the team in case they were added a per-user permission and then removed
        # from the project.
        #if not project.teams.filter(users__in=[self.user]).count():
        #    return False

        return True

    def can_change(self, obj, data):
        return self.can_read(obj) and self.can_add(data)

    def can_delete(self, obj):
        return self.can_read(obj)

class JobAccess(BaseAccess):

    model = Job

    def get_queryset(self):
        qs = self.model.objects.filter(active=True).distinct()
        qs = qs.select_related('created_by', 'job_template', 'inventory',
                               'project', 'credential')
        if self.user.is_superuser:
            return qs
        credential_qs = self.user.get_queryset(Credential)
        base_qs = qs.filter(
            credential__in=credential_qs,
        )
        org_admin_qs = base_qs.filter(
            project__organizations__admins__in=[self.user]
        )
        allowed = [PERM_INVENTORY_CHECK, PERM_INVENTORY_DEPLOY]
        perm_qs = base_qs.filter(
            Q(inventory__permissions__user=self.user) | Q(inventory__permissions__team__users__in=[self.user]),
            Q(project__permissions__user=self.user) | Q(project__permissions__team__users__in=[self.user]),
            inventory__permissions__permission_type__in=allowed,
            project__permissions__permission_type__in=allowed,
            inventory__permissions__pk=F('project__permissions__pk'),
        )
        # FIXME: I *think* this should work... needs more testing.
        return org_admin_qs | perm_qs

    def can_add(self, data):
        if not data or '_method' in data:  # So the browseable API will work?
            return True
        if self.user.is_superuser:
            return True
        add_data = dict(data.items())

        # If a job template is provided, the user should have read access to it.
        job_template_pk = get_pk_from_dict(data, 'job_template')
        if job_template_pk:
            job_template = get_object_or_400(JobTemplate, pk=job_template_pk)
            if not self.user.can_access(JobTemplate, 'read', job_template):
                return False
            add_data.setdefault('inventory', job_template.inventory.pk)
            add_data.setdefault('project', job_template.project.pk)
            add_data.setdefault('job_type', job_template.job_type)
            if job_template.credential:
                add_data.setdefault('credential', job_template.credential.pk)
        else:
            job_template = None

        # Check that the user would be able to add a job template with the
        # same data.
        if not self.user.can_access(JobTemplate, 'add', add_data):
            return False

        return True

    def can_change(self, obj, data):
        return obj.status == 'new' and self.can_read(obj) and self.can_add(data)

    def can_delete(self, obj):
        return self.can_read(obj)

    def can_start(self, obj):
        return self.can_read(obj) and obj.can_start

    def can_cancel(self, obj):
        return self.can_read(obj) and obj.can_cancel

class JobHostSummaryAccess(BaseAccess):
    '''
    I can see job/host summary records whenever I can read both job and host.
    '''

    model = JobHostSummary

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'job', 'job__job_template',
                               'host')
        if self.user.is_superuser:
            return qs
        job_qs = self.user.get_queryset(Job)
        host_qs = self.user.get_queryset(Host)
        return qs.filter(job__in=job_qs, host__in=host_qs)

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

class JobEventAccess(BaseAccess):
    '''
    I can see job event records whenever I can read both job and host.
    '''

    model = JobEvent

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'job', 'job__job_template',
                               'host', 'parent')
        qs = qs.prefetch_related('hosts', 'children')

        # Filter certain "internal" events generating by async polling.
        qs = qs.exclude(event__in=('runner_on_ok', 'runner_on_failed'),
                        event_data__icontains='"ansible_job_id": "',
                        event_data__contains='"module_name": "async_status"')

        if self.user.is_superuser:
            return qs
        job_qs = self.user.get_queryset(Job)
        host_qs = self.user.get_queryset(Host)
        qs = qs.filter(Q(host__isnull=True) | Q(host__in=host_qs),
                       job__in=job_qs)
        return qs

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

register_access(User, UserAccess)
register_access(Organization, OrganizationAccess)
register_access(Inventory, InventoryAccess)
register_access(Host, HostAccess)
register_access(Group, GroupAccess)
register_access(InventorySource, InventorySourceAccess)
register_access(InventoryUpdate, InventoryUpdateAccess)
register_access(Credential, CredentialAccess)
register_access(Team, TeamAccess)
register_access(Project, ProjectAccess)
register_access(ProjectUpdate, ProjectUpdateAccess)
register_access(Permission, PermissionAccess)
register_access(JobTemplate, JobTemplateAccess)
register_access(Job, JobAccess)
register_access(JobHostSummary, JobHostSummaryAccess)
register_access(JobEvent, JobEventAccess)
