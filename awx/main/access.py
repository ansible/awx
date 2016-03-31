# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
import sys
import logging

# Django
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied

# AWX
from awx.main.utils import * # noqa
from awx.main.models import * # noqa
from awx.main.models.mixins import ResourceMixin
from awx.main.models.rbac import ALL_PERMISSIONS
from awx.api.license import LicenseForbids
from awx.main.task_engine import TaskSerializer
from awx.main.conf import tower_settings

__all__ = ['get_user_queryset', 'check_user_access',
           'user_accessible_objects', 'user_accessible_by',
           'user_admin_role',]

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

@property
def user_admin_role(self):
    return Role.objects.get(content_type=ContentType.objects.get_for_model(User), object_id=self.id)

def user_accessible_objects(user, permissions):
    return ResourceMixin._accessible_objects(User, user, permissions)

def user_accessible_by(instance, user, permissions):
    perms = get_user_permissions_on_resource(instance, user)
    if perms is None:
        return False
    for k in permissions:
        if k not in perms or perms[k] < permissions[k]:
            return False
    return True

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
            logger.debug('%s.%s not found', access_instance.__class__.__name__,
                         'can_%s' % action)
            continue
        result = access_method(*args, **kwargs)
        logger.debug('%s.%s %r returned %r', access_instance.__class__.__name__,
                     access_method.__name__, args, result)
        if result:
            return result
    return False

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
        return bool(obj and self.get_queryset().filter(pk=obj.pk).exists())

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

    def check_license(self, add_host=False, feature=None, check_expiration=True):
        reader = TaskSerializer()
        validation_info = reader.from_database()
        if ('test' in sys.argv or 'py.test' in sys.argv[0] or 'jenkins' in sys.argv) and not os.environ.get('SKIP_LICENSE_FIXUP_FOR_TEST', ''):
            validation_info['free_instances'] = 99999999
            validation_info['time_remaining'] = 99999999
            validation_info['grace_period_remaining'] = 99999999

        if check_expiration and validation_info.get('time_remaining', None) is None:
            raise PermissionDenied("license is missing")
        if check_expiration and validation_info.get("grace_period_remaining") <= 0:
            raise PermissionDenied("license has expired")

        free_instances = validation_info.get('free_instances', 0)
        available_instances = validation_info.get('available_instances', 0)
        if add_host and free_instances == 0:
            raise PermissionDenied("license count of %s instances has been reached" % available_instances)
        elif add_host and free_instances < 0:
            raise PermissionDenied("license count of %s instances has been exceeded" % available_instances)
        elif not add_host and free_instances < 0:
            raise PermissionDenied("host count exceeds available instances")

        if feature is not None:
            if "features" in validation_info and not validation_info["features"].get(feature, False):
                raise LicenseForbids("Feature %s is not enabled in the active license" % feature)
            elif "features" not in validation_info:
                raise LicenseForbids("Features not found in active license")


