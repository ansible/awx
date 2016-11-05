# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
import sys
import logging

# Django
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied, ValidationError

# AWX
from awx.main.utils import * # noqa
from awx.main.models import * # noqa
from awx.main.models.unified_jobs import ACTIVE_STATES
from awx.main.models.mixins import ResourceMixin
from awx.main.task_engine import TaskEnhancer
from awx.conf.license import LicenseForbids

__all__ = ['get_user_queryset', 'check_user_access',
           'user_accessible_objects',
           'user_admin_role', 'StateConflict',]

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

class StateConflict(ValidationError):
    status_code = 409

def register_access(model_class, access_class):
    access_classes = access_registry.setdefault(model_class, [])
    access_classes.append(access_class)

@property
def user_admin_role(self):
    role = Role.objects.get(
        content_type=ContentType.objects.get_for_model(User),
        object_id=self.id,
        role_field='admin_role'
    )
    # Trick the user.admin_role so that the signal filtering for RBAC activity stream works as intended.
    role.parents = [org.admin_role.pk for org in self.organizations]
    return role

def user_accessible_objects(user, role_name):
    return ResourceMixin._accessible_objects(User, user, role_name)

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

def get_user_capabilities(user, instance, **kwargs):
    '''
    Returns a dictionary of capabilities the user has on the particular
    instance.  *NOTE* This is not a direct mapping of can_* methods into this
    dictionary, it is intended to munge some queries in a way that is
    convenient for the user interface to consume and hide or show various
    actions in the interface.
    '''
    for access_class in access_registry.get(type(instance), []):
        return access_class(user).get_user_capabilities(instance, **kwargs)
    return None