class UserAccess(BaseAccess):
    '''
    I can see user records when:
     - I'm a useruser
     - I'm in a role with them (such as in an organization or team)
     - They are in a role which includes a role of mine
     - I am in a role that includes a role of theirs
    I can change some fields for a user (mainly password) when I am that user.
    I can change all fields for a user (admin access) or delete when:
     - I'm a superuser.
     - I'm their org admin.
    '''

    model = User

    def get_queryset(self):
        if self.user.is_superuser:
            return User.objects.all()

        if tower_settings.ORG_ADMINS_CAN_SEE_ALL_USERS and self.user.admin_of_organizations.exists():
            return User.objects.all()

        viewable_users_set = set()
        viewable_users_set.update(self.user.roles.values_list('ancestors__members__id', flat=True))
        viewable_users_set.update(self.user.roles.values_list('descendents__members__id', flat=True))

        return User.objects.filter(id__in=viewable_users_set)

    def can_add(self, data):
        if data is not None and 'is_superuser' in data:
            if to_python_boolean(data['is_superuser'], allow_none=True) and not self.user.is_superuser:
                return False
        if self.user.is_superuser:
            return True
        return Organization.accessible_objects(self.user, ALL_PERMISSIONS).exists()

    def can_change(self, obj, data):
        if data is not None and 'is_superuser' in data:
            if to_python_boolean(data['is_superuser'], allow_none=True) and not self.user.is_superuser:
                return False
        # A user can be changed if they are themselves, or by org admins or
        # superusers.  Change permission implies changing only certain fields
        # that a user should be able to edit for themselves.
        return bool(self.user == obj or self.can_admin(obj, data))

    def can_admin(self, obj, data):
        # Admin implies changing all user fields.
        if self.user.is_superuser:
            return True
        return Organization.objects.filter(member_role__members=obj, admin_role__members=self.user).exists()

    def can_delete(self, obj):
        if obj == self.user:
            # cannot delete yourself
            return False
        super_users = User.objects.filter(is_superuser=True)
        if obj.is_superuser and super_users.count() == 1:
            # cannot delete the last active superuser
            return False
        return obj.accessible_by(self.user, {'delete': True})


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
        qs = self.model.accessible_objects(self.user, {'read':True})
        return qs.select_related('created_by', 'modified_by').all()

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        return obj.accessible_by(self.user, ALL_PERMISSIONS)

    def can_delete(self, obj):
        self.check_license(feature='multiple_organizations', check_expiration=False)
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
    I can run ad hoc commands when:
     - I'm a superuser.
     - I'm an org admin of the inventory's org.
     - I have read/write/admin permission on an inventory with the run_ad_hoc_commands flag set.
    '''

    model = Inventory

    def get_queryset(self, allowed=None, ad_hoc=None):
        qs = self.model.accessible_objects(self.user, {'read': True})
        return qs.select_related('created_by', 'modified_by', 'organization').all()

    def can_read(self, obj):
        return obj.accessible_by(self.user, {'read': True})

    def can_add(self, data):
        # If no data is specified, just checking for generic add permission?
        if not data:
            return Organization.accessible_objects(self.user, ALL_PERMISSIONS).exists()
        if self.user.is_superuser:
            return True

        org_pk = get_pk_from_dict(data, 'organization')
        org = get_object_or_400(Organization, pk=org_pk)
        return org.accessible_by(self.user, {'read': True, 'create':True, 'update': True, 'delete': True})

    def can_change(self, obj, data):
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            org = get_object_or_400(Organization, pk=org_pk)
            if not org.accessible_by(self.user, {'read': True, 'create':True, 'update': True, 'delete': True}):
                return False
        # Otherwise, just check for write permission.
        return obj.accessible_by(self.user, {'read': True, 'create':True, 'update': True, 'delete': True})

    def can_admin(self, obj, data):
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            org = get_object_or_400(Organization, pk=org_pk)
            if not org.accessible_by(self.user, ALL_PERMISSIONS):
                return False
        # Otherwise, just check for admin permission.
        return obj.accessible_by(self.user, ALL_PERMISSIONS)

    def can_delete(self, obj):
        return self.can_admin(obj, None)

    def can_run_ad_hoc_commands(self, obj):
        return obj.accessible_by(self.user, {'execute': True})

class HostAccess(BaseAccess):
    '''
    I can see hosts whenever I can see their inventory.
    I can change or delete hosts whenver I can change their inventory.
    '''

    model = Host

    def get_queryset(self):
        qs = self.model.accessible_objects(self.user, {'read':True})
        qs = qs.select_related('created_by', 'modified_by', 'inventory',
                               'last_job__job_template',
                               'last_job_host_summary__job')
        return qs.prefetch_related('groups').all()

    def can_read(self, obj):
        return obj and obj.inventory.accessible_by(self.user, {'read':True})

    def can_add(self, data):
        if not data or 'inventory' not in data:
            return False

        # Checks for admin or change permission on inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = get_object_or_400(Inventory, pk=inventory_pk)
        if not inventory.accessible_by(self.user, {'read':True, 'create':True}):
            return False

        # Check to see if we have enough licenses
        self.check_license(add_host=True)
        return True

    def can_change(self, obj, data):
        # Prevent moving a host to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied('Unable to change inventory on a host')
        # Checks for admin or change permission on inventory, controls whether
        # the user can edit variable data.
        return obj and obj.inventory.accessible_by(self.user, {'read':True, 'update':True, 'write':True})

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if not super(HostAccess, self).can_attach(obj, sub_obj, relationship,
                                                  data, skip_sub_obj_read_check):
            return False
        # Prevent assignments between different inventories.
        if obj.inventory != sub_obj.inventory:
            raise ParseError('Cannot associate two items from different inventories')
        return True

    def can_delete(self, obj):
        return obj and obj.inventory.accessible_by(self.user, {'delete':True})

class GroupAccess(BaseAccess):
    '''
    I can see groups whenever I can see their inventory.
    I can change or delete groups whenever I can change their inventory.
    '''

    model = Group

    def get_queryset(self):
        qs = self.model.accessible_objects(self.user, {'read':True})
        qs = qs.select_related('created_by', 'modified_by', 'inventory')
        return qs.prefetch_related('parents', 'children', 'inventory_source').all()

    def can_read(self, obj):
        return obj and obj.inventory.accessible_by(self.user, {'read':True})

    def can_add(self, data):
        if not data or 'inventory' not in data:
            return False
        # Checks for admin or change permission on inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = get_object_or_400(Inventory, pk=inventory_pk)
        return inventory.accessible_by(self.user, {'read':True, 'create':True})

    def can_change(self, obj, data):
        # Prevent moving a group to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied('Unable to change inventory on a group')
        # Checks for admin or change permission on inventory, controls whether
        # the user can attach subgroups or edit variable data.
        return obj and obj.inventory.accessible_by(self.user, {'read':True, 'update':True, 'write':True})

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
            if parent_pks & child_pks:
                return False
        return True

    def can_delete(self, obj):
        return obj and obj.inventory.accessible_by(self.user, {'delete':True})

class InventorySourceAccess(BaseAccess):
    '''
    I can see inventory sources whenever I can see their group or inventory.
    I can change inventory sources whenever I can change their group.
    '''

    model = InventorySource

    def get_queryset(self):
        qs = self.model.objects
        qs = qs.select_related('created_by', 'modified_by', 'group', 'inventory')
        inventory_ids = set(self.user.get_queryset(Inventory).values_list('id', flat=True))
        return qs.filter(Q(inventory_id__in=inventory_ids) |
                         Q(group__inventory_id__in=inventory_ids))

    def can_read(self, obj):
        if obj and obj.group:
            return obj.group.accessible_by(self.user, {'read':True})
        elif obj and obj.inventory:
            return obj.inventory.accessible_by(self.user, {'read':True})
        else:
            return False

    def can_add(self, data):
        # Automatically created from group or management command.
        return False

    def can_change(self, obj, data):
        # Checks for admin or change permission on group.
        if obj and obj.group:
            return obj.group.accessible_by(self.user, {'read':True, 'update':True, 'write':True})
        # Can't change inventory sources attached to only the inventory, since
        # these are created automatically from the management command.
        else:
            return False

    def can_start(self, obj):
        return self.can_change(obj, {}) and obj.can_update

class InventoryUpdateAccess(BaseAccess):
    '''
    I can see inventory updates when I can see the inventory source.
    I can change inventory updates whenever I can change their source.
    I can delete when I can change/delete the inventory source.
    '''

    model = InventoryUpdate

    def get_queryset(self):
        qs = InventoryUpdate.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'inventory_source__group',
                               'inventory_source__inventory')
        inventory_sources_qs = self.user.get_queryset(InventorySource)
        return qs.filter(inventory_source__in=inventory_sources_qs)

    def can_cancel(self, obj):
        return self.can_change(obj, {}) and obj.can_cancel

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
        """Return the queryset for credentials, based on what the user is
        permitted to see.
        """
        qs = self.model.accessible_objects(self.user, {'read':True})
        return qs.select_related('created_by', 'modified_by').all()

    def can_add(self, data):
        if self.user.is_superuser:
            return True

        if 'user' in data:
            pk = get_pk_from_dict(data, 'user')
            user = get_object_or_400(User, pk=pk)
            return user.accessible_by(self.user, {'write': True})
        elif 'organization' in data:
            pk = get_pk_from_dict(data, 'organization')
            org = get_object_or_400(Organization, pk=pk)
            return org.accessible_by(self.user, {'write': True})

        return False

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        return obj.accessible_by(self.user, {'read':True, 'update': True, 'delete':True})

    def can_delete(self, obj):
        # Unassociated credentials may be marked deleted by anyone, though we
        # shouldn't ever end up with those.
        #if obj.user is None and obj.team is None:
        #    return True
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
        qs = self.model.accessible_objects(self.user, {'read':True})
        return qs.select_related('created_by', 'modified_by', 'organization').all()

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        else:
            org_pk = get_pk_from_dict(data, 'organization')
            org = get_object_or_400(Organization, pk=org_pk)
            if org.accessible_by(self.user, {'read':True, 'update':True, 'write':True}):
                return True
        return False

    def can_change(self, obj, data):
        # Prevent moving a team to a different organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            raise PermissionDenied('Unable to change organization on a team')
        return obj.organization.accessible_by(self.user, ALL_PERMISSIONS)

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
     - I created the project but it isn't associated with an organization
    I can change/delete when:
     - I am a superuser.
     - I am an admin in an organization associated with the project.
     - I created the project but it isn't associated with an organization
    '''

    model = Project

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.all()
        qs = self.model.accessible_objects(self.user, {'read':True})
        return qs.select_related('modified_by', 'credential', 'current_job', 'last_job').all()

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        qs = Organization.accessible_objects(self.user, ALL_PERMISSIONS)
        return qs.exists()

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        return obj.accessible_by(self.user, ALL_PERMISSIONS)

    def can_delete(self, obj):
        return self.can_change(obj, None)

    def can_start(self, obj):
        return self.can_change(obj, {}) and obj.can_update