def check_superuser(func):
    '''
    check_superuser is a decorator that provides a simple short circuit
    for access checks. If the User object is a superuser, return True, otherwise
    execute the logic of the can_access method.
    '''
    def wrapper(self, *args, **kwargs):
        if self.user.is_superuser:
            return True
        return func(self, *args, **kwargs)
    return wrapper

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
        if self.user.is_superuser or self.user.is_system_auditor:
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

    def can_unattach(self, obj, sub_obj, relationship, data=None):
        return self.can_change(obj, data)

    def check_related(self, field, Model, data, role_field='admin_role',
                      obj=None, mandatory=False):
        '''
        Check permission for related field, in scenarios:
         - creating a new resource, user must have permission if
           resource is specified in `data`
         - editing an existing resource, user must have permission to resource
           in `data`, as well as existing related resource on `obj`

        If obj.field is null, this does not block the action
        If `mandatory` is set, new resources require the field and
                               existing field will always be checked
        '''
        new = None
        changed = True
        is_removal = False
        if data and 'reference_obj' in data:
            # Use reference object's related fields, if given
            new = getattr(data['reference_obj'], field)
        elif data and field in data:
            # Obtain the resource specified in `data`
            raw_value = data[field]
            if isinstance(raw_value, Model):
                new = raw_value
            elif raw_value is None:
                new = None
                is_removal = True
            else:
                try:
                    new_pk = int(raw_value)
                    # Avoid database query by comparing pk to model for similarity
                    if obj and new_pk == getattr(obj, '%s_id' % field, None):
                        changed = False
                    else:
                        # Get the new resource from the database
                        new = get_object_or_400(Model, pk=new_pk)
                except (TypeError, ValueError):
                    raise ParseError(_("Bad data found in related field %s." % field))
        elif data is None or field not in data:
            changed = False

        # Obtain existing related resource
        current = None
        if obj and (changed or mandatory):
            current = getattr(obj, field)

        if obj and new == current and (not is_removal):
            # Resource not changed, like a PUT request
            changed = False

        if (not new) and (not obj) and mandatory:
            # Restrict ability to create resource without required field
            print ' superuser '
            return self.user.is_superuser

        def user_has_resource_access(resource):
            role = getattr(resource, role_field, None)
            if role is None:
                # Handle special case where resource does not have direct roles
                access_method_type = {'admin_role': 'change', 'execute_role': 'start'}[role_field]
                return self.user.can_access(type(resource), access_method_type, resource, None)
            return self.user in role

        if new and changed:
            if not user_has_resource_access(new):
                return False  # User lacks access to provided resource

        if current and (changed or mandatory):
            if not user_has_resource_access(current):
                return False  # User lacks access to existing resource

        return True  # User has access to both, permission check passed

    def check_license(self, add_host=False, feature=None, check_expiration=True):
        validation_info = TaskEnhancer().validate_enhancements()
        if ('test' in sys.argv or 'py.test' in sys.argv[0] or 'jenkins' in sys.argv) and not os.environ.get('SKIP_LICENSE_FIXUP_FOR_TEST', ''):
            validation_info['free_instances'] = 99999999
            validation_info['time_remaining'] = 99999999
            validation_info['grace_period_remaining'] = 99999999

        if check_expiration and validation_info.get('time_remaining', None) is None:
            raise PermissionDenied(_("License is missing."))
        if check_expiration and validation_info.get("grace_period_remaining") <= 0:
            raise PermissionDenied(_("License has expired."))

        free_instances = validation_info.get('free_instances', 0)
        available_instances = validation_info.get('available_instances', 0)
        if add_host and free_instances == 0:
            raise PermissionDenied(_("License count of %s instances has been reached.") % available_instances)
        elif add_host and free_instances < 0:
            raise PermissionDenied(_("License count of %s instances has been exceeded.") % available_instances)
        elif not add_host and free_instances < 0:
            raise PermissionDenied(_("Host count exceeds available instances."))

        if feature is not None:
            if "features" in validation_info and not validation_info["features"].get(feature, False):
                raise LicenseForbids(_("Feature %s is not enabled in the active license.") % feature)
            elif "features" not in validation_info:
                raise LicenseForbids(_("Features not found in active license."))

    def get_user_capabilities(self, obj, method_list=[], parent_obj=None):
        if obj is None:
            return {}
        user_capabilities = {}

        # Custom ordering to loop through methods so we can reuse earlier calcs
        for display_method in ['edit', 'delete', 'start', 'schedule', 'copy', 'adhoc', 'unattach']:
            if display_method not in method_list:
                continue

            # Validation consistency checks
            if display_method == 'copy' and isinstance(obj, JobTemplate):
                validation_errors, resources_needed_to_start = obj.resource_validation_data()
                if validation_errors:
                    user_capabilities[display_method] = False
                    continue
            elif display_method == 'start' and isinstance(obj, Group):
                if obj.inventory_source and not obj.inventory_source._can_update():
                    user_capabilities[display_method] = False
                    continue

            # Grab the answer from the cache, if available
            if hasattr(obj, 'capabilities_cache') and display_method in obj.capabilities_cache:
                user_capabilities[display_method] = obj.capabilities_cache[display_method]
                continue

            # Aliases for going form UI language to API language
            if display_method == 'edit':
                method = 'change'
            elif display_method == 'copy':
                method = 'add'
            elif display_method == 'adhoc':
                method = 'run_ad_hoc_commands'
            else:
                method = display_method

            # Shortcuts in certain cases by deferring to earlier property
            if display_method == 'schedule':
                user_capabilities['schedule'] = user_capabilities['edit']
                continue
            elif display_method == 'delete' and not isinstance(obj, (User, UnifiedJob)):
                user_capabilities['delete'] = user_capabilities['edit']
                continue
            elif display_method == 'copy' and isinstance(obj, (Group, Host)):
                user_capabilities['copy'] = user_capabilities['edit']
                continue
            elif display_method == 'start' and isinstance(obj, (Project)) and obj.scm_type == '':
                # Special case to return False for a manual project
                user_capabilities['start'] = False
                continue

            # Preprocessing before the access method is called
            data = {}
            if method == 'add':
                if isinstance(obj, JobTemplate):
                    data['reference_obj'] = obj

            # Compute permission
            access_method = getattr(self, "can_%s" % method)
            if method in ['change']: # 3 args
                user_capabilities[display_method] = access_method(obj, data)
            elif method in ['delete', 'run_ad_hoc_commands']:
                user_capabilities[display_method] = access_method(obj)
            elif method in ['start']:
                user_capabilities[display_method] = access_method(obj, validate_license=False)
            elif method in ['add']: # 2 args with data
                user_capabilities[display_method] = access_method(data)
            elif method in ['attach', 'unattach']: # parent/sub-object call
                if type(parent_obj) == Team:
                    relationship = 'parents'
                    parent_obj = parent_obj.member_role
                else:
                    relationship = 'members'
                user_capabilities[display_method] = access_method(
                    obj, parent_obj, relationship, skip_sub_obj_read_check=True, data=data)

        return user_capabilities


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
        if self.user.is_superuser or self.user.is_system_auditor:
            return User.objects.all()

        if settings.ORG_ADMINS_CAN_SEE_ALL_USERS and \
                (self.user.admin_of_organizations.exists() or self.user.auditor_of_organizations.exists()):
            return User.objects.all()

        return (
            User.objects.filter(
                pk__in=Organization.accessible_objects(self.user, 'read_role').values('member_role__members')
            ) |
            User.objects.filter(
                pk=self.user.id
            ) |
            User.objects.filter(
                pk__in=Role.objects.filter(singleton_name__in = [ROLE_SINGLETON_SYSTEM_ADMINISTRATOR, ROLE_SINGLETON_SYSTEM_AUDITOR]).values('members')
            )
        ).distinct()


    def can_add(self, data):
        if data is not None and ('is_superuser' in data or 'is_system_auditor' in data):
            if (to_python_boolean(data.get('is_superuser', 'false'), allow_none=True) or
                    to_python_boolean(data.get('is_system_auditor', 'false'), allow_none=True)) and not self.user.is_superuser:
                return False
        if self.user.is_superuser:
            return True
        return Organization.accessible_objects(self.user, 'admin_role').exists()

    def can_change(self, obj, data):
        if data is not None and ('is_superuser' in data or 'is_system_auditor' in data):
            if (to_python_boolean(data.get('is_superuser', 'false'), allow_none=True) or
                    to_python_boolean(data.get('is_system_auditor', 'false'), allow_none=True)) and not self.user.is_superuser:
                return False
        # A user can be changed if they are themselves, or by org admins or
        # superusers.  Change permission implies changing only certain fields
        # that a user should be able to edit for themselves.
        return bool(self.user == obj or self.can_admin(obj, data))

    @check_superuser
    def can_admin(self, obj, data):
        return Organization.objects.filter(Q(member_role__members=obj) | Q(admin_role__members=obj),
                                           Q(admin_role__members=self.user)).exists()

    def can_delete(self, obj):
        if obj == self.user:
            # cannot delete yourself
            return False
        super_users = User.objects.filter(is_superuser=True)
        if obj.is_superuser and super_users.count() == 1:
            # cannot delete the last active superuser
            return False
        if self.user.is_superuser:
            return True
        return False

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        "Reverse obj and sub_obj, defer to RoleAccess if this is a role assignment."
        if relationship == 'roles':
            role_access = RoleAccess(self.user)
            return role_access.can_attach(sub_obj, obj, 'members', *args, **kwargs)
        return super(UserAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        if relationship == 'roles':
            role_access = RoleAccess(self.user)
            return role_access.can_unattach(sub_obj, obj, 'members', *args, **kwargs)
        return super(UserAccess, self).can_unattach(obj, sub_obj, relationship, *args, **kwargs)


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
        qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by').all()

    @check_superuser
    def can_change(self, obj, data):
        return self.user in obj.admin_role

    def can_delete(self, obj):
        self.check_license(feature='multiple_organizations', check_expiration=False)
        is_change_possible = self.can_change(obj, None)
        if not is_change_possible:
            return False
        active_jobs = []
        active_jobs.extend([dict(type="job", id=o.id)
                            for o in Job.objects.filter(project__in=obj.projects.all(), status__in=ACTIVE_STATES)])
        active_jobs.extend([dict(type="project_update", id=o.id)
                            for o in ProjectUpdate.objects.filter(project__in=obj.projects.all(), status__in=ACTIVE_STATES)])
        active_jobs.extend([dict(type="inventory_update", id=o.id)
                            for o in InventoryUpdate.objects.filter(inventory_source__inventory__organization=obj, status__in=ACTIVE_STATES)])
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True

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
        qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by', 'organization').all()

    @check_superuser
    def can_read(self, obj):
        return self.user in obj.read_role

    @check_superuser
    def can_use(self, obj):
        return self.user in obj.use_role

    @check_superuser
    def can_add(self, data):
        # If no data is specified, just checking for generic add permission?
        if not data:
            return Organization.accessible_objects(self.user, 'admin_role').exists()

        return self.check_related('organization', Organization, data)

    @check_superuser
    def can_change(self, obj, data):
        return self.can_admin(obj, data)

    @check_superuser
    def can_admin(self, obj, data):
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.
        if not self.check_related('organization', Organization, data, obj=obj):
            return False
        # Otherwise, just check for admin permission.
        return self.user in obj.admin_role

    def can_delete(self, obj):
        is_can_admin = self.can_admin(obj, None)
        if not is_can_admin:
            return False
        active_jobs = []
        active_jobs.extend([dict(type="job", id=o.id)
                           for o in Job.objects.filter(inventory=obj, status__in=ACTIVE_STATES)])
        active_jobs.extend([dict(type="inventory_update", id=o.id)
                            for o in InventoryUpdate.objects.filter(inventory_source__inventory=obj, status__in=ACTIVE_STATES)])
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True

    def can_run_ad_hoc_commands(self, obj):
        return self.user in obj.adhoc_role

class HostAccess(BaseAccess):
    '''
    I can see hosts whenever I can see their inventory.
    I can change or delete hosts whenver I can change their inventory.
    '''

    model = Host

    def get_queryset(self):
        inv_qs = Inventory.accessible_objects(self.user, 'read_role')
        qs = self.model.objects.filter(inventory__in=inv_qs)
        qs = qs.select_related('created_by', 'modified_by', 'inventory',
                               'last_job__job_template',
                               'last_job_host_summary__job')
        qs =qs.prefetch_related('groups').all()
        return qs

    def can_read(self, obj):
        return obj and self.user in obj.inventory.read_role

    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Inventory.accessible_objects(self.user, 'admin_role').exists()

        # Checks for admin or change permission on inventory.
        if not self.check_related('inventory', Inventory, data):
            return False

        # Check to see if we have enough licenses
        self.check_license(add_host=True)
        return True

    def can_change(self, obj, data):
        # Prevent moving a host to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied(_('Unable to change inventory on a host.'))
        # Checks for admin or change permission on inventory, controls whether
        # the user can edit variable data.
        return obj and self.user in obj.inventory.admin_role

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if not super(HostAccess, self).can_attach(obj, sub_obj, relationship,
                                                  data, skip_sub_obj_read_check):
            return False
        # Prevent assignments between different inventories.
        if obj.inventory != sub_obj.inventory:
            raise ParseError(_('Cannot associate two items from different inventories.'))
        return True

    def can_delete(self, obj):
        return obj and self.user in obj.inventory.admin_role

class GroupAccess(BaseAccess):
    '''
    I can see groups whenever I can see their inventory.
    I can change or delete groups whenever I can change their inventory.
    '''

    model = Group

    def get_queryset(self):
        qs = Group.objects.filter(inventory__in=Inventory.accessible_objects(self.user, 'read_role'))
        qs = qs.select_related('created_by', 'modified_by', 'inventory')
        return qs.prefetch_related('parents', 'children', 'inventory_source').all()

    def can_read(self, obj):
        return obj and self.user in obj.inventory.read_role

    def can_add(self, data):
        if not data or 'inventory' not in data:
            return False
        # Checks for admin or change permission on inventory.
        return self.check_related('inventory', Inventory, data)

    def can_change(self, obj, data):
        # Prevent moving a group to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied(_('Unable to change inventory on a group.'))
        # Checks for admin or change permission on inventory, controls whether
        # the user can attach subgroups or edit variable data.
        return obj and self.user in obj.inventory.admin_role

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if not super(GroupAccess, self).can_attach(obj, sub_obj, relationship,
                                                   data, skip_sub_obj_read_check):
            return False
        # Prevent assignments between different inventories.
        if obj.inventory != sub_obj.inventory:
            raise ParseError(_('Cannot associate two items from different inventories.'))
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
        is_delete_allowed = bool(obj and self.user in obj.inventory.admin_role)
        if not is_delete_allowed:
            return False
        active_jobs = []
        active_jobs.extend([dict(type="inventory_update", id=o.id)
                            for o in InventoryUpdate.objects.filter(inventory_source__in=obj.inventory_sources.all(), status__in=ACTIVE_STATES)])
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True

    def can_start(self, obj, validate_license=True):
        # Used as another alias to inventory_source start access for user_capabilities
        if obj and obj.inventory_source:
            return self.user.can_access(InventorySource, 'start', obj.inventory_source, validate_license=validate_license)
        return False

class InventorySourceAccess(BaseAccess):
    '''
    I can see inventory sources whenever I can see their group or inventory.
    I can change inventory sources whenever I can change their group.
    '''

    model = InventorySource

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = qs.select_related('created_by', 'modified_by', 'group', 'inventory')
        inventory_ids = self.user.get_queryset(Inventory)
        return qs.filter(Q(inventory_id__in=inventory_ids) |
                         Q(group__inventory_id__in=inventory_ids))

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

    def can_start(self, obj, validate_license=True):
        if obj and obj.group:
            return obj.can_update and self.user in obj.group.inventory.update_role
        elif obj and obj.inventory:
            return obj.can_update and self.user in obj.inventory.update_role
        return False


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
        if not obj.can_cancel:
            return False
        if self.user.is_superuser or self.user == obj.created_by:
            return True
        # Inventory cascade deletes to inventory update, descends from org admin
        return self.user in obj.inventory_source.inventory.admin_role

    def can_start(self, obj, validate_license=True):
        # For relaunching
        if obj and obj.inventory_source:
            access = InventorySourceAccess(self.user)
            return access.can_start(obj.inventory_source, validate_license=validate_license)
        return False

    @check_superuser
    def can_delete(self, obj):
        return self.user in obj.inventory_source.inventory.admin_role

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
        qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by').all()

    @check_superuser
    def can_read(self, obj):
        return self.user in obj.read_role

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        user_pk = get_pk_from_dict(data, 'user')
        if user_pk:
            user_obj = get_object_or_400(User, pk=user_pk)
            return check_user_access(self.user, User, 'change', user_obj, None)
        team_pk = get_pk_from_dict(data, 'team')
        if team_pk:
            team_obj = get_object_or_400(Team, pk=team_pk)
            return check_user_access(self.user, Team, 'change', team_obj, None)
        organization_pk = get_pk_from_dict(data, 'organization')
        if organization_pk:
            organization_obj = get_object_or_400(Organization, pk=organization_pk)
            return check_user_access(self.user, Organization, 'change', organization_obj, None)
        return False

    @check_superuser
    def can_use(self, obj):
        return self.user in obj.use_role

    @check_superuser
    def can_change(self, obj, data):
        if not obj:
            return False

        # Cannot change the organization for a credential after it's been created
        if data and 'organization' in data:
            organization_pk = get_pk_from_dict(data, 'organization')
            if (organization_pk and (not obj.organization or organization_pk != obj.organization.id)) \
                    or (not organization_pk and obj.organization):
                return False

        return self.user in obj.admin_role

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
     - I'm an admin of the team
     - I'm a member of that team.
    I can create/change a team when:
     - I'm a superuser.
     - I'm an admin for the team
    '''

    model = Team

    def get_queryset(self):
        qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by', 'organization').all()

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data)

    def can_change(self, obj, data):
        # Prevent moving a team to a different organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            raise PermissionDenied(_('Unable to change organization on a team.'))
        if self.user.is_superuser:
            return True
        return self.user in obj.admin_role

    def can_delete(self, obj):
        return self.can_change(obj, None)

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        """Reverse obj and sub_obj, defer to RoleAccess if this is an assignment
        of a resource role to the team."""
        if isinstance(sub_obj, Role):
            if sub_obj.content_object is None:
                raise PermissionDenied(_("The {} role cannot be assigned to a team").format(sub_obj.name))
            elif isinstance(sub_obj.content_object, User):
                raise PermissionDenied(_("The admin_role for a User cannot be assigned to a team"))

            if isinstance(sub_obj.content_object, ResourceMixin):
                role_access = RoleAccess(self.user)
                return role_access.can_attach(sub_obj, obj, 'member_role.parents',
                                              *args, **kwargs)
        return super(TeamAccess, self).can_attach(obj, sub_obj, relationship,
                                                  *args, **kwargs)

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        if isinstance(sub_obj, Role):
            if isinstance(sub_obj.content_object, ResourceMixin):
                role_access = RoleAccess(self.user)
                return role_access.can_unattach(sub_obj, obj, 'member_role.parents',
                                                *args, **kwargs)
        return super(TeamAccess, self).can_unattach(obj, sub_obj, relationship,
                                                    *args, **kwargs)

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
        if self.user.is_superuser or self.user.is_system_auditor:
            return self.model.objects.all()
        qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('modified_by', 'credential', 'current_job', 'last_job').all()

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data, mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if not self.check_related('organization', Organization, data):
            return False
        return self.user in obj.admin_role

    def can_delete(self, obj):
        is_change_allowed = self.can_change(obj, None)
        if not is_change_allowed:
            return False
        active_jobs = []
        active_jobs.extend([dict(type="job", id=o.id)
                            for o in Job.objects.filter(project=obj, status__in=ACTIVE_STATES)])
        active_jobs.extend([dict(type="project_update", id=o.id)
                            for o in ProjectUpdate.objects.filter(project=obj, status__in=ACTIVE_STATES)])
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True

    @check_superuser
    def can_start(self, obj, validate_license=True):
        return obj and self.user in obj.update_role

class ProjectUpdateAccess(BaseAccess):
    '''
    I can see project updates when I can see the project.
    I can change when I can change the project.
    I can delete when I can change/delete the project.
    '''

    model = ProjectUpdate

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            return self.model.objects.all()
        qs = ProjectUpdate.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'project')
        project_ids = set(self.user.get_queryset(Project).values_list('id', flat=True))
        return qs.filter(project_id__in=project_ids)

    @check_superuser
    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        if self.user == obj.created_by:
            return True
        # Project updates cascade delete with project, admin role descends from org admin
        return self.user in obj.project.admin_role

    def can_start(self, obj, validate_license=True):
        # for relaunching
        if obj and obj.project:
            return self.user in obj.project.update_role
        return False

    @check_superuser
    def can_delete(self, obj):
        return obj and self.user in obj.project.admin_role

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
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by', 'inventory', 'project',
                                 'credential', 'cloud_credential', 'next_schedule').all()

    @check_superuser
    def can_read(self, obj):
        return self.user in obj.read_role

    def can_add(self, data):
        '''
        a user can create a job template if they are a superuser, an org admin
        of any org that the project is a member, or if they have user or team
        based permissions tying the project to the inventory source for the
        given action as well as the 'create' deploy permission.
        Users who are able to create deploy jobs can also run normal and check (dry run) jobs.
        '''
        if not data:  # So the browseable API will work
            return (
                Project.accessible_objects(self.user, 'use_role').exists() or
                Inventory.accessible_objects(self.user, 'use_role').exists())

        # if reference_obj is provided, determine if it can be coppied
        reference_obj = data.get('reference_obj', None)

        if 'job_type' in data and data['job_type'] == PERM_INVENTORY_SCAN:
            self.check_license(feature='system_tracking')

        if 'survey_enabled' in data and data['survey_enabled']:
            self.check_license(feature='surveys')

        if self.user.is_superuser:
            return True

        def get_value(Class, field):
            if reference_obj:
                return getattr(reference_obj, field, None)
            else:
                pk = get_pk_from_dict(data, field)
                if pk:
                    return get_object_or_400(Class, pk=pk)
                else:
                    return None

        # If a credential is provided, the user should have use access to it.
        if not self.check_related('credential', Credential, data, role_field='use_role'):
            return False

        # If a cloud credential is provided, the user should have use access.
        if not self.check_related('cloud_credential', Credential, data, role_field='use_role'):
            return False

        # If a network credential is provided, the user should have use access.
        if not self.check_related('network_credential', Credential, data, role_field='use_role'):
            return False

        # If an inventory is provided, the user should have use access.
        inventory = get_value(Inventory, 'inventory')
        if inventory:
            if self.user not in inventory.use_role:
                return False

        project = get_value(Project, 'project')
        if 'job_type' in data and data['job_type'] == PERM_INVENTORY_SCAN:
            if inventory:
                accessible = self.user in inventory.use_role
            else:
                accessible = False
            if not project and accessible:
                return True
            elif not accessible:
                return False
        # If the user has admin access to the project (as an org admin), should
        # be able to proceed without additional checks.
        if project:
            return self.user in project.use_role
        else:
            return False

    def can_start(self, obj, validate_license=True):
        # Check license.
        if validate_license:
            self.check_license()
            if obj.job_type == PERM_INVENTORY_SCAN:
                self.check_license(feature='system_tracking')
            if obj.survey_enabled:
                self.check_license(feature='surveys')
            if Instance.objects.active_count() > 1:
                self.check_license(feature='ha')

        # Super users can start any job
        if self.user.is_superuser:
            return True

        if obj.job_type == PERM_INVENTORY_SCAN:
            # Scan job with default project, must have JT execute or be org admin
            if obj.project is None and obj.inventory:
                return (self.user in obj.execute_role or
                        self.user in obj.inventory.organization.admin_role)

        return self.user in obj.execute_role

    def can_change(self, obj, data):
        data_for_change = data
        if self.user not in obj.admin_role and not self.user.is_superuser:
            return False
        if data is not None:
            data = dict(data)

            if self.changes_are_non_sensitive(obj, data):
                if 'job_type' in data and obj.job_type != data['job_type'] and data['job_type'] == PERM_INVENTORY_SCAN:
                    self.check_license(feature='system_tracking')

                if 'survey_enabled' in data and obj.survey_enabled != data['survey_enabled'] and data['survey_enabled']:
                    self.check_license(feature='surveys')
                return True

            for required_field in ('credential', 'cloud_credential', 'network_credential', 'inventory', 'project'):
                required_obj = getattr(obj, required_field, None)
                if required_field not in data_for_change and required_obj is not None:
                    data_for_change[required_field] = required_obj.pk
        return self.can_read(obj) and (self.can_add(data_for_change) if data is not None else True)

    def changes_are_non_sensitive(self, obj, data):
        '''
        Return true if the changes being made are considered nonsensitive, and
        thus can be made by a job template administrator which may not have access
        to the any inventory, project, or credentials associated with the template.
        '''
        # We are white listing fields that can
        field_whitelist = [
            'name', 'description', 'forks', 'limit', 'verbosity', 'extra_vars',
            'job_tags', 'force_handlers', 'skip_tags', 'ask_variables_on_launch',
            'ask_tags_on_launch', 'ask_job_type_on_launch', 'ask_skip_tags_on_launch',
            'ask_inventory_on_launch', 'ask_credential_on_launch', 'survey_enabled',

            # These fields are ignored, but it is convenient for QA to allow clients to post them
            'last_job_run', 'created', 'modified',
        ]

        for k, v in data.items():
            if hasattr(obj, k) and getattr(obj, k) != v:
                if k not in field_whitelist and v != getattr(obj, '%s_id' % k, None) \
                        and not (hasattr(obj, '%s_id' % k) and getattr(obj, '%s_id' % k) is None and v == ''): # Equate '' to None in the case of foreign keys
                    return False
        return True

    def can_update_sensitive_fields(self, obj, data):
        project_id = data.get('project', obj.project.id if obj.project else None)
        inventory_id = data.get('inventory', obj.inventory.id if obj.inventory else None)
        credential_id = data.get('credential', obj.credential.id if obj.credential else None)
        cloud_credential_id = data.get('cloud_credential', obj.cloud_credential.id if obj.cloud_credential else None)
        network_credential_id = data.get('network_credential', obj.network_credential.id if obj.network_credential else None)

        if project_id and self.user not in Project.objects.get(pk=project_id).use_role:
            return False
        if inventory_id and self.user not in Inventory.objects.get(pk=inventory_id).use_role:
            return False
        if credential_id and self.user not in Credential.objects.get(pk=credential_id).use_role:
            return False
        if cloud_credential_id and self.user not in Credential.objects.get(pk=cloud_credential_id).use_role:
            return False
        if network_credential_id and self.user not in Credential.objects.get(pk=network_credential_id).use_role:
            return False

        return True

    def can_delete(self, obj):
        is_delete_allowed = self.user.is_superuser or self.user in obj.admin_role
        if not is_delete_allowed:
            return False
        active_jobs = [dict(type="job", id=o.id)
                       for o in obj.jobs.filter(status__in=ACTIVE_STATES)]
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True

class JobAccess(BaseAccess):
    '''
    I can see jobs when:
     - I am a superuser.
     - I can see its job template
     - I am an admin or auditor of the organization which contains its inventory
     - I am an admin or auditor of the organization which contains its project
    I can delete jobs when:
     - I am an admin of the organization which contains its inventory
     - I am an admin of the organization which contains its project
    '''

    model = Job

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'job_template', 'inventory',
                               'project', 'credential', 'cloud_credential', 'job_template')
        qs = qs.prefetch_related('unified_job_template')
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs.all()

        qs_jt = qs.filter(
            job_template__in=JobTemplate.accessible_objects(self.user, 'read_role')
        )

        org_access_qs = Organization.objects.filter(
            Q(admin_role__members=self.user) | Q(auditor_role__members=self.user))
        if not org_access_qs.exists():
            return qs_jt

        return qs.filter(
            Q(job_template__in=JobTemplate.accessible_objects(self.user, 'read_role')) |
            Q(inventory__organization__in=org_access_qs) |
            Q(project__organization__in=org_access_qs)).distinct()

    def related_orgs(self, obj):
        orgs = []
        if obj.inventory and obj.inventory.organization:
            orgs.append(obj.inventory.organization)
        if obj.project and obj.project.organization and obj.project.organization not in orgs:
            orgs.append(obj.project.organization)
        return orgs

    def org_access(self, obj, role_types=['admin_role']):
        orgs = self.related_orgs(obj)
        for org in orgs:
            for role_type in role_types:
                role = getattr(org, role_type)
                if self.user in role:
                    return True
        return False

    @check_superuser
    def can_read(self, obj):
        if obj.job_template and self.user in obj.job_template.read_role:
            return True
        return self.org_access(obj, role_types=['auditor_role', 'admin_role'])

    def can_add(self, data, validate_license=True):
        if validate_license:
            self.check_license()

        if not data:  # So the browseable API will work
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
        return (obj.status == 'new' and
                self.can_read(obj) and
                self.can_add(data, validate_license=False))

    @check_superuser
    def can_delete(self, obj):
        return self.org_access(obj)

    def can_start(self, obj, validate_license=True):
        if validate_license:
            self.check_license()

        # A super user can relaunch a job
        if self.user.is_superuser:
            return True

        inventory_access = obj.inventory and self.user in obj.inventory.use_role
        credential_access = obj.credential and self.user in obj.credential.use_role

        # Check if JT execute access (and related prompts) is sufficient
        if obj.job_template is not None:
            prompts_access = True
            job_fields = {}
            for fd in obj.job_template._ask_for_vars_dict():
                job_fields[fd] = getattr(obj, fd)
            accepted_fields, ignored_fields = obj.job_template._accept_or_ignore_job_kwargs(**job_fields)
            for fd in ignored_fields:
                if fd != 'extra_vars' and job_fields[fd] != getattr(obj.job_template, fd):
                    # Job has field that is not promptable
                    prompts_access = False
            if obj.credential != obj.job_template.credential and not credential_access:
                prompts_access = False
            if obj.inventory != obj.job_template.inventory and not inventory_access:
                prompts_access = False
            if prompts_access and self.user in obj.job_template.execute_role:
                return True


        org_access = obj.inventory and self.user in obj.inventory.organization.admin_role
        project_access = obj.project is None or self.user in obj.project.admin_role

        # job can be relaunched if user could make an equivalent JT
        return inventory_access and credential_access and (org_access or project_access)

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        # Delete access allows org admins to stop running jobs
        if self.user == obj.created_by or self.can_delete(obj):
            return True
        return obj.job_template is not None and self.user in obj.job_template.admin_role

class SystemJobTemplateAccess(BaseAccess):
    '''
    I can only see/manage System Job Templates if I'm a super user
    '''

    model = SystemJobTemplate

    def can_start(self, obj, validate_license=True):
        return self.can_read(obj)

class SystemJobAccess(BaseAccess):
    '''
    I can only see manage System Jobs if I'm a super user
    '''
    model = SystemJob

    def can_start(self, obj, validate_license=True):
        return False # no relaunching of system jobs

# TODO:
class WorkflowJobTemplateNodeAccess(BaseAccess):
    '''
    I can see/use a WorkflowJobTemplateNode if I have read permission
        to associated Workflow Job Template

    In order to add a node, I need:
     - admin access to parent WFJT
     - execute access to the unified job template being used
     - access to any credential or inventory provided as the prompted fields

    In order to do anything to a node, I need admin access to its WFJT

    In order to edit fields on a node, I need:
     - execute access to the unified job template of the node
     - access to BOTH credential and inventory post-change, if present

    In order to delete a node, I only need the admin access its WFJT

    In order to manage connections (edges) between nodes I do not need anything
      beyond the standard admin access to its WFJT
    '''
    model = WorkflowJobTemplateNode

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.filter(
                workflow_job_template__in=WorkflowJobTemplate.accessible_objects(
                    self.user, 'read_role'))
        qs = qs.prefetch_related('success_nodes', 'failure_nodes', 'always_nodes')
        return qs

    def can_use_prompted_resources(self, data):
        if not self.check_related('credential', Credential, data):
            return False
        if not self.check_related('inventory', Inventory, data):
            return False
        return True

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        if not self.check_related('workflow_job_template', WorkflowJobTemplate, data, mandatory=True):
            return False
        if not self.can_use_prompted_resources(data):
            return False
        return True

    def wfjt_admin(self, obj):
        if not obj.workflow_job_template:
            return self.user.is_superuser
        else:
            return self.user in obj.workflow_job_template.admin_role

    def ujt_execute(self, obj):
        if not obj.unified_job_template:
            return self.wfjt_admin(obj)
        else:
            return self.user in obj.unified_job_template.execute_role and self.wfjt_admin(obj)

    def can_change(self, obj, data):
        if not data:
            return True

        if not self.ujt_execute(obj):
            # should not be able to edit the prompts if lacking access to UJT
            return False

        if 'credential' in data or 'inventory' in data:
            new_data = data
            if 'credential' not in data:
                new_data['credential'] = self.credential
            if 'inventory' not in data:
                new_data['inventory'] = self.inventory
            return self.can_use_prompted_resources(new_data)
        return True

    def can_delete(self, obj):
        return self.wfjt_admin(obj)

    def check_same_WFJT(self, obj, sub_obj):
        if type(obj) != self.model or type(sub_obj) != self.model:
            raise Exception('Attaching workflow nodes only allowed for other nodes')
        if obj.workflow_job_template != sub_obj.workflow_job_template:
            return False
        return True

    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        return self.wfjt_admin(obj) and self.check_same_WFJT(obj, sub_obj)

    def can_unattach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        return self.wfjt_admin(obj) and self.check_same_WFJT(obj, sub_obj)

class WorkflowJobNodeAccess(BaseAccess):
    '''
    I can see a WorkflowJobNode if I have permission to...
    the workflow job template associated with...
    the workflow job associated with the node.

    Any deletion of editing of individual nodes would undermine the integrity
    of the graph structure.
    Deletion must happen as a cascade delete from the workflow job.
    '''
    model = WorkflowJobNode

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.filter(
                workflow_job__workflow_job_template__in=WorkflowJobTemplate.accessible_objects(
                    self.user, 'read_role'))
        qs = qs.select_related('unified_job_template', 'job')
        qs = qs.prefetch_related('success_nodes', 'failure_nodes', 'always_nodes')
        return qs

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

# TODO: revisit for survey logic, notification attachments?
class WorkflowJobTemplateAccess(BaseAccess):
    '''
    I can only see/manage Workflow Job Templates if I'm a super user
    '''

    model = WorkflowJobTemplate

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = self.model.accessible_objects(self.user, 'read_role')
        return qs.select_related('created_by', 'modified_by', 'next_schedule',
                                 'admin_role', 'execute_role', 'read_role').all()

    @check_superuser
    def can_read(self, obj):
        return self.user in obj.read_role

    @check_superuser
    def can_add(self, data):
        '''
        a user can create a job template if they are a superuser, an org admin
        of any org that the project is a member, or if they have user or team
        based permissions tying the project to the inventory source for the
        given action as well as the 'create' deploy permission.
        Users who are able to create deploy jobs can also run normal and check (dry run) jobs.
        '''
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()

        # if reference_obj is provided, determine if it can be coppied
        reference_obj = data.pop('reference_obj', None)
        if reference_obj:
            for node in reference_obj.workflow_job_template_nodes.all():
                if node.inventory and self.user not in node.inventory.use_role:
                    return False
                if node.credential and self.user not in node.credential.use_role:
                    return False
                if node.unified_job_template:
                    if isinstance(node.unified_job_template, SystemJobTemplate):
                        if not self.user.is_superuser:
                            return False
                    elif isinstance(node.unified_job_template, JobTemplate):
                        if self.user not in node.unified_job_template.execute_role:
                            return False
                    elif isinstance(node.unified_job_template, Project):
                        if self.user not in node.unified_job_template.update_role:
                            return False
                    elif isinstance(node.unified_job_template, InventorySource):
                        if not self.user.can_access(InventorySource, 'start', node.unified_job_template):
                            return False
                    else:
                        return False
            return True

        # will check this if surveys are added to WFJT
        # if 'survey_enabled' in data and data['survey_enabled']:
        #     self.check_license(feature='surveys')

        return self.check_related('organization', Organization, data)

    def can_start(self, obj, validate_license=True):
        if validate_license:
            # check basic license, node count
            self.check_license()
            # if surveys are added to WFJTs, check license here
            # if obj.survey_enabled:
            #     self.check_license(feature='surveys')

        # Super users can start any job
        if self.user.is_superuser:
            return True

        return self.user in obj.execute_role

    def can_change(self, obj, data):
        # # Check survey license if surveys are added to WFJTs
        # if 'survey_enabled' in data and obj.survey_enabled != data['survey_enabled'] and data['survey_enabled']:
        #     self.check_license(feature='surveys')

        if self.user.is_superuser:
            return True

        return self.check_related('organization', Organization, data, obj=obj) and self.user in obj.admin_role

    def can_delete(self, obj):
        is_delete_allowed = self.user.is_superuser or self.user in obj.admin_role
        if not is_delete_allowed:
            return False
        active_jobs = [dict(type="job", id=o.id)
                       for o in obj.jobs.filter(status__in=ACTIVE_STATES)]
        if len(active_jobs) > 0:
            raise StateConflict({"conflict": _("Resource is being used by running jobs"),
                                 "active_jobs": active_jobs})
        return True


class WorkflowJobAccess(BaseAccess):
    '''
    I can only see Workflow Jobs if I can see the associated
    workflow job template that it was created from.
    I can delete them if I am admin of their workflow job template
    I can cancel one if I can delete it
       I can also cancel it if I started it
    '''
    model = WorkflowJob

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = WorkflowJob.objects.filter(
                workflow_job_template__in=WorkflowJobTemplate.accessible_objects(
                    self.user, 'read_role'))
        return qs.select_related('created_by', 'modified_by')

    def can_add(self, data):
        # Old add-start system for launching jobs is being depreciated, and
        # not supported for new types of resources
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        if obj.workflow_job_template is None:
            # only superusers can delete orphaned workflow jobs
            return self.user.is_superuser
        return self.user in obj.workflow_job_template.admin_role

    # TODO: add support for relaunching workflow jobs
    def can_start(self, obj, validate_license=True):
        return False

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        return self.can_delete(obj) or self.user == obj.created_by

class AdHocCommandAccess(BaseAccess):
    '''
    I can only see/run ad hoc commands when:
    - I am a superuser.
    - I have read access to the inventory
    '''
    model = AdHocCommand

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('created_by', 'modified_by', 'inventory',
                               'credential')
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs.all()

        inventory_qs = Inventory.accessible_objects(self.user, 'read_role')
        return qs.filter(inventory__in=inventory_qs)

    def can_add(self, data, validate_license=True):
        if not data:  # So the browseable API will work
            return True

        if validate_license:
            self.check_license()

        # If a credential is provided, the user should have use access to it.
        if not self.check_related('credential', Credential, data, role_field='use_role'):
            return False

        # Check that the user has the run ad hoc command permission on the
        # given inventory.
        if not self.check_related('inventory', Inventory, data, role_field='adhoc_role'):
            return False

        return True

    def can_change(self, obj, data):
        return False

    @check_superuser
    def can_delete(self, obj):
        return obj.inventory is not None and self.user in obj.inventory.organization.admin_role

    def can_start(self, obj, validate_license=True):
        return self.can_add({
            'credential': obj.credential_id,
            'inventory': obj.inventory_id,
        }, validate_license=validate_license)

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        if self.user == obj.created_by:
            return True
        return obj.inventory is not None and self.user in obj.inventory.admin_role

class AdHocCommandEventAccess(BaseAccess):
    '''
    I can see ad hoc command event records whenever I can read both ad hoc
    command and host.
    '''

    model = AdHocCommandEvent

    def get_queryset(self):
        qs = self.model.objects.distinct()
        qs = qs.select_related('ad_hoc_command', 'host')

        if self.user.is_superuser or self.user.is_system_auditor:
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
        if self.user.is_superuser or self.user.is_system_auditor:
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
        qs = self.model.objects.all()
        qs = qs.select_related('job', 'job__job_template', 'host', 'parent')
        qs = qs.prefetch_related('hosts', 'children')

        # Filter certain "internal" events generated by async polling.
        qs = qs.exclude(event__in=('runner_on_ok', 'runner_on_failed'),
                        event_data__icontains='"ansible_job_id": "',
                        event_data__contains='"module_name": "async_status"')

        if self.user.is_superuser or self.user.is_system_auditor:
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
        qs = self.model.objects.all()
        project_qs = self.user.get_queryset(Project).filter(scm_type__in=[s[0] for s in Project.SCM_TYPE_CHOICES])
        inventory_source_qs = self.user.get_queryset(InventorySource).filter(source__in=CLOUD_INVENTORY_SOURCES)
        job_template_qs = self.user.get_queryset(JobTemplate)
        system_job_template_qs = self.user.get_queryset(SystemJobTemplate)
        workflow_job_template_qs = self.user.get_queryset(WorkflowJobTemplate)
        qs = qs.filter(Q(Project___in=project_qs) |
                       Q(InventorySource___in=inventory_source_qs) |
                       Q(JobTemplate___in=job_template_qs) |
                       Q(systemjobtemplate__in=system_job_template_qs) |
                       Q(workflowjobtemplate__in=workflow_job_template_qs))
        qs = qs.select_related(
            'created_by',
            'modified_by',
            'next_schedule',
            'last_job',
            'current_job',
        )

        # WISH - sure would be nice if the following worked, but it does not.
        # In the future, as django and polymorphic libs are upgraded, try again.

        #qs = qs.prefetch_related(
        #    'project',
        #    'inventory',
        #    'credential',
        #    'cloud_credential',
        #)

        return qs.all()

class UnifiedJobAccess(BaseAccess):
    '''
    I can see a unified job whenever I can see the same project update,
    inventory update or job.
    '''

    model = UnifiedJob

    def get_queryset(self):
        qs = self.model.objects.all()
        project_update_qs = self.user.get_queryset(ProjectUpdate)
        inventory_update_qs = self.user.get_queryset(InventoryUpdate).filter(source__in=CLOUD_INVENTORY_SOURCES)
        job_qs = self.user.get_queryset(Job)
        ad_hoc_command_qs = self.user.get_queryset(AdHocCommand)
        system_job_qs = self.user.get_queryset(SystemJob)
        workflow_job_qs = self.user.get_queryset(WorkflowJob)
        qs = qs.filter(Q(ProjectUpdate___in=project_update_qs) |
                       Q(InventoryUpdate___in=inventory_update_qs) |
                       Q(Job___in=job_qs) |
                       Q(AdHocCommand___in=ad_hoc_command_qs) |
                       Q(SystemJob___in=system_job_qs) |
                       Q(WorkflowJob___in=workflow_job_qs))
        qs = qs.select_related(
            'created_by',
            'modified_by',
        )
        qs = qs.prefetch_related(
            'unified_job_template',
        )

        # WISH - sure would be nice if the following worked, but it does not.
        # In the future, as django and polymorphic libs are upgraded, try again.

        #qs = qs.prefetch_related(
        #    'project',
        #    'inventory',
        #    'credential',
        #    'job_template',
        #    'inventory_source',
        #    'cloud_credential',
        #    'project___credential',
        #    'inventory_source___credential',
        #    'inventory_source___inventory',
        #    'job_template__inventory',
        #    'job_template__project',
        #    'job_template__credential',
        #    'job_template__cloud_credential',
        #)
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
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs.all()
        job_template_qs = self.user.get_queryset(JobTemplate)
        inventory_source_qs = self.user.get_queryset(InventorySource)
        project_qs = self.user.get_queryset(Project)
        unified_qs = UnifiedJobTemplate.objects.filter(jobtemplate__in=job_template_qs) | \
            UnifiedJobTemplate.objects.filter(Q(project__in=project_qs)) | \
            UnifiedJobTemplate.objects.filter(Q(inventorysource__in=inventory_source_qs))
        return qs.filter(unified_job_template__in=unified_qs)

    @check_superuser
    def can_read(self, obj):
        if obj and obj.unified_job_template:
            job_class = obj.unified_job_template
            return self.user.can_access(type(job_class), 'read', obj.unified_job_template)
        else:
            return False

    @check_superuser
    def can_add(self, data):
        return self.check_related('unified_job_template', UnifiedJobTemplate, data, mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        return self.check_related('unified_job_template', UnifiedJobTemplate, data, obj=obj, mandatory=True)

    def can_delete(self, obj):
        return self.can_change(obj, {})

class NotificationTemplateAccess(BaseAccess):
    '''
    I can see/use a notification_template if I have permission to
    '''
    model = NotificationTemplate

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs
        return self.model.objects.filter(
            Q(organization__in=self.user.admin_of_organizations) |
            Q(organization__in=self.user.auditor_of_organizations)
        ).distinct()

    def can_read(self, obj):
        if self.user.is_superuser or self.user.is_system_auditor:
            return True
        if obj.organization is not None:
            if self.user in obj.organization.admin_role or self.user in obj.organization.auditor_role:
                return True
        return False

    @check_superuser
    def can_add(self, data):
        if not data:
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data, mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if obj.organization is None:
            # only superusers are allowed to edit orphan notification templates
            return False
        return self.check_related('organization', Organization, data, obj=obj, mandatory=True)

    def can_admin(self, obj, data):
        return self.can_change(obj, data)

    def can_delete(self, obj):
        return self.can_change(obj, None)

    @check_superuser
    def can_start(self, obj, validate_license=True):
        if obj.organization is None:
            return False
        return self.user in obj.organization.admin_role

class NotificationAccess(BaseAccess):
    '''
    I can see/use a notification if I have permission to
    '''
    model = Notification

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs
        return self.model.objects.filter(
            Q(notification_template__organization__in=self.user.admin_of_organizations) |
            Q(notification_template__organization__in=self.user.auditor_of_organizations)
        ).distinct()

    def can_read(self, obj):
        return self.user.can_access(NotificationTemplate, 'read', obj.notification_template)

    def can_delete(self, obj):
        return self.user.can_access(NotificationTemplate, 'delete', obj.notification_template)

class LabelAccess(BaseAccess):
    '''
    I can see/use a Label if I have permission to associated organization
    '''
    model = Label

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            return self.model.objects.all()
        return self.model.objects.filter(
            organization__in=Organization.accessible_objects(self.user, 'read_role')
        )

    @check_superuser
    def can_read(self, obj):
        return self.user in obj.organization.read_role

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        return self.check_related('organization', Organization, data, role_field='member_role', mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if self.can_add(data) is False:
            return False
        return self.check_related('organization', Organization, data, obj=obj, mandatory=True)

    def can_delete(self, obj):
        return self.can_change(obj, None)

class ActivityStreamAccess(BaseAccess):
    '''
    I can see activity stream events only when I have permission on all objects included in the event
    '''

    model = ActivityStream

    def get_queryset(self):
        '''
        The full set is returned if the user is:
         - System Administrator
         - System Auditor
        These users will be able to see orphaned activity stream items
        (the related resource has been deleted), as well as the other
        obscure cases listed here

        Complex permissions omitted from the activity stream of a normal user:
         - host access via group
         - permissions (from prior versions)
         - notifications via team admin access

        Activity stream events that have been omitted from list for
        normal users since 2.4:
         - unified job templates
         - unified jobs
         - schedules
         - custom inventory scripts
        '''
        qs = self.model.objects.all()
        qs = qs.select_related('actor')
        qs = qs.prefetch_related('organization', 'user', 'inventory', 'host', 'group', 'inventory_source',
                                 'inventory_update', 'credential', 'team', 'project', 'project_update',
                                 'permission', 'job_template', 'job', 'ad_hoc_command',
                                 'notification_template', 'notification', 'label', 'role')
        if self.user.is_superuser or self.user.is_system_auditor:
            return qs.all()

        inventory_set = Inventory.accessible_objects(self.user, 'read_role')
        credential_set = Credential.accessible_objects(self.user, 'read_role')
        auditing_orgs = (
            Organization.accessible_objects(self.user, 'admin_role') |
            Organization.accessible_objects(self.user, 'auditor_role')
        ).distinct().values_list('id', flat=True)
        project_set = Project.accessible_objects(self.user, 'read_role')
        jt_set = JobTemplate.accessible_objects(self.user, 'read_role')
        team_set = Team.accessible_objects(self.user, 'read_role')

        return qs.filter(
            Q(ad_hoc_command__inventory__in=inventory_set) |
            Q(user__in=auditing_orgs.values('member_role__members')) |
            Q(user=self.user) |
            Q(organization__in=auditing_orgs) |
            Q(inventory__in=inventory_set) |
            Q(host__inventory__in=inventory_set) |
            Q(group__inventory__in=inventory_set) |
            Q(inventory_source__inventory__in=inventory_set) |
            Q(inventory_update__inventory_source__inventory__in=inventory_set) |
            Q(credential__in=credential_set) |
            Q(team__in=team_set) |
            Q(project__in=project_set) |
            Q(project_update__project__in=project_set) |
            Q(job_template__in=jt_set) |
            Q(job__job_template__in=jt_set) |
            Q(notification_template__organization__in=auditing_orgs) |
            Q(notification__notification_template__organization__in=auditing_orgs) |
            Q(label__organization__in=auditing_orgs) |
            Q(role__in=Role.visible_roles(self.user) if auditing_orgs else [])
        ).distinct()

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False

class CustomInventoryScriptAccess(BaseAccess):

    model = CustomInventoryScript

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            return self.model.objects.distinct().all()
        return self.model.accessible_objects(self.user, 'read_role').all()

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data)

    @check_superuser
    def can_admin(self, obj, data=None):
        return self.check_related('organization', Organization, data, obj=obj)

    @check_superuser
    def can_change(self, obj, data):
        return self.can_admin(obj, data=data)

    @check_superuser
    def can_delete(self, obj):
        return self.can_admin(obj)

class RoleAccess(BaseAccess):
    '''
    - I can see roles when
      - I am a super user
      - I am a member of that role
      - The role is a descdendent role of a role I am a member of
      - The role is an implicit role of an object that I can see a role of.
    '''

    model = Role

    def can_read(self, obj):
        if not obj:
            return False
        if self.user.is_superuser or self.user.is_system_auditor:
            return True

        return Role.filter_visible_roles(
            self.user, Role.objects.filter(pk=obj.id)).exists()

    def can_add(self, obj, data):
        # Unsupported for now
        return False

    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        return self.can_unattach(obj, sub_obj, relationship, data, skip_sub_obj_read_check)

    @check_superuser
    def can_unattach(self, obj, sub_obj, relationship, data=None, skip_sub_obj_read_check=False):
        if not skip_sub_obj_read_check and relationship in ['members', 'member_role.parents', 'parents']:
            # If we are unattaching a team Role, check the Team read access
            if relationship == 'parents':
                sub_obj_resource = sub_obj.content_object
            else:
                sub_obj_resource = sub_obj
            if not check_user_access(self.user, sub_obj_resource.__class__, 'read', sub_obj_resource):
                return False

        if isinstance(obj.content_object, ResourceMixin) and \
           self.user in obj.content_object.admin_role:
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
register_access(Role, RoleAccess)
register_access(NotificationTemplate, NotificationTemplateAccess)
register_access(Notification, NotificationAccess)
register_access(Label, LabelAccess)
register_access(WorkflowJobTemplateNode, WorkflowJobTemplateNodeAccess)
register_access(WorkflowJobNode, WorkflowJobNodeAccess)
register_access(WorkflowJobTemplate, WorkflowJobTemplateAccess)
register_access(WorkflowJob, WorkflowJobAccess)