class ProjectUpdateAccess(BaseAccess):
    '''
    I can see project updates when I can see the project.
    I can change when I can change the project.
    I can delete when I can change/delete the project.
    '''

    model = ProjectUpdate

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.all()
        qs = ProjectUpdate.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'project')
        project_ids = set(self.user.get_queryset(Project).values_list('id', flat=True))
        return qs.filter(project_id__in=project_ids)

    def can_cancel(self, obj):
        return self.can_change(obj, {}) and obj.can_cancel

    def can_delete(self, obj):
        return obj and obj.project.accessible_by(self.user, {'delete':True})

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
        qs = self.model.accessible_objects(self.user, {'read':True})
        return qs.select_related('created_by', 'modified_by', 'inventory', 'project',
                                 'credential', 'cloud_credential', 'next_schedule').all()

    def can_read(self, obj):
        # you can only see the job templates that you have permission to launch.
        return self.can_start(obj, validate_license=False)

    def can_add(self, data):
        '''
        a user can create a job template if they are a superuser, an org admin
        of any org that the project is a member, or if they have user or team
        based permissions tying the project to the inventory source for the
        given action as well as the 'create' deploy permission.
        Users who are able to create deploy jobs can also run normal and check (dry run) jobs.
        '''
        if not data or '_method' in data:  # So the browseable API will work?
            return True

        if 'job_type' in data and data['job_type'] == PERM_INVENTORY_SCAN:
            self.check_license(feature='system_tracking')

        if 'survey_enabled' in data and data['survey_enabled']:
            self.check_license(feature='surveys')

        if self.user.is_superuser:
            return True

        # If a credential is provided, the user should have read access to it.
        credential_pk = get_pk_from_dict(data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            if not credential.accessible_by(self.user, {'read':True}):
                return False

        # If a cloud credential is provided, the user should have read access.
        cloud_credential_pk = get_pk_from_dict(data, 'cloud_credential')
        if cloud_credential_pk:
            cloud_credential = get_object_or_400(Credential,
                                                 pk=cloud_credential_pk)
            if not cloud_credential.accessible_by(self.user, {'read':True}):
                return False

        # Check that the given inventory ID is valid.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        inventory = Inventory.objects.filter(id=inventory_pk)
        if not inventory.exists():
            return False # Does this make sense?  Maybe should check read access

        project_pk = get_pk_from_dict(data, 'project')
        if 'job_type' in data and data['job_type'] == PERM_INVENTORY_SCAN:
            org = inventory[0].organization
            accessible = org.accessible_by(self.user, {'read':True, 'update':True, 'write':True})
            if not project_pk and accessible:
                return True
            elif not accessible:
                return False
        # If the user has admin access to the project (as an org admin), should
        # be able to proceed without additional checks.
        project = get_object_or_400(Project, pk=project_pk)
        if project.accessible_by(self.user, ALL_PERMISSIONS):
            return True

        return project.accessible_by(self.user, ALL_PERMISSIONS) and inventory.accessible_by(self.user, {'read':True})

    def can_start(self, obj, validate_license=True):
        # Check license.
        if validate_license:
            self.check_license()
            if obj.job_type == PERM_INVENTORY_SCAN:
                self.check_license(feature='system_tracking')
            if obj.survey_enabled:
                self.check_license(feature='surveys')

        # Super users can start any job
        if self.user.is_superuser:
            return True
        # Check to make sure both the inventory and project exist
        if obj.inventory is None:
            return False
        if obj.job_type == PERM_INVENTORY_SCAN:
            if obj.project is None and obj.inventory.organization.accessible_by(self.user, {'read':True, 'update':True, 'write':True}):
                return True
            if not obj.inventory.organization.accessible_by(self.user, {'read':True, 'update':True, 'write':True}):
                return False
        if obj.project is None:
            return False
        # If the user has admin access to the project they can start a job
        if obj.project.accessible_by(self.user, ALL_PERMISSIONS):
            return True

        return obj.inventory.accessible_by(self.user, {'read':True}) and obj.project.accessible_by(self.user, {'read':True})

    def can_change(self, obj, data):
        data_for_change = data
        if data is not None:
            data_for_change = dict(data)
            for required_field in ('credential', 'cloud_credential', 'inventory', 'project'):
                required_obj = getattr(obj, required_field, None)
                if required_field not in data_for_change and required_obj is not None:
                    data_for_change[required_field] = required_obj.pk
        return self.can_read(obj) and self.can_add(data_for_change)

    def can_delete(self, obj):
        add_obj = dict(credential=obj.credential.id if obj.credential is not None else None,
                       cloud_credential=obj.cloud_credential.id if obj.cloud_credential is not None else None,
                       inventory=obj.inventory.id if obj.inventory is not None else None,
                       project=obj.project.id if obj.project is not None else None,
                       job_type=obj.job_type)
        return self.can_add(add_obj)

class JobAccess(BaseAccess):

    model = Job

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'job_template', 'inventory',
                               'project', 'credential', 'cloud_credential', 'job_template')
        qs = qs.prefetch_related('unified_job_template')
        if self.user.is_superuser:
            return qs.all()

        credential_ids = self.user.get_queryset(Credential)
        return qs.filter(
            credential_id__in=credential_ids,
            job_template__in=JobTemplate.accessible_objects(self.user, {'read': True})
        )

    def can_add(self, data):
        if not data or '_method' in data:  # So the browseable API will work?
            return True
        if not self.user.is_superuser:
            return False


        add_data = dict(data.items())

        # If a job template is provided, the user should have read access to it.
        job_template_pk = get_pk_from_dict(data, 'job_template')
        if job_template_pk:
            job_template = get_object_or_400(JobTemplate, pk=job_template_pk)
            add_data.setdefault('inventory', job_template.inventory.pk)
            add_data.setdefault('project', job_template.project.pk)
            add_data.setdefault('job_type', job_template.job_type)
            if job_template.credential:
                add_data.setdefault('credential', job_template.credential.pk)
        else:
            job_template = None

        return True

    def can_change(self, obj, data):
        return obj.status == 'new' and self.can_read(obj) and self.can_add(data)

    def can_delete(self, obj):
        # Allow org admins and superusers to delete jobs
        if self.user.is_superuser:
            return True
        return obj.inventory.accessible_by(self.user, ALL_PERMISSIONS)

    def can_start(self, obj):
        self.check_license()

        # A super user can relaunch a job
        if self.user.is_superuser:
            return True
        # If a user can launch the job template then they can relaunch a job from that
        # job template
        has_perm = False
        if obj.job_template is not None and obj.job_template.accessible_by(self.user, {'execute':True}):
            has_perm = True
        dep_access_inventory = obj.inventory.accessible_by(self.user, {'read':True})
        dep_access_project = obj.project is None or obj.project.accessible_by(self.user, {'read':True})
        return self.can_read(obj) and dep_access_inventory and dep_access_project and has_perm

    def can_cancel(self, obj):
        return self.can_read(obj) and obj.can_cancel

class SystemJobTemplateAccess(BaseAccess):
    '''
    I can only see/manage System Job Templates if I'm a super user
    '''

    model = SystemJobTemplate

    def can_start(self, obj):
        return self.can_read(obj)

class SystemJobAccess(BaseAccess):
    '''
    I can only see manage System Jobs if I'm a super user
    '''
    model = SystemJob

class AdHocCommandAccess(BaseAccess):
    '''
    I can only see/run ad hoc commands when:
    - I am a superuser.
    - I am an org admin and have permission to read the credential.
    - I am a normal user with a user/team permission that has at least read
      permission on the inventory and the run_ad_hoc_commands flag set, and I
      can read the credential.
    '''
    model = AdHocCommand

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'inventory',
                               'credential')
        if self.user.is_superuser:
            return qs.all()

        credential_ids = set(self.user.get_queryset(Credential).values_list('id', flat=True))
        inventory_qs = Inventory.accessible_objects(self.user, {'read': True, 'execute': True})

        return qs.filter(credential_id__in=credential_ids,
                         inventory__in=inventory_qs)

    def can_add(self, data):
        if not data or '_method' in data:  # So the browseable API will work?
            return True

        self.check_license()

        # If a credential is provided, the user should have read access to it.
        credential_pk = get_pk_from_dict(data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            if not credential.accessible_by(self.user, {'read':True}):
                return False

        # Check that the user has the run ad hoc command permission on the
        # given inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if inventory_pk:
            inventory = get_object_or_400(Inventory, pk=inventory_pk)
            if not inventory.accessible_by(self.user, {'execute': True}):
                return False

        return True

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return self.can_read(obj)

    def can_start(self, obj):
        return self.can_add({
            'credential': obj.credential_id,
            'inventory': obj.inventory_id,
        })

    def can_cancel(self, obj):
        return self.can_read(obj) and obj.can_cancel

class AdHocCommandEventAccess(BaseAccess):
    '''
    I can see ad hoc command event records whenever I can read both ad hoc
    command and host.
    '''

    model = AdHocCommandEvent

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('ad_hoc_command', 'host')

        if self.user.is_superuser:
            return qs.all()
        ad_hoc_command_qs = self.user.get_queryset(AdHocCommand)
        host_qs = self.user.get_queryset(Host)
        return qs.filter(Q(host__isnull=True) | Q(host__in=host_qs),
                         ad_hoc_command__in=ad_hoc_command_qs)

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

class JobHostSummaryAccess(BaseAccess):
    '''
    I can see job/host summary records whenever I can read both job and host.
    '''

    model = JobHostSummary

    def get_queryset(self):
        qs = self.model.objects
        qs = qs.select_related('job', 'job__job_template', 'host')
        if self.user.is_superuser:
            return qs.all()
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
        qs = self.model.objects
        qs = qs.select_related('job', 'job__job_template', 'host', 'parent')
        qs = qs.prefetch_related('hosts', 'children')

        # Filter certain "internal" events generated by async polling.
        qs = qs.exclude(event__in=('runner_on_ok', 'runner_on_failed'),
                        event_data__icontains='"ansible_job_id": "',
                        event_data__contains='"module_name": "async_status"')

        if self.user.is_superuser:
            return qs.all()

        job_qs = self.user.get_queryset(Job)
        host_qs = self.user.get_queryset(Host)
        return qs.filter(Q(host__isnull=True) | Q(host__in=host_qs), job__in=job_qs)

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

class UnifiedJobTemplateAccess(BaseAccess):
    '''
    I can see a unified job template whenever I can see the same project,
    inventory source or job template.  Unified job templates do not include
    projects without SCM configured or inventory sources without a cloud
    source.
    '''

    model = UnifiedJobTemplate

    def get_queryset(self):
        qs = self.model.objects
        project_qs = self.user.get_queryset(Project).filter(scm_type__in=[s[0] for s in Project.SCM_TYPE_CHOICES])
        inventory_source_qs = self.user.get_queryset(InventorySource).filter(source__in=CLOUD_INVENTORY_SOURCES)
        job_template_qs = self.user.get_queryset(JobTemplate)
        qs = qs.filter(Q(Project___in=project_qs) |
                       Q(InventorySource___in=inventory_source_qs) |
                       Q(JobTemplate___in=job_template_qs))
        qs = qs.select_related(
            'created_by',
            'modified_by',
            'next_schedule',
            'last_job',
            'current_job',
        )
        qs = qs.prefetch_related(
            #'project',
            'inventory',
            'credential',
            'cloud_credential',
        )

        return qs.all()

class UnifiedJobAccess(BaseAccess):
    '''
    I can see a unified job whenever I can see the same project update,
    inventory update or job.
    '''

    model = UnifiedJob

    def get_queryset(self):
        qs = self.model.objects
        project_update_qs = self.user.get_queryset(ProjectUpdate)
        inventory_update_qs = self.user.get_queryset(InventoryUpdate).filter(source__in=CLOUD_INVENTORY_SOURCES)
        job_qs = self.user.get_queryset(Job)
        ad_hoc_command_qs = self.user.get_queryset(AdHocCommand)
        system_job_qs = self.user.get_queryset(SystemJob)
        qs = qs.filter(Q(ProjectUpdate___in=project_update_qs) |
                       Q(InventoryUpdate___in=inventory_update_qs) |
                       Q(Job___in=job_qs) |
                       Q(AdHocCommand___in=ad_hoc_command_qs) |
                       Q(SystemJob___in=system_job_qs))
        qs = qs.select_related(
            'created_by',
            'modified_by',
        )
        qs = qs.prefetch_related(
            'unified_job_template',
            'project',
            'inventory',
            'credential',
            'job_template',
            'inventory_source',
            'cloud_credential',
            'project___credential',
            'inventory_source___credential',
            'inventory_source___inventory',
            'job_template__inventory',
            'job_template__project',
            'job_template__credential',
            'job_template__cloud_credential',
        )
        return qs.all()

class ScheduleAccess(BaseAccess):
    '''
    I can see a schedule if I can see it's related unified job, I can create them or update them if I have write access
    '''

    model = Schedule

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related('created_by', 'modified_by')
        qs = qs.prefetch_related('unified_job_template')
        if self.user.is_superuser:
            return qs.all()
        job_template_qs = self.user.get_queryset(JobTemplate)
        inventory_source_qs = self.user.get_queryset(InventorySource)
        project_qs = self.user.get_queryset(Project)
        unified_qs = UnifiedJobTemplate.objects.filter(jobtemplate__in=job_template_qs) | \
            UnifiedJobTemplate.objects.filter(Q(project__in=project_qs)) | \
            UnifiedJobTemplate.objects.filter(Q(inventorysource__in=inventory_source_qs))
        return qs.filter(unified_job_template__in=unified_qs)

    def can_read(self, obj):
        if self.user.is_superuser:
            return True
        if obj and obj.unified_job_template:
            job_class = obj.unified_job_template
            return self.user.can_access(type(job_class), 'read', obj.unified_job_template)
        else:
            return False

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        pk = get_pk_from_dict(data, 'unified_job_template')
        obj = get_object_or_400(UnifiedJobTemplate, pk=pk)
        if obj:
            return self.user.can_access(type(obj), 'change', obj, None)
        else:
            return False

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        if obj and obj.unified_job_template:
            job_class = obj.unified_job_template
            return self.user.can_access(type(job_class), 'change', job_class, None)
        else:
            return False

    def can_delete(self, obj):
        if self.user.is_superuser:
            return True
        if obj and obj.unified_job_template:
            job_class = obj.unified_job_template
            return self.user.can_access(type(job_class), 'change', job_class, None)
        else:
            return False

class NotifierAccess(BaseAccess):
    '''
    I can see/use a notifier if I have permission to
    '''
    model = Notifier

    def get_queryset(self):
        return self.model.objects.distinct().all()

class NotificationAccess(BaseAccess):
    '''
    I can see/use a notification if I have permission to
    '''
    model = Notification

    def get_queryset(self):
        return self.model.objects.distinct().all()

class LabelAccess(BaseAccess):
    '''
    I can see/use a Label if I have permission to
    '''
    model = Label

    def get_queryset(self):
        return self.model.objects.distinct().all()

    def can_delete(self, obj):
        return False

class ActivityStreamAccess(BaseAccess):
    '''
    I can see activity stream events only when I have permission on all objects included in the event
    '''

    model = ActivityStream

    def get_queryset(self):
        qs = self.model.objects
        qs = qs.select_related('actor')
        qs = qs.prefetch_related('organization', 'user', 'inventory', 'host', 'group', 'inventory_source',
                                 'inventory_update', 'credential', 'team', 'project', 'project_update',
                                 'permission', 'job_template', 'job')
        if self.user.is_superuser:
            return qs.all()

        #Inventory filter
        inventory_qs = self.user.get_queryset(Inventory)
        qs = qs.filter(inventory__in=inventory_qs)

        #Host filter
        qs = qs.filter(host__inventory__in=inventory_qs)

        #Group filter
        qs = qs.filter(group__inventory__in=inventory_qs)

        #Inventory Source Filter
        qs = qs.filter(Q(inventory_source__inventory__in=inventory_qs) |
                       Q(inventory_source__group__inventory__in=inventory_qs))

        #Inventory Update Filter
        qs = qs.filter(Q(inventory_update__inventory_source__inventory__in=inventory_qs) |
                       Q(inventory_update__inventory_source__group__inventory__in=inventory_qs))

        #Credential Update Filter
        credential_qs = self.user.get_queryset(Credential)
        qs = qs.filter(credential__in=credential_qs)

        #Team Filter
        team_qs = self.user.get_queryset(Team)
        qs = qs.filter(team__in=team_qs)

        #Project Filter
        project_qs = self.user.get_queryset(Project)
        qs = qs.filter(project__in=project_qs)

        #Project Update Filter
        qs = qs.filter(project_update__project__in=project_qs)

        #Job Template Filter
        jobtemplate_qs = self.user.get_queryset(JobTemplate)
        qs = qs.filter(job_template__in=jobtemplate_qs)

        #Job Filter
        job_qs = self.user.get_queryset(Job)
        qs = qs.filter(job__in=job_qs)

        # Ad Hoc Command Filter
        ad_hoc_command_qs = self.user.get_queryset(AdHocCommand)
        qs = qs.filter(ad_hoc_command__in=ad_hoc_command_qs)

        return qs.all()

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

class CustomInventoryScriptAccess(BaseAccess):

    model = CustomInventoryScript

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.distinct().all()
        return self.model.accessible_objects(self.user, {'read':True}).all()

    def can_read(self, obj):
        if self.user.is_superuser:
            return True
        return obj.accessible_by(self.user, {'read':True})

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        return False

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True
        return False

    def can_delete(self, obj):
        if self.user.is_superuser:
            return True
        return False


class TowerSettingsAccess(BaseAccess):
    '''
    - I can see settings when
      - I am a super user
    - I can edit settings when
      - I am a super user
    - I can clear settings when
      - I am a super user
    '''

    model = TowerSettings

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.none()

    def can_change(self, obj, data):
        return self.user.is_superuser

    def can_delete(self, obj):
        return self.user.is_superuser


class RoleAccess(BaseAccess):
    '''
    - I can see roles when
      - I am a super user
      - I am a member of that role
      - The role is a descdendent role of a role I am a member of
      - The role is an implicit role of an object that I can see a role of.
    '''

    model = Role

    def get_queryset(self):
        if self.user.is_superuser:
            return self.model.objects.all()
        return Role.objects.none()

    def can_change(self, obj, data):
        return self.user.is_superuser

    def can_read(self, obj):
        if not obj:
            return False
        if self.user.is_superuser:
            return True

        if obj.object_id:
            sister_roles = Role.objects.filter(
                content_type = obj.content_type,
                object_id = obj.object_id
            )
        else:
            sister_roles = obj
        return self.user.roles.filter(descendents__in=sister_roles).exists()

    def can_add(self, obj, data):
        # Unsupported for now
        return False

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        return self.can_unattach(obj, sub_obj, relationship)

    def can_unattach(self, obj, sub_obj, relationship):
        if self.user.is_superuser:
            return True
        if obj.object_id and \
           isinstance(obj.content_object, ResourceMixin) and \
           obj.content_object.accessible_by(self.user, {'write': True}):
            return True
        return False

    def can_delete(self, obj):
        # Unsupported for now
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
register_access(JobTemplate, JobTemplateAccess)
register_access(Job, JobAccess)
register_access(JobHostSummary, JobHostSummaryAccess)
register_access(JobEvent, JobEventAccess)
register_access(SystemJobTemplate, SystemJobTemplateAccess)
register_access(SystemJob, SystemJobAccess)
register_access(AdHocCommand, AdHocCommandAccess)
register_access(AdHocCommandEvent, AdHocCommandEventAccess)
register_access(Schedule, ScheduleAccess)
register_access(UnifiedJobTemplate, UnifiedJobTemplateAccess)
register_access(UnifiedJob, UnifiedJobAccess)
register_access(ActivityStream, ActivityStreamAccess)
register_access(CustomInventoryScript, CustomInventoryScriptAccess)
register_access(TowerSettings, TowerSettingsAccess)
register_access(Role, RoleAccess)
register_access(Notifier, NotifierAccess)
register_access(Notification, NotificationAccess)
register_access(Label, LabelAccess)
