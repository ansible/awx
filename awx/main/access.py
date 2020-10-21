# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
import sys
import logging
from functools import reduce

# Django
from django.conf import settings
from django.db.models import Q, Prefetch
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied

# Django OAuth Toolkit
from awx.main.models.oauth import OAuth2Application, OAuth2AccessToken

# AWX
from awx.main.utils import (
    get_object_or_400,
    get_pk_from_dict,
    to_python_boolean,
    get_licenser,
)
from awx.main.models import (
    ActivityStream, AdHocCommand, AdHocCommandEvent, Credential, CredentialType,
    CredentialInputSource, CustomInventoryScript, Group, Host, Instance, InstanceGroup,
    Inventory, InventorySource, InventoryUpdate, InventoryUpdateEvent, Job, JobEvent,
    JobHostSummary, JobLaunchConfig, JobTemplate, Label, Notification,
    NotificationTemplate, Organization, Project, ProjectUpdate,
    ProjectUpdateEvent, Role, Schedule, SystemJob, SystemJobEvent,
    SystemJobTemplate, Team, UnifiedJob, UnifiedJobTemplate, WorkflowJob,
    WorkflowJobNode, WorkflowJobTemplate, WorkflowJobTemplateNode,
    WorkflowApproval, WorkflowApprovalTemplate,
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR, ROLE_SINGLETON_SYSTEM_AUDITOR
)
from awx.main.models.mixins import ResourceMixin

__all__ = ['get_user_queryset', 'check_user_access', 'check_user_access_with_errors',
           'user_accessible_objects', 'consumer_access',]

logger = logging.getLogger('awx.main.access')

access_registry = {
    # <model_class>: <access_class>,
    # ...
}


def get_object_from_data(field, Model, data, obj=None):
    """
    Utility method to obtain related object in data according to fallbacks:
     - if data contains key with pointer to Django object, return that
     - if contains integer, get object from database
     - if this does not work, raise exception
    """
    try:
        raw_value = data[field]
    except KeyError:
        # Calling method needs to deal with non-existence of key
        raise ParseError(_("Required related field %s for permission check." % field))

    try:
        if isinstance(raw_value, Model):
            return raw_value
        elif raw_value is None:
            return None
        else:
            new_pk = int(raw_value)
            # Avoid database query by comparing pk to model for similarity
            if obj and new_pk == getattr(obj, '%s_id' % field, None):
                return getattr(obj, field)
            else:
                # Get the new resource from the database
                return get_object_or_400(Model, pk=new_pk)
    except (TypeError, ValueError):
        raise ParseError(_("Bad data found in related field %s." % field))


def vars_are_encrypted(vars):
    '''Returns True if any of the values in the dictionary vars contains
    content which is encrypted by the AWX encryption algorithm
    '''
    for value in vars.values():
        if isinstance(value, str):
            if value.startswith('$encrypted$'):
                return True
    return False


def register_access(model_class, access_class):
    access_registry[model_class] = access_class


def user_accessible_objects(user, role_name):
    return ResourceMixin._accessible_objects(User, user, role_name)


def get_user_queryset(user, model_class):
    '''
    Return a queryset for the given model_class containing only the instances
    that should be visible to the given user.
    '''
    access_class = access_registry[model_class]
    access_instance = access_class(user)
    return access_instance.get_queryset()


def check_user_access(user, model_class, action, *args, **kwargs):
    '''
    Return True if user can perform action against model_class with the
    provided parameters.
    '''
    access_class = access_registry[model_class]
    access_instance = access_class(user)
    access_method = getattr(access_instance, 'can_%s' % action)
    result = access_method(*args, **kwargs)
    logger.debug('%s.%s %r returned %r', access_instance.__class__.__name__,
                 getattr(access_method, '__name__', 'unknown'), args, result)
    return result


def check_user_access_with_errors(user, model_class, action, *args, **kwargs):
    '''
    Return T/F permission and summary of problems with the action.
    '''
    access_class = access_registry[model_class]
    access_instance = access_class(user, save_messages=True)
    access_method = getattr(access_instance, 'can_%s' % action, None)
    result = access_method(*args, **kwargs)
    logger.debug('%s.%s %r returned %r', access_instance.__class__.__name__,
                 access_method.__name__, args, result)
    return (result, access_instance.messages)


def get_user_capabilities(user, instance, **kwargs):
    '''
    Returns a dictionary of capabilities the user has on the particular
    instance.  *NOTE* This is not a direct mapping of can_* methods into this
    dictionary, it is intended to munge some queries in a way that is
    convenient for the user interface to consume and hide or show various
    actions in the interface.
    '''
    access_class = access_registry[instance.__class__]
    return access_class(user).get_user_capabilities(instance, **kwargs)


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


def consumer_access(group_name):
    '''
    consumer_access returns the proper Access class based on group_name
    for a channels consumer.
    '''
    class_map = {'job_events': JobAccess,
                 'workflow_events': WorkflowJobAccess,
                 'ad_hoc_command_events': AdHocCommandAccess}
    return class_map.get(group_name)


class BaseAccess(object):
    '''
    Base class for checking user access to a given model.  Subclasses should
    define the model attribute, override the get_queryset method to return only
    the instances the user should be able to view, and override/define can_*
    methods to verify a user's permission to perform a particular action.
    '''

    model = None
    select_related = ()
    prefetch_related = ()

    def __init__(self, user, save_messages=False):
        self.user = user
        self.save_messages = save_messages
        if save_messages:
            self.messages = {}

    def get_queryset(self):
        if self.user.is_superuser or self.user.is_system_auditor:
            qs = self.model.objects.all()
        else:
            qs = self.filtered_queryset()

        # Apply queryset optimizations
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_related:
            qs = qs.prefetch_related(*self.prefetch_related)

        return qs

    def filtered_queryset(self):
        # Override in subclasses
        # filter objects according to user's read access
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

    def can_copy(self, obj):
        return self.can_add({'reference_obj': obj})

    def can_copy_related(self, obj):
        '''
        can_copy_related() should only be used to check if the user have access to related
        many to many credentials in when copying the object. It does not check if the user
        has permission for any other related objects. Therefore, when checking if the user
        can copy an object, it should always be used in conjunction with can_add()
        '''
        return True

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

        If `mandatory` is set, new resources require the field and
                               existing field will always be checked
        '''
        new = None
        changed = True
        if data and 'reference_obj' in data:
            # Use reference object's related fields, if given
            new = getattr(data['reference_obj'], field)
        elif data and field in data:
            new = get_object_from_data(field, Model, data, obj=obj)
        else:
            changed = False

        # Obtain existing related resource
        current = None
        if obj and (changed or mandatory):
            current = getattr(obj, field)

        if obj and new == current:
            # Resource not changed, like a PUT request
            changed = False

        if (not new) and (not obj) and mandatory:
            # Restrict ability to create resource without required field
            return self.user.is_superuser

        def user_has_resource_access(resource):
            role = getattr(resource, role_field, None)
            if role is None:
                # Handle special case where resource does not have direct roles
                access_method_type = {'admin_role': 'change', 'execute_role': 'start'}[role_field]
                return self.user.can_access(type(resource), access_method_type, resource, None)
            return self.user in role

        if new and changed and (not user_has_resource_access(new)):
            return False  # User lacks access to provided resource

        if current and (changed or mandatory) and (not user_has_resource_access(current)):
            return False  # User lacks access to existing resource

        return True  # User has access to both, permission check passed

    def check_license(self, add_host_name=None, feature=None, check_expiration=True, quiet=False):
        validation_info = get_licenser().validate()
        if validation_info.get('license_type', 'UNLICENSED') == 'open':
            return

        if ('test' in sys.argv or 'py.test' in sys.argv[0] or 'jenkins' in sys.argv) and not os.environ.get('SKIP_LICENSE_FIXUP_FOR_TEST', ''):
            validation_info['free_instances'] = 99999999
            validation_info['time_remaining'] = 99999999
            validation_info['grace_period_remaining'] = 99999999

        if quiet:
            report_violation = lambda message: None
        else:
            report_violation = lambda message: logger.warning(message)
        if (
            validation_info.get('trial', False) is True or
            validation_info['instance_count'] == 10  # basic 10 license
        ):
            def report_violation(message):
                raise PermissionDenied(message)

        if check_expiration and validation_info.get('time_remaining', None) is None:
            raise PermissionDenied(_("License is missing."))
        elif check_expiration and validation_info.get("grace_period_remaining") <= 0:
            report_violation(_("License has expired."))

        free_instances = validation_info.get('free_instances', 0)
        available_instances = validation_info.get('available_instances', 0)

        if add_host_name:
            host_exists = Host.objects.filter(name=add_host_name).exists()
            if not host_exists and free_instances == 0:
                report_violation(_("License count of %s instances has been reached.") % available_instances)
            elif not host_exists and free_instances < 0:
                report_violation(_("License count of %s instances has been exceeded.") % available_instances)
        elif not add_host_name and free_instances < 0:
            report_violation(_("Host count exceeds available instances."))

    def check_org_host_limit(self, data, add_host_name=None):
        validation_info = get_licenser().validate()
        if validation_info.get('license_type', 'UNLICENSED') == 'open':
            return

        inventory = get_object_from_data('inventory', Inventory, data)
        if inventory is None:  # In this case a missing inventory error is launched
            return             # further down the line, so just ignore it.

        org = inventory.organization
        if org is None or org.max_hosts == 0:
            return

        active_count = Host.objects.org_active_count(org.id)
        if active_count > org.max_hosts:
            raise PermissionDenied(
                _("You have already reached the maximum number of %s hosts"
                  " allowed for your organization. Contact your System Administrator"
                  " for assistance." % org.max_hosts)
            )

        if add_host_name:
            host_exists = Host.objects.filter(inventory__organization=org.id, name=add_host_name).exists()
            if not host_exists and active_count == org.max_hosts:
                raise PermissionDenied(
                    _("You have already reached the maximum number of %s hosts"
                      " allowed for your organization. Contact your System Administrator"
                      " for assistance." % org.max_hosts)
                )

    def get_user_capabilities(self, obj, method_list=[], parent_obj=None, capabilities_cache={}):
        if obj is None:
            return {}
        user_capabilities = {}

        # Custom ordering to loop through methods so we can reuse earlier calcs
        for display_method in ['edit', 'delete', 'start', 'schedule', 'copy', 'adhoc', 'unattach']:
            if display_method not in method_list:
                continue

            if not settings.MANAGE_ORGANIZATION_AUTH and isinstance(obj, (Team, User)):
                user_capabilities[display_method] = self.user.is_superuser
                continue

            # Actions not possible for reason unrelated to RBAC
            # Cannot copy with validation errors, or update a manual group/project
            if 'write' not in getattr(self.user, 'oauth_scopes', ['write']):
                user_capabilities[display_method] = False  # Read tokens cannot take any actions
                continue
            elif display_method in ['copy', 'start', 'schedule'] and isinstance(obj, JobTemplate):
                if obj.validation_errors:
                    user_capabilities[display_method] = False
                    continue
            elif display_method == 'copy' and isinstance(obj, WorkflowJobTemplate) and obj.organization_id is None:
                user_capabilities[display_method] = self.user.is_superuser
                continue
            elif display_method == 'copy' and isinstance(obj, Project) and obj.scm_type == '':
                # Cannot copy manual project without errors
                user_capabilities[display_method] = False
                continue
            elif display_method in ['start', 'schedule'] and isinstance(obj, (Project)):
                if obj.scm_type == '':
                    user_capabilities[display_method] = False
                    continue

            # Grab the answer from the cache, if available
            if display_method in capabilities_cache:
                user_capabilities[display_method] = capabilities_cache[display_method]
                if self.user.is_superuser and not user_capabilities[display_method]:
                    # Cache override for models with bad orphaned state
                    user_capabilities[display_method] = True
                continue

            # Aliases for going form UI language to API language
            if display_method == 'edit':
                method = 'change'
            elif display_method == 'adhoc':
                method = 'run_ad_hoc_commands'
            else:
                method = display_method

            # Shortcuts in certain cases by deferring to earlier property
            if display_method == 'schedule':
                user_capabilities['schedule'] = user_capabilities['start']
                continue
            elif display_method == 'delete' and not isinstance(obj, (User, UnifiedJob, CustomInventoryScript, CredentialInputSource)):
                user_capabilities['delete'] = user_capabilities['edit']
                continue
            elif display_method == 'copy' and isinstance(obj, (Group, Host)):
                user_capabilities['copy'] = user_capabilities['edit']
                continue

            # Compute permission
            user_capabilities[display_method] = self.get_method_capability(method, obj, parent_obj)

        return user_capabilities

    def get_method_capability(self, method, obj, parent_obj):
        try:
            if method in ['change']: # 3 args
                return self.can_change(obj, {})
            elif method in ['delete', 'run_ad_hoc_commands', 'copy']:
                access_method = getattr(self, "can_%s" % method)
                return access_method(obj)
            elif method in ['start']:
                return self.can_start(obj, validate_license=False)
            elif method in ['attach', 'unattach']: # parent/sub-object call
                access_method = getattr(self, "can_%s" % method)
                if type(parent_obj) == Team:
                    relationship = 'parents'
                    parent_obj = parent_obj.member_role
                else:
                    relationship = 'members'
                return access_method(obj, parent_obj, relationship, skip_sub_obj_read_check=True, data={})
        except (ParseError, ObjectDoesNotExist, PermissionDenied):
            return False
        return False


class NotificationAttachMixin(BaseAccess):
    '''For models that can have notifications attached

    I can attach a notification template when
    - I have notification_admin_role to organization of the NT
    - I can read the object I am attaching it to

    I can unattach when those same critiera are met
    '''
    notification_attach_roles = None

    def _can_attach(self, notification_template, resource_obj):
        if not NotificationTemplateAccess(self.user).can_change(notification_template, {}):
            return False
        if self.notification_attach_roles is None:
            return self.can_read(resource_obj)
        return any(self.user in getattr(resource_obj, role) for role in self.notification_attach_roles)

    @check_superuser
    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if isinstance(sub_obj, NotificationTemplate):
            # reverse obj and sub_obj
            return self._can_attach(notification_template=sub_obj, resource_obj=obj)
        return super(NotificationAttachMixin, self).can_attach(
            obj, sub_obj, relationship, data, skip_sub_obj_read_check=skip_sub_obj_read_check)

    @check_superuser
    def can_unattach(self, obj, sub_obj, relationship, data=None):
        if isinstance(sub_obj, NotificationTemplate):
            # due to this special case, we use symmetrical logic with attach permission
            return self._can_attach(notification_template=sub_obj, resource_obj=obj)
        return super(NotificationAttachMixin, self).can_unattach(
            obj, sub_obj, relationship, data=data
        )


class InstanceAccess(BaseAccess):

    model = Instance
    prefetch_related = ('rampart_groups',)

    def filtered_queryset(self):
        return Instance.objects.filter(
            rampart_groups__in=self.user.get_queryset(InstanceGroup)).distinct()


    def can_attach(self, obj, sub_obj, relationship, data,
                   skip_sub_obj_read_check=False):
        if relationship == 'rampart_groups' and isinstance(sub_obj, InstanceGroup):
            return self.user.is_superuser
        return super(InstanceAccess, self).can_attach(
            obj, sub_obj, relationship, data, skip_sub_obj_read_check=skip_sub_obj_read_check
        )

    def can_unattach(self, obj, sub_obj, relationship, data=None):
        if relationship == 'rampart_groups' and isinstance(sub_obj, InstanceGroup):
            return self.user.is_superuser
        return super(InstanceAccess, self).can_unattach(
            obj, sub_obj, relationship, relationship, data=data
        )

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class InstanceGroupAccess(BaseAccess):

    model = InstanceGroup
    prefetch_related = ('instances',)

    def filtered_queryset(self):
        return InstanceGroup.objects.filter(
            organization__in=Organization.accessible_pk_qs(self.user, 'admin_role')).distinct()

    def can_add(self, data):
        return self.user.is_superuser

    def can_change(self, obj, data):
        return self.user.is_superuser


class UserAccess(BaseAccess):
    '''
    I can see user records when:
     - I'm a superuser
     - I'm in a role with them (such as in an organization or team)
     - They are in a role which includes a role of mine
     - I am in a role that includes a role of theirs
    I can change some fields for a user (mainly password) when I am that user.
    I can change all fields for a user (admin access) or delete when:
     - I'm a superuser.
     - I'm their org admin.
    '''

    model = User
    prefetch_related = ('profile',)

    def filtered_queryset(self):
        if settings.ORG_ADMINS_CAN_SEE_ALL_USERS and \
                (self.user.admin_of_organizations.exists() or self.user.auditor_of_organizations.exists()):
            qs = User.objects.all()
        else:
            qs = (
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
        return qs


    def can_add(self, data):
        if data is not None and ('is_superuser' in data or 'is_system_auditor' in data):
            if (to_python_boolean(data.get('is_superuser', 'false'), allow_none=True) or
                    to_python_boolean(data.get('is_system_auditor', 'false'), allow_none=True)) and not self.user.is_superuser:
                return False
        if self.user.is_superuser:
            return True
        if not settings.MANAGE_ORGANIZATION_AUTH:
            return False
        return Organization.accessible_objects(self.user, 'admin_role').exists()

    def can_change(self, obj, data):
        if data is not None and ('is_superuser' in data or 'is_system_auditor' in data):
            if to_python_boolean(data.get('is_superuser', 'false'), allow_none=True) and \
               not self.user.is_superuser:
                return False
            if to_python_boolean(data.get('is_system_auditor', 'false'), allow_none=True) and not (self.user.is_superuser or self.user == obj):
                return False
        # A user can be changed if they are themselves, or by org admins or
        # superusers.  Change permission implies changing only certain fields
        # that a user should be able to edit for themselves.
        if not settings.MANAGE_ORGANIZATION_AUTH and not self.user.is_superuser:
            return False
        return bool(self.user == obj or self.can_admin(obj, data))

    @staticmethod
    def user_organizations(u):
        '''
        Returns all organizations that count `u` as a member
        '''
        return Organization.accessible_objects(u, 'member_role')

    def is_all_org_admin(self, u):
        '''
        returns True if `u` is member of any organization that is
        not also an organization that `self.user` admins
        '''
        return not self.user_organizations(u).exclude(
            pk__in=Organization.accessible_pk_qs(self.user, 'admin_role')
        ).exists()

    def user_is_orphaned(self, u):
        return not self.user_organizations(u).exists()

    @check_superuser
    def can_admin(self, obj, data, allow_orphans=False, check_setting=True):
        if check_setting and (not settings.MANAGE_ORGANIZATION_AUTH):
            return False
        if obj.is_superuser or obj.is_system_auditor:
            # must be superuser to admin users with system roles
            return False
        if self.user_is_orphaned(obj):
            if not allow_orphans:
                # in these cases only superusers can modify orphan users
                return False
            return not obj.roles.all().exclude(
                ancestors__in=self.user.roles.all()
            ).exists()
        else:
            return self.is_all_org_admin(obj)

    def can_delete(self, obj):
        if obj == self.user:
            # cannot delete yourself
            return False
        super_users = User.objects.filter(is_superuser=True)
        if obj.is_superuser and super_users.count() == 1:
            # cannot delete the last active superuser
            return False
        if self.can_admin(obj, None, allow_orphans=True):
            return True
        return False

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        # The only thing that a User should ever have attached is a Role
        if relationship == 'roles':
            role_access = RoleAccess(self.user)
            return role_access.can_attach(sub_obj, obj, 'members', *args, **kwargs)

        logger.error('Unexpected attempt to associate {} with a user.'.format(sub_obj))
        return False

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        # The only thing that a User should ever have to be unattached is a Role
        if relationship == 'roles':
            role_access = RoleAccess(self.user)
            return role_access.can_unattach(sub_obj, obj, 'members', *args, **kwargs)

        logger.error('Unexpected attempt to de-associate {} from a user.'.format(sub_obj))
        return False


class OAuth2ApplicationAccess(BaseAccess):
    '''
    I can read, change or delete OAuth 2 applications when:
     - I am a superuser.
     - I am the admin of the organization of the user of the application.
     - I am a user in the organization of the application.
    I can create OAuth 2 applications when:
     - I am a superuser.
     - I am the admin of the organization of the application.
    '''

    model = OAuth2Application
    select_related = ('user',)
    prefetch_related = ('organization', 'oauth2accesstoken_set')

    def filtered_queryset(self):
        org_access_qs = Organization.accessible_objects(self.user, 'member_role')
        return self.model.objects.filter(organization__in=org_access_qs)

    def can_change(self, obj, data):
        return self.user.is_superuser or self.check_related('organization', Organization, data, obj=obj,
                                                            role_field='admin_role', mandatory=True)

    def can_delete(self, obj):
        return self.user.is_superuser or obj.organization in self.user.admin_of_organizations

    def can_add(self, data):
        if self.user.is_superuser:
            return True
        if not data:
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data, role_field='admin_role', mandatory=True)


class OAuth2TokenAccess(BaseAccess):
    '''
    I can read, change or delete an app token when:
     - I am a superuser.
     - I am the admin of the organization of the application of the token.
     - I am the user of the token.
    I can create an OAuth2 app token when:
     - I have the read permission of the related application.
    I can read, change or delete a personal token when:
     - I am the user of the token
     - I am the superuser
    I can create an OAuth2 Personal Access Token when:
     - I am a user.  But I can only create a PAT for myself.
    '''

    model = OAuth2AccessToken

    select_related = ('user', 'application')
    prefetch_related = ('refresh_token',)

    def filtered_queryset(self):
        org_access_qs = Organization.objects.filter(
            Q(admin_role__members=self.user) | Q(auditor_role__members=self.user))
        return self.model.objects.filter(application__organization__in=org_access_qs)  | self.model.objects.filter(user__id=self.user.pk)

    def can_delete(self, obj):
        if (self.user.is_superuser) | (obj.user == self.user):
            return True
        elif not obj.application:
            return False
        return self.user in obj.application.organization.admin_role

    def can_change(self, obj, data):
        return self.can_delete(obj)

    def can_add(self, data):
        if 'application' in data:
            app = get_object_from_data('application', OAuth2Application, data)
            if app is None:
                return True
            return OAuth2ApplicationAccess(self.user).can_read(app)
        return True


class OrganizationAccess(NotificationAttachMixin, BaseAccess):
    '''
    I can see organizations when:
     - I am a superuser.
     - I am an admin or user in that organization.
    I can change or delete organizations when:
     - I am a superuser.
     - I'm an admin of that organization.
    I can associate/disassociate instance groups when:
     - I am a superuser.
    '''

    model = Organization
    prefetch_related = ('created_by', 'modified_by',)
    # organization admin_role is not a parent of organization auditor_role
    notification_attach_roles = ['admin_role', 'auditor_role']

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role')

    @check_superuser
    def can_change(self, obj, data):
        return self.user in obj.admin_role

    def can_delete(self, obj):
        is_change_possible = self.can_change(obj, None)
        if not is_change_possible:
            return False
        return True

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        # If the request is updating the membership, check the membership role permissions instead
        if relationship in ('member_role.members', 'admin_role.members'):
            rel_role = getattr(obj, relationship.split('.')[0])
            return RoleAccess(self.user).can_attach(rel_role, sub_obj, 'members', *args, **kwargs)

        if relationship == "instance_groups":
            if self.user.is_superuser:
                return True
            return False
        return super(OrganizationAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        # If the request is updating the membership, check the membership role permissions instead
        if relationship in ('member_role.members', 'admin_role.members'):
            rel_role = getattr(obj, relationship.split('.')[0])
            return RoleAccess(self.user).can_unattach(rel_role, sub_obj, 'members', *args, **kwargs)

        if relationship == "instance_groups":
            return self.can_attach(obj, sub_obj, relationship, *args, **kwargs)
        return super(OrganizationAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)


class InventoryAccess(BaseAccess):
    '''
    I can see inventory when:
     - I'm a superuser.
     - I'm an org admin of the inventory's org.
     - I'm an inventory admin of the inventory's org.
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
    prefetch_related = ('created_by', 'modified_by', 'organization')

    def filtered_queryset(self, allowed=None, ad_hoc=None):
        return self.model.accessible_objects(self.user, 'read_role')

    @check_superuser
    def can_use(self, obj):
        return self.user in obj.use_role

    @check_superuser
    def can_add(self, data):
        # If no data is specified, just checking for generic add permission?
        if not data:
            return Organization.accessible_objects(self.user, 'inventory_admin_role').exists()
        return (self.check_related('organization', Organization, data, role_field='inventory_admin_role') and
                self.check_related('insights_credential', Credential, data, role_field='use_role'))

    @check_superuser
    def can_change(self, obj, data):
        return (self.can_admin(obj, data) and
                self.check_related('insights_credential', Credential, data, obj=obj, role_field='use_role'))

    @check_superuser
    def can_admin(self, obj, data):
        # Host filter may only be modified by org admin level
        org_admin_mandatory = False
        new_host_filter = data.get('host_filter', None) if data else None
        if new_host_filter and new_host_filter != obj.host_filter:
            org_admin_mandatory = True
        # Verify that the user has access to the new organization if moving an
        # inventory to a new organization.  Otherwise, just check for admin permission.
        return (
            self.check_related('organization', Organization, data, obj=obj, role_field='inventory_admin_role',
                               mandatory=org_admin_mandatory) and
            self.user in obj.admin_role
        )

    @check_superuser
    def can_update(self, obj):
        return self.user in obj.update_role

    def can_delete(self, obj):
        return self.can_admin(obj, None)

    def can_run_ad_hoc_commands(self, obj):
        return self.user in obj.adhoc_role

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        if relationship == "instance_groups":
            if self.user.can_access(type(sub_obj), "read", sub_obj) and self.user in obj.organization.admin_role:
                return True
            return False
        return super(InventoryAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        if relationship == "instance_groups":
            return self.can_attach(obj, sub_obj, relationship, *args, **kwargs)
        return super(InventoryAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)


class HostAccess(BaseAccess):
    '''
    I can see hosts whenever I can see their inventory.
    I can change or delete hosts whenver I can change their inventory.
    '''

    model = Host
    select_related = ('created_by', 'modified_by', 'inventory',
                      'last_job__job_template', 'last_job_host_summary__job',)
    prefetch_related = ('groups', 'inventory_sources')

    def filtered_queryset(self):
        return self.model.objects.filter(inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role'))

    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Inventory.accessible_objects(self.user, 'admin_role').exists()

        # Checks for admin or change permission on inventory.
        if not self.check_related('inventory', Inventory, data):
            return False

        # Check to see if we have enough licenses
        self.check_license(add_host_name=data.get('name', None))

        # Check the per-org limit
        self.check_org_host_limit(data, add_host_name=data.get('name', None))

        return True

    def can_change(self, obj, data):
        # Prevent moving a host to a different inventory.
        inventory_pk = get_pk_from_dict(data, 'inventory')
        if obj and inventory_pk and obj.inventory.pk != inventory_pk:
            raise PermissionDenied(_('Unable to change inventory on a host.'))

        # Prevent renaming a host that might exceed license count
        if data and 'name' in data:
            self.check_license(add_host_name=data['name'])

            # Check the per-org limit
            self.check_org_host_limit({'inventory': obj.inventory},
                                      add_host_name=data['name'])

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
    select_related = ('created_by', 'modified_by', 'inventory',)
    prefetch_related = ('parents', 'children',)

    def filtered_queryset(self):
        return Group.objects.filter(inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role'))

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
        return True

    def can_delete(self, obj):
        return bool(obj and self.user in obj.inventory.admin_role)


class InventorySourceAccess(NotificationAttachMixin, BaseAccess):
    '''
    I can see inventory sources whenever I can see their inventory.
    I can change inventory sources whenever I can change their inventory.
    '''

    model = InventorySource
    select_related = ('created_by', 'modified_by', 'inventory')
    prefetch_related = ('credentials__credential_type', 'last_job',
                        'source_script', 'source_project')

    def filtered_queryset(self):
        return self.model.objects.filter(inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role'))

    def can_add(self, data):
        if not data or 'inventory' not in data:
            return Organization.accessible_objects(self.user, 'admin_role').exists()

        if not self.check_related('source_project', Project, data, role_field='use_role'):
            return False
        # Checks for admin or change permission on inventory.
        return self.check_related('inventory', Inventory, data)

    def can_delete(self, obj):
        if not self.user.is_superuser and \
                not (obj and obj.inventory and self.user.can_access(Inventory, 'admin', obj.inventory, None)):
            return False
        return True

    @check_superuser
    def can_change(self, obj, data):
        # Checks for admin change permission on inventory.
        if obj and obj.inventory:
            return (
                self.user.can_access(Inventory, 'change', obj.inventory, None) and
                self.check_related('source_project', Project, data, obj=obj, role_field='use_role')
            )
        # Can't change inventory sources attached to only the inventory, since
        # these are created automatically from the management command.
        else:
            return False

    def can_start(self, obj, validate_license=True):
        if obj and obj.inventory:
            return self.user in obj.inventory.update_role
        return False

    @check_superuser
    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if relationship == 'credentials' and isinstance(sub_obj, Credential):
            return (
                obj and obj.inventory and self.user in obj.inventory.admin_role and
                self.user in sub_obj.use_role)
        return super(InventorySourceAccess, self).can_attach(
            obj, sub_obj, relationship, data, skip_sub_obj_read_check=skip_sub_obj_read_check)

    @check_superuser
    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        if relationship == 'credentials' and isinstance(sub_obj, Credential):
            return obj and obj.inventory and self.user in obj.inventory.admin_role
        return super(InventorySourceAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)


class InventoryUpdateAccess(BaseAccess):
    '''
    I can see inventory updates when I can see the inventory source.
    I can change inventory updates whenever I can change their source.
    I can delete when I can change/delete the inventory source.
    '''

    model = InventoryUpdate
    select_related = ('created_by', 'modified_by', 'inventory_source',)
    prefetch_related = ('unified_job_template', 'instance_group', 'credentials__credential_type', 'inventory', 'source_script')

    def filtered_queryset(self):
        return self.model.objects.filter(inventory_source__inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role'))

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        if self.user.is_superuser or self.user == obj.created_by:
            return True
        # Inventory cascade deletes to inventory update, descends from org admin
        return self.user in obj.inventory_source.inventory.admin_role

    def can_start(self, obj, validate_license=True):
        return InventorySourceAccess(self.user).can_start(obj, validate_license=validate_license)

    @check_superuser
    def can_delete(self, obj):
        return self.user in obj.inventory_source.inventory.admin_role


class CredentialTypeAccess(BaseAccess):
    '''
    I can see credentials types when:
     - I'm authenticated
    I can create when:
     - I'm a superuser:
    I can change when:
     - I'm a superuser and the type is not "managed by Tower"
    '''

    model = CredentialType
    prefetch_related = ('created_by', 'modified_by',)

    def can_use(self, obj):
        return True

    def filtered_queryset(self):
        return self.model.objects.all()


class CredentialAccess(BaseAccess):
    '''
    I can see credentials when:
     - I'm a superuser.
     - It's a user credential and it's my credential.
     - It's a user credential and I'm an admin of an organization where that
       user is a member.
     - It's a user credential and I'm a credential_admin of an organization
       where that user is a member.
     - It's a team credential and I'm an admin of the team's organization.
     - It's a team credential and I'm a credential admin of the team's
       organization.
     - It's a team credential and I'm a member of the team.
    I can change/delete when:
     - I'm a superuser.
     - It's my user credential.
     - It's a user credential for a user in an org I admin.
     - It's a team credential for a team in an org I admin.
    '''

    model = Credential
    select_related = ('created_by', 'modified_by',)
    prefetch_related = ('admin_role', 'use_role', 'read_role',
                        'admin_role__parents', 'admin_role__members',
                        'credential_type', 'organization')

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role')

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        if data and data.get('user', None):
            user_obj = get_object_from_data('user', User, data)
            if not bool(self.user == user_obj or UserAccess(self.user).can_admin(user_obj, None, check_setting=False)):
                return False
        if data and data.get('team', None):
            team_obj = get_object_from_data('team', Team, data)
            if not check_user_access(self.user, Team, 'change', team_obj, None):
                return False
        if data and data.get('organization', None):
            organization_obj = get_object_from_data('organization', Organization, data)
            if not any([check_user_access(self.user, Organization, 'change', organization_obj, None),
                        self.user in organization_obj.credential_admin_role]):
                return False
        if not any(data.get(key, None) for key in ('user', 'team', 'organization')):
            return False  # you have to provide 1 owner field
        return True

    @check_superuser
    def can_use(self, obj):
        return self.user in obj.use_role

    @check_superuser
    def can_change(self, obj, data):
        if not obj:
            return False
        return self.user in obj.admin_role and self.check_related('organization', Organization, data, obj=obj, role_field='credential_admin_role')

    def can_delete(self, obj):
        # Unassociated credentials may be marked deleted by anyone, though we
        # shouldn't ever end up with those.
        #if obj.user is None and obj.team is None:
        #    return True
        return self.can_change(obj, None)

    def get_user_capabilities(self, obj, **kwargs):
        user_capabilities = super(CredentialAccess, self).get_user_capabilities(obj, **kwargs)
        user_capabilities['use'] = self.can_use(obj)
        if getattr(obj, 'managed_by_tower', False) is True:
            user_capabilities['edit'] = user_capabilities['delete'] = False
        return user_capabilities


class CredentialInputSourceAccess(BaseAccess):
    '''
    I can see a CredentialInputSource when:
     - I can see the associated target_credential
    I can create/change a CredentialInputSource when:
     - I'm an admin of the associated target_credential
     - I have use access to the associated source credential
    I can delete a CredentialInputSource when:
     - I'm an admin of the associated target_credential
    '''

    model = CredentialInputSource
    select_related = ('target_credential', 'source_credential')

    def filtered_queryset(self):
        return CredentialInputSource.objects.filter(
            target_credential__in=Credential.accessible_pk_qs(self.user, 'read_role'))

    @check_superuser
    def can_add(self, data):
        return (
            self.check_related('target_credential', Credential, data, role_field='admin_role') and
            self.check_related('source_credential', Credential, data, role_field='use_role')
        )

    @check_superuser
    def can_change(self, obj, data):
        if self.can_add(data) is False:
            return False

        return (
            self.user in obj.target_credential.admin_role and
            self.user in obj.source_credential.use_role
        )

    @check_superuser
    def can_delete(self, obj):
        return self.user in obj.target_credential.admin_role


class TeamAccess(BaseAccess):
    '''
    I can see a team when:
     - I'm a superuser.
     - I'm an admin of the team
     - I'm a member of that team.
     - I'm a member of the team's organization
    I can create/change a team when:
     - I'm a superuser.
     - I'm an admin for the team
    '''

    model = Team
    select_related = ('created_by', 'modified_by', 'organization',)

    def filtered_queryset(self):
        if settings.ORG_ADMINS_CAN_SEE_ALL_USERS and \
                (self.user.admin_of_organizations.exists() or self.user.auditor_of_organizations.exists()):
            return self.model.objects.all()
        return self.model.objects.filter(
            Q(organization__in=Organization.accessible_pk_qs(self.user, 'member_role')) |
            Q(pk__in=self.model.accessible_pk_qs(self.user, 'read_role'))
        )

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        if not settings.MANAGE_ORGANIZATION_AUTH:
            return False
        return self.check_related('organization', Organization, data)

    def can_change(self, obj, data):
        # Prevent moving a team to a different organization.
        org_pk = get_pk_from_dict(data, 'organization')
        if obj and org_pk and obj.organization.pk != org_pk:
            raise PermissionDenied(_('Unable to change organization on a team.'))
        if self.user.is_superuser:
            return True
        if not settings.MANAGE_ORGANIZATION_AUTH:
            return False
        return self.user in obj.admin_role

    def can_delete(self, obj):
        return self.can_change(obj, None)

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        """Reverse obj and sub_obj, defer to RoleAccess if this is an assignment
        of a resource role to the team."""
        # MANAGE_ORGANIZATION_AUTH setting checked in RoleAccess
        if isinstance(sub_obj, Role):
            if sub_obj.content_object is None:
                raise PermissionDenied(_("The {} role cannot be assigned to a team").format(sub_obj.name))

            if isinstance(sub_obj.content_object, ResourceMixin):
                role_access = RoleAccess(self.user)
                return role_access.can_attach(sub_obj, obj, 'member_role.parents',
                                              *args, **kwargs)
        if self.user.is_superuser:
            return True

        # If the request is updating the membership, check the membership role permissions instead
        if relationship in ('member_role.members', 'admin_role.members'):
            rel_role = getattr(obj, relationship.split('.')[0])
            return RoleAccess(self.user).can_attach(rel_role, sub_obj, 'members', *args, **kwargs)

        return super(TeamAccess, self).can_attach(obj, sub_obj, relationship,
                                                  *args, **kwargs)

    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        # MANAGE_ORGANIZATION_AUTH setting checked in RoleAccess
        if isinstance(sub_obj, Role):
            if isinstance(sub_obj.content_object, ResourceMixin):
                role_access = RoleAccess(self.user)
                return role_access.can_unattach(sub_obj, obj, 'member_role.parents',
                                                *args, **kwargs)

        # If the request is updating the membership, check the membership role permissions instead
        if relationship in ('member_role.members', 'admin_role.members'):
            rel_role = getattr(obj, relationship.split('.')[0])
            return RoleAccess(self.user).can_unattach(rel_role, sub_obj, 'members', *args, **kwargs)

        return super(TeamAccess, self).can_unattach(obj, sub_obj, relationship,
                                                    *args, **kwargs)


class ProjectAccess(NotificationAttachMixin, BaseAccess):
    '''
    I can see projects when:
     - I am a superuser.
     - I am an admin in an organization associated with the project.
     - I am a project admin in an organization associated with the project.
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
    select_related = ('credential',)
    prefetch_related = ('modified_by', 'created_by', 'organization', 'last_job', 'current_job')
    notification_attach_roles = ['admin_role']

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role')

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'project_admin_role').exists()
        return (self.check_related('organization', Organization, data, role_field='project_admin_role', mandatory=True) and
                self.check_related('credential', Credential, data, role_field='use_role'))

    @check_superuser
    def can_change(self, obj, data):
        return (self.check_related('organization', Organization, data, obj=obj, role_field='project_admin_role') and
                self.user in obj.admin_role and
                self.check_related('credential', Credential, data, obj=obj, role_field='use_role'))

    @check_superuser
    def can_start(self, obj, validate_license=True):
        return obj and self.user in obj.update_role

    def can_delete(self, obj):
        return self.can_change(obj, None)


class ProjectUpdateAccess(BaseAccess):
    '''
    I can see project updates when I can see the project.
    I can change when I can change the project.
    I can delete when I can change/delete the project.
    '''

    model = ProjectUpdate
    select_related = ('created_by', 'modified_by', 'project',)
    prefetch_related = ('unified_job_template', 'instance_group',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            project__in=Project.accessible_pk_qs(self.user, 'read_role')
        )

    @check_superuser
    def can_cancel(self, obj):
        if self.user == obj.created_by:
            return True
        # Project updates cascade delete with project, admin role descends from org admin
        return self.user in obj.project.admin_role

    def can_start(self, obj, validate_license=True):
        # for relaunching
        try:
            if obj and obj.project:
                return self.user in obj.project.update_role
        except ObjectDoesNotExist:
            pass
        return False

    @check_superuser
    def can_delete(self, obj):
        return obj and self.user in obj.project.admin_role


class JobTemplateAccess(NotificationAttachMixin, BaseAccess):
    '''
    I can see job templates when:
     - I have read role for the job template.
    '''

    model = JobTemplate
    select_related = ('created_by', 'modified_by', 'inventory', 'project', 'organization',
                      'next_schedule',)
    prefetch_related = (
        'instance_groups',
        'credentials__credential_type',
        Prefetch('labels', queryset=Label.objects.all().order_by('name')),
        Prefetch('last_job', queryset=UnifiedJob.objects.non_polymorphic()),
    )

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role')

    def can_add(self, data):
        '''
        a user can create a job template if
         - they are a superuser
         - an org admin of any org that the project is a member
         - if they are a project_admin for any org that project is a member of
         - if they have user or team
        based permissions tying the project to the inventory source for the
        given action as well as the 'create' deploy permission.
        Users who are able to create deploy jobs can also run normal and check (dry run) jobs.
        '''
        if not data:  # So the browseable API will work
            return Project.accessible_objects(self.user, 'use_role').exists()

        # if reference_obj is provided, determine if it can be copied
        reference_obj = data.get('reference_obj', None)

        if self.user.is_superuser:
            return True

        def get_value(Class, field):
            if reference_obj:
                return getattr(reference_obj, field, None)
            else:
                if data and data.get(field, None):
                    return get_object_from_data(field, Class, data)
                else:
                    return None

        # If credentials is provided, the user should have use access to them.
        for pk in data.get('credentials', []):
            raise Exception('Credentials must be attached through association method.')

        # If an inventory is provided, the user should have use access.
        inventory = get_value(Inventory, 'inventory')
        if inventory:
            if self.user not in inventory.use_role:
                return False

        project = get_value(Project, 'project')
        # If the user has admin access to the project (as an org admin), should
        # be able to proceed without additional checks.
        if project:
            return self.user in project.use_role
        else:
            return False

    @check_superuser
    def can_copy_related(self, obj):
        '''
        Check if we have access to all the credentials related to Job Templates.
        Does not verify the user's permission for any other related fields (projects, inventories, etc).
        '''

        # obj.credentials.all() is accessible ONLY when object is saved (has valid id)
        credential_manager = getattr(obj, 'credentials', None) if getattr(obj, 'id', False) else Credential.objects.none()
        user_can_copy = reduce(lambda prev, cred: prev and self.user in cred.use_role, credential_manager.all(), True)
        if not user_can_copy:
            raise PermissionDenied(_('Insufficient access to Job Template credentials.'))
        return user_can_copy

    def can_start(self, obj, validate_license=True):
        # Check license.
        if validate_license:
            self.check_license()

            # Check the per-org limit
            self.check_org_host_limit({'inventory': obj.inventory})

        # Super users can start any job
        if self.user.is_superuser:
            return True

        return self.user in obj.execute_role

    def can_change(self, obj, data):
        if self.user not in obj.admin_role and not self.user.is_superuser:
            return False
        if data is None:
            return True

        data = dict(data)

        if self.changes_are_non_sensitive(obj, data):
            return True

        for required_field, cls in (('inventory', Inventory), ('project', Project)):
            is_mandatory = True
            if not getattr(obj, '{}_id'.format(required_field)):
                is_mandatory = False
            if not self.check_related(required_field, cls, data, obj=obj, role_field='use_role', mandatory=is_mandatory):
                return False
        return True

    def changes_are_non_sensitive(self, obj, data):
        '''
        Return true if the changes being made are considered nonsensitive, and
        thus can be made by a job template administrator which may not have access
        to the any inventory, project, or credentials associated with the template.
        '''
        allowed_fields = [
            'name', 'description', 'forks', 'limit', 'verbosity', 'extra_vars',
            'job_tags', 'force_handlers', 'skip_tags', 'ask_variables_on_launch',
            'ask_tags_on_launch', 'ask_job_type_on_launch', 'ask_skip_tags_on_launch',
            'ask_inventory_on_launch', 'ask_credential_on_launch', 'survey_enabled',
            'custom_virtualenv', 'diff_mode', 'timeout', 'job_slice_count',

            # These fields are ignored, but it is convenient for QA to allow clients to post them
            'last_job_run', 'created', 'modified',
        ]

        for k, v in data.items():
            if k not in [x.name for x in obj._meta.concrete_fields]:
                continue
            if hasattr(obj, k) and getattr(obj, k) != v:
                if k not in allowed_fields and v != getattr(obj, '%s_id' % k, None) \
                        and not (hasattr(obj, '%s_id' % k) and getattr(obj, '%s_id' % k) is None and v == ''): # Equate '' to None in the case of foreign keys
                    return False
        return True

    def can_delete(self, obj):
        return self.user.is_superuser or self.user in obj.admin_role

    @check_superuser
    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if relationship == "instance_groups":
            if not obj.organization:
                return False
            return self.user.can_access(type(sub_obj), "read", sub_obj) and self.user in obj.organization.admin_role
        if relationship == 'credentials' and isinstance(sub_obj, Credential):
            return self.user in obj.admin_role and self.user in sub_obj.use_role
        return super(JobTemplateAccess, self).can_attach(
            obj, sub_obj, relationship, data, skip_sub_obj_read_check=skip_sub_obj_read_check)

    @check_superuser
    def can_unattach(self, obj, sub_obj, relationship, *args, **kwargs):
        if relationship == "instance_groups":
            return self.can_attach(obj, sub_obj, relationship, *args, **kwargs)
        if relationship == 'credentials' and isinstance(sub_obj, Credential):
            return self.user in obj.admin_role
        return super(JobTemplateAccess, self).can_attach(obj, sub_obj, relationship, *args, **kwargs)


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
    select_related = ('created_by', 'modified_by', 'job_template', 'inventory',
                      'project', 'project_update',)
    prefetch_related = (
        'organization',
        'unified_job_template',
        'instance_group',
        'credentials__credential_type',
        Prefetch('labels', queryset=Label.objects.all().order_by('name')),
    )

    def filtered_queryset(self):
        qs = self.model.objects

        qs_jt = qs.filter(
            job_template__in=JobTemplate.accessible_objects(self.user, 'read_role')
        )

        org_access_qs = Organization.objects.filter(
            Q(admin_role__members=self.user) | Q(auditor_role__members=self.user))
        if not org_access_qs.exists():
            return qs_jt

        return qs.filter(
            Q(job_template__in=JobTemplate.accessible_objects(self.user, 'read_role')) |
            Q(organization__in=org_access_qs)).distinct()

    def can_add(self, data, validate_license=True):
        raise NotImplementedError('Direct job creation not possible in v2 API')

    def can_change(self, obj, data):
        raise NotImplementedError('Direct job editing not supported in v2 API')

    @check_superuser
    def can_delete(self, obj):
        if not obj.organization:
            return False
        return self.user in obj.organization.admin_role

    def can_start(self, obj, validate_license=True):
        if validate_license:
            self.check_license()

            # Check the per-org limit
            self.check_org_host_limit({'inventory': obj.inventory})

        # A super user can relaunch a job
        if self.user.is_superuser:
            return True

        # Obtain prompts used to start original job
        JobLaunchConfig = obj._meta.get_field('launch_config').related_model
        try:
            config = JobLaunchConfig.objects.prefetch_related('credentials').get(job=obj)
        except JobLaunchConfig.DoesNotExist:
            config = None

        # Standard permissions model
        if obj.job_template and (self.user not in obj.job_template.execute_role):
            return False

        # Check if JT execute access (and related prompts) is sufficient
        if config and obj.job_template:
            if not config.has_user_prompts(obj.job_template):
                return True
            elif obj.created_by_id != self.user.pk and vars_are_encrypted(config.extra_data):
                # never allowed, not even for org admins
                raise PermissionDenied(_('Job was launched with secret prompts provided by another user.'))
            elif not config.has_unprompted(obj.job_template):
                if JobLaunchConfigAccess(self.user).can_add({'reference_obj': config}):
                    return True

        # Standard permissions model without job template involved
        if obj.organization and self.user in obj.organization.execute_role:
            return True
        elif not (obj.job_template or obj.organization):
            raise PermissionDenied(_('Job has been orphaned from its job template and organization.'))
        elif obj.job_template and config is not None:
            raise PermissionDenied(_('Job was launched with prompted fields you do not have access to.'))
        elif obj.job_template and config is None:
            raise PermissionDenied(_('Job was launched with unknown prompted fields. Organization admin permissions required.'))

        return False

    def get_method_capability(self, method, obj, parent_obj):
        if method == 'start':
            # Return simplistic permission, will perform detailed check on POST
            if not obj.job_template:
                return True
            return self.user in obj.job_template.execute_role
        return super(JobAccess, self).get_method_capability(method, obj, parent_obj)

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        # Users may always cancel their own jobs
        if self.user == obj.created_by:
            return True
        # Users with direct admin to JT may cancel jobs started by anyone
        if obj.job_template and self.user in obj.job_template.admin_role:
            return True
        # If orphaned, allow org JT admins to stop running jobs
        if not obj.job_template and obj.organization and self.user in obj.organization.job_template_admin_role:
            return True
        return False


class SystemJobTemplateAccess(BaseAccess):
    '''
    I can only see/manage System Job Templates if I'm a super user
    '''

    model = SystemJobTemplate

    @check_superuser
    def can_start(self, obj, validate_license=True):
        '''Only a superuser can start a job from a SystemJobTemplate'''
        return False


class SystemJobAccess(BaseAccess):
    '''
    I can only see manage System Jobs if I'm a super user
    '''
    model = SystemJob

    def can_start(self, obj, validate_license=True):
        return False # no relaunching of system jobs


class JobLaunchConfigAccess(BaseAccess):
    '''
    Launch configs must have permissions checked for
     - relaunching
     - rescheduling

    In order to create a new object with a copy of this launch config, I need:
     - use access to related inventory (if present)
     - use role to many-related credentials (if any present)
    '''
    model = JobLaunchConfig
    select_related = ('job')
    prefetch_related = ('credentials', 'inventory')

    def _unusable_creds_exist(self, qs):
        return qs.exclude(
            pk__in=Credential._accessible_pk_qs(Credential, self.user, 'use_role')
        ).exists()

    def has_credentials_access(self, obj):
        # user has access if no related credentials exist that the user lacks use role for
        return not self._unusable_creds_exist(obj.credentials)

    @check_superuser
    def can_add(self, data, template=None):
        # This is a special case, we don't check related many-to-many elsewhere
        # launch RBAC checks use this
        if 'credentials' in data and data['credentials'] or 'reference_obj' in data:
            if 'reference_obj' in data:
                prompted_cred_qs = data['reference_obj'].credentials.all()
            else:
                # If given model objects, only use the primary key from them
                cred_pks = [cred.pk for cred in data['credentials']]
                if template:
                    for cred in template.credentials.all():
                        if cred.pk in cred_pks:
                            cred_pks.remove(cred.pk)
                prompted_cred_qs = Credential.objects.filter(pk__in=cred_pks)
            if self._unusable_creds_exist(prompted_cred_qs):
                return False
        return self.check_related('inventory', Inventory, data, role_field='use_role')

    @check_superuser
    def can_use(self, obj):
        return (
            self.check_related('inventory', Inventory, {}, obj=obj, role_field='use_role', mandatory=True) and
            self.has_credentials_access(obj)
        )

    def can_change(self, obj, data):
        return self.check_related('inventory', Inventory, data, obj=obj, role_field='use_role')

    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if isinstance(sub_obj, Credential) and relationship == 'credentials':
            return self.user in sub_obj.use_role
        else:
            raise NotImplementedError('Only credentials can be attached to launch configurations.')

    def can_unattach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if isinstance(sub_obj, Credential) and relationship == 'credentials':
            if skip_sub_obj_read_check:
                return True
            else:
                return self.user in sub_obj.read_role
        else:
            raise NotImplementedError('Only credentials can be attached to launch configurations.')


class WorkflowJobTemplateNodeAccess(BaseAccess):
    '''
    I can see/use a WorkflowJobTemplateNode if I have read permission
        to associated Workflow Job Template

    In order to add a node, I need:
     - admin access to parent WFJT
     - execute access to the unified job template being used
     - access prompted fields via. launch config access

    In order to do anything to a node, I need admin access to its WFJT

    In order to edit fields on a node, I need:
     - execute access to the unified job template of the node
     - access to prompted fields

    In order to delete a node, I only need the admin access its WFJT

    In order to manage connections (edges) between nodes I do not need anything
      beyond the standard admin access to its WFJT
    '''
    model = WorkflowJobTemplateNode
    prefetch_related = ('success_nodes', 'failure_nodes', 'always_nodes',
                        'unified_job_template', 'credentials', 'workflow_job_template')

    def filtered_queryset(self):
        return self.model.objects.filter(
            workflow_job_template__in=WorkflowJobTemplate.accessible_objects(
                self.user, 'read_role'))

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        return (
            self.check_related('workflow_job_template', WorkflowJobTemplate, data, mandatory=True) and
            self.check_related('unified_job_template', UnifiedJobTemplate, data, role_field='execute_role') and
            JobLaunchConfigAccess(self.user).can_add(data))

    def wfjt_admin(self, obj):
        if not obj.workflow_job_template:
            return self.user.is_superuser
        else:
            return self.user in obj.workflow_job_template.admin_role

    def ujt_execute(self, obj):
        if not obj.unified_job_template:
            return True
        return self.check_related('unified_job_template', UnifiedJobTemplate, {}, obj=obj,
                                  role_field='execute_role', mandatory=True)

    def can_change(self, obj, data):
        if not data:
            return True

        # should not be able to edit the prompts if lacking access to UJT or WFJT
        return (
            self.ujt_execute(obj) and
            self.wfjt_admin(obj) and
            JobLaunchConfigAccess(self.user).can_change(obj, data)
        )

    def can_delete(self, obj):
        return self.wfjt_admin(obj)

    def check_same_WFJT(self, obj, sub_obj):
        if type(obj) != self.model or type(sub_obj) != self.model:
            raise Exception('Attaching workflow nodes only allowed for other nodes')
        if obj.workflow_job_template != sub_obj.workflow_job_template:
            return False
        return True

    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if not self.wfjt_admin(obj):
            return False
        if relationship == 'credentials':
            # Need permission to related template to attach a credential
            if not self.ujt_execute(obj):
                return False
            return JobLaunchConfigAccess(self.user).can_attach(
                obj, sub_obj, relationship, data,
                skip_sub_obj_read_check=skip_sub_obj_read_check
            )
        elif relationship in ('success_nodes', 'failure_nodes', 'always_nodes'):
            return self.check_same_WFJT(obj, sub_obj)
        else:
            raise NotImplementedError('Relationship {} not understood for WFJT nodes.'.format(relationship))

    def can_unattach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        if not self.wfjt_admin(obj):
            return False
        if relationship == 'credentials':
            if not self.ujt_execute(obj):
                return False
            return JobLaunchConfigAccess(self.user).can_unattach(
                obj, sub_obj, relationship, data,
                skip_sub_obj_read_check=skip_sub_obj_read_check
            )
        elif relationship in ('success_nodes', 'failure_nodes', 'always_nodes'):
            return self.check_same_WFJT(obj, sub_obj)
        else:
            raise NotImplementedError('Relationship {} not understood for WFJT nodes.'.format(relationship))


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
    prefetch_related = ('unified_job_template', 'job', 'workflow_job', 'credentials',
                        'success_nodes', 'failure_nodes', 'always_nodes',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            workflow_job__unified_job_template__in=UnifiedJobTemplate.accessible_pk_qs(
                self.user, 'read_role'))

    @check_superuser
    def can_add(self, data):
        if data is None:  # Hide direct creation in API browser
            return False
        return (
            self.check_related('unified_job_template', UnifiedJobTemplate, data, role_field='execute_role') and
            JobLaunchConfigAccess(self.user).can_add(data))

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


# TODO: notification attachments?
class WorkflowJobTemplateAccess(NotificationAttachMixin, BaseAccess):
    '''
    I can see/manage Workflow Job Templates based on object roles
    '''

    model = WorkflowJobTemplate
    select_related = ('created_by', 'modified_by', 'organization', 'next_schedule',
                      'admin_role', 'execute_role', 'read_role',)

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role')

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
            return Organization.accessible_objects(self.user, 'workflow_admin_role').exists()

        return (
            self.check_related('organization', Organization, data, role_field='workflow_admin_role', mandatory=True) and
            self.check_related('inventory', Inventory, data, role_field='use_role')
        )

    def can_copy(self, obj):
        if self.save_messages:
            missing_ujt = []
            missing_credentials = []
            missing_inventories = []
            qs = obj.workflow_job_template_nodes
            qs = qs.prefetch_related('unified_job_template', 'inventory__use_role', 'credentials__use_role')
            for node in qs.all():
                if node.inventory and self.user not in node.inventory.use_role:
                    missing_inventories.append(node.inventory.name)
                for cred in node.credentials.all():
                    if self.user not in cred.use_role:
                        missing_credentials.append(cred.name)
                ujt = node.unified_job_template
                if ujt and not self.user.can_access(UnifiedJobTemplate, 'start', ujt, validate_license=False):
                    missing_ujt.append(ujt.name)
            if missing_ujt:
                self.messages['templates_unable_to_copy'] = missing_ujt
            if missing_credentials:
                self.messages['credentials_unable_to_copy'] = missing_credentials
            if missing_inventories:
                self.messages['inventories_unable_to_copy'] = missing_inventories

        return self.check_related('organization', Organization, {'reference_obj': obj}, role_field='workflow_admin_role',
                                  mandatory=True)

    def can_start(self, obj, validate_license=True):
        if validate_license:
            # check basic license, node count
            self.check_license()

            # Check the per-org limit
            self.check_org_host_limit({'inventory': obj.inventory})

        # Super users can start any job
        if self.user.is_superuser:
            return True

        return self.user in obj.execute_role

    def can_change(self, obj, data):
        if self.user.is_superuser:
            return True

        return (
            self.check_related('organization', Organization, data, role_field='workflow_admin_role', obj=obj) and
            self.check_related('inventory', Inventory, data, role_field='use_role', obj=obj) and
            self.user in obj.admin_role
        )

    def can_delete(self, obj):
        return self.user.is_superuser or self.user in obj.admin_role


class WorkflowJobAccess(BaseAccess):
    '''
    I can only see Workflow Jobs if I can see the associated
    workflow job template that it was created from.
    I can delete them if I am admin of their workflow job template
    I can cancel one if I can delete it
       I can also cancel it if I started it
    '''
    model = WorkflowJob
    select_related = ('created_by', 'modified_by', 'organization',)

    def filtered_queryset(self):
        return WorkflowJob.objects.filter(
            unified_job_template__in=UnifiedJobTemplate.accessible_pk_qs(
                self.user, 'read_role'))

    def can_add(self, data):
        # Old add-start system for launching jobs is being depreciated, and
        # not supported for new types of resources
        return False

    def can_change(self, obj, data):
        return False

    @check_superuser
    def can_delete(self, obj):
        return (obj.workflow_job_template and
                obj.workflow_job_template.organization and
                self.user in obj.workflow_job_template.organization.workflow_admin_role)

    def get_method_capability(self, method, obj, parent_obj):
        if method == 'start':
            # Return simplistic permission, will perform detailed check on POST
            if not obj.workflow_job_template:
                return self.user.is_superuser
            return self.user in obj.workflow_job_template.execute_role
        return super(WorkflowJobAccess, self).get_method_capability(method, obj, parent_obj)

    def can_start(self, obj, validate_license=True):
        if validate_license:
            self.check_license()

            # Check the per-org limit
            self.check_org_host_limit({'inventory': obj.inventory})

        if self.user.is_superuser:
            return True

        template = obj.workflow_job_template
        if not template and obj.job_template_id:
            template = obj.job_template
        # only superusers can relaunch orphans
        if not template:
            return False

        # Obtain prompts used to start original job
        JobLaunchConfig = obj._meta.get_field('launch_config').related_model
        try:
            config = JobLaunchConfig.objects.get(job=obj)
        except JobLaunchConfig.DoesNotExist:
            if self.save_messages:
                self.messages['detail'] = _('Workflow Job was launched with unknown prompts.')
            return False

        # execute permission to WFJT is mandatory for any relaunch
        if self.user not in template.execute_role:
            return False

        # Check if access to prompts to prevent relaunch
        if config.prompts_dict():
            if obj.created_by_id != self.user.pk and vars_are_encrypted(config.extra_data):
                raise PermissionDenied(_("Job was launched with secret prompts provided by another user."))
            if not JobLaunchConfigAccess(self.user).can_add({'reference_obj': config}):
                raise PermissionDenied(_('Job was launched with prompts you lack access to.'))
            if config.has_unprompted(template):
                raise PermissionDenied(_('Job was launched with prompts no longer accepted.'))

        return True  # passed config checks

    def can_recreate(self, obj):
        node_qs = obj.workflow_job_nodes.all().prefetch_related('inventory', 'credentials', 'unified_job_template')
        node_access = WorkflowJobNodeAccess(user=self.user)
        wj_add_perm = True
        for node in node_qs:
            if not node_access.can_add({'reference_obj': node}):
                wj_add_perm = False
        if not wj_add_perm and self.save_messages:
            self.messages['workflow_job_template'] = _('You do not have permission to the workflow job '
                                                       'resources required for relaunch.')
        return wj_add_perm

    def can_cancel(self, obj):
        if not obj.can_cancel:
            return False
        if self.user == obj.created_by or self.can_delete(obj):
            return True
        return obj.workflow_job_template is not None and self.user in obj.workflow_job_template.admin_role


class AdHocCommandAccess(BaseAccess):
    '''
    I can only see/run ad hoc commands when:
    - I am a superuser.
    - I have read access to the inventory
    '''
    model = AdHocCommand
    select_related = ('created_by', 'modified_by', 'inventory', 'credential',)

    def filtered_queryset(self):
        return self.model.objects.filter(inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role'))

    def can_add(self, data, validate_license=True):
        if not data:  # So the browseable API will work
            return True

        if validate_license:
            self.check_license()

            # Check the per-org limit
            self.check_org_host_limit(data)

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
    select_related = ('job', 'job__job_template', 'host',)

    def filtered_queryset(self):
        job_qs = self.user.get_queryset(Job)
        host_qs = self.user.get_queryset(Host)
        return self.model.objects.filter(job__in=job_qs, host__in=host_qs)

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
    prefetch_related = ('job__job_template', 'host',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(host__inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role')) |
            Q(job__job_template__in=JobTemplate.accessible_pk_qs(self.user, 'read_role')))

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class ProjectUpdateEventAccess(BaseAccess):
    '''
    I can see project update event records whenever I can access the project update
    '''

    model = ProjectUpdateEvent

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(project_update__project__in=Project.accessible_pk_qs(self.user, 'read_role')))

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class InventoryUpdateEventAccess(BaseAccess):
    '''
    I can see inventory update event records whenever I can access the inventory update
    '''

    model = InventoryUpdateEvent

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(inventory_update__inventory_source__inventory__in=Inventory.accessible_pk_qs(self.user, 'read_role')))

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class SystemJobEventAccess(BaseAccess):
    '''
    I can only see manage System Jobs events if I'm a super user
    '''
    model = SystemJobEvent

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class UnifiedJobTemplateAccess(BaseAccess):
    '''
    I can see a unified job template whenever I can see the same project,
    inventory source, WFJT, or job template.  Unified job templates do not include
    inventory sources without a cloud source.
    '''

    model = UnifiedJobTemplate
    select_related = (
        'created_by',
        'modified_by',
        'next_schedule',
    )
    # prefetch last/current jobs so we get the real instance
    prefetch_related = (
        'last_job',
        'current_job',
        'organization',
        'credentials__credential_type',
        Prefetch('labels', queryset=Label.objects.all().order_by('name')),
    )

    # WISH - sure would be nice if the following worked, but it does not.
    # In the future, as django and polymorphic libs are upgraded, try again.

    #qs = qs.prefetch_related(
    #    'project',
    #    'inventory',
    #)

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(pk__in=self.model.accessible_pk_qs(self.user, 'read_role')) |
            Q(inventorysource__inventory__id__in=Inventory._accessible_pk_qs(
                Inventory, self.user, 'read_role'))
        )

    def can_start(self, obj, validate_license=True):
        access_class = access_registry[obj.__class__]
        access_instance = access_class(self.user)
        return access_instance.can_start(obj, validate_license=validate_license)

    def get_queryset(self):
        return super(UnifiedJobTemplateAccess, self).get_queryset().filter(
            workflowapprovaltemplate__isnull=True)


class UnifiedJobAccess(BaseAccess):
    '''
    I can see a unified job whenever I can see the same project update,
    inventory update or job.
    '''

    model = UnifiedJob
    prefetch_related = (
        'created_by',
        'modified_by',
        'organization',
        'unified_job_node__workflow_job',
        'unified_job_template',
        'instance_group',
        'credentials__credential_type',
        Prefetch('labels', queryset=Label.objects.all().order_by('name')),
    )

    # WISH - sure would be nice if the following worked, but it does not.
    # In the future, as django and polymorphic libs are upgraded, try again.

    #qs = qs.prefetch_related(
    #    'project',
    #    'inventory',
    #    'job_template',
    #    'inventory_source',
    #    'project___credential',
    #    'inventory_source___credential',
    #    'inventory_source___inventory',
    #    'job_template__inventory',
    #    'job_template__project',
    #)

    def filtered_queryset(self):
        inv_pk_qs = Inventory._accessible_pk_qs(Inventory, self.user, 'read_role')
        org_auditor_qs = Organization.objects.filter(
            Q(admin_role__members=self.user) | Q(auditor_role__members=self.user))
        qs = self.model.objects.filter(
            Q(unified_job_template_id__in=UnifiedJobTemplate.accessible_pk_qs(self.user, 'read_role')) |
            Q(inventoryupdate__inventory_source__inventory__id__in=inv_pk_qs) |
            Q(adhoccommand__inventory__id__in=inv_pk_qs) |
            Q(organization__in=org_auditor_qs)
        )
        return qs

    def get_queryset(self):
        return super(UnifiedJobAccess, self).get_queryset().filter(
            workflowapproval__isnull=True)


class ScheduleAccess(BaseAccess):
    '''
    I can see a schedule if I can see it's related unified job, I can create them or update them if I have write access
    '''

    model = Schedule
    select_related = ('created_by', 'modified_by',)
    prefetch_related = ('unified_job_template', 'credentials',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            unified_job_template__in=UnifiedJobTemplateAccess(self.user).filtered_queryset()
        )

    @check_superuser
    def can_add(self, data):
        if not JobLaunchConfigAccess(self.user).can_add(data):
            return False
        if not data:
            return Role.objects.filter(role_field__in=['update_role', 'execute_role'], ancestors__in=self.user.roles.all()).exists()

        return self.check_related('unified_job_template', UnifiedJobTemplate, data, role_field='execute_role', mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if not JobLaunchConfigAccess(self.user).can_change(obj, data):
            return False
        if self.check_related('unified_job_template', UnifiedJobTemplate, data, obj=obj, mandatory=True):
            return True
        # Users with execute role can modify the schedules they created
        return (
            obj.created_by == self.user and
            self.check_related('unified_job_template', UnifiedJobTemplate, data, obj=obj, role_field='execute_role', mandatory=True))

    def can_delete(self, obj):
        return self.can_change(obj, {})

    def can_attach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        return JobLaunchConfigAccess(self.user).can_attach(
            obj, sub_obj, relationship, data,
            skip_sub_obj_read_check=skip_sub_obj_read_check
        )

    def can_unattach(self, obj, sub_obj, relationship, data, skip_sub_obj_read_check=False):
        return JobLaunchConfigAccess(self.user).can_unattach(
            obj, sub_obj, relationship, data,
            skip_sub_obj_read_check=skip_sub_obj_read_check
        )


class NotificationTemplateAccess(BaseAccess):
    '''
    I can see/use a notification_template if I have permission to
    '''
    model = NotificationTemplate
    prefetch_related = ('created_by', 'modified_by', 'organization')

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(organization__in=Organization.accessible_objects(self.user, 'notification_admin_role')) |
            Q(organization__in=self.user.auditor_of_organizations)
        ).distinct()

    @check_superuser
    def can_add(self, data):
        if not data:
            return Organization.accessible_objects(self.user, 'notification_admin_role').exists()
        return self.check_related('organization', Organization, data, role_field='notification_admin_role', mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if obj.organization is None:
            # only superusers are allowed to edit orphan notification templates
            return False
        return self.check_related('organization', Organization, data, obj=obj, role_field='notification_admin_role', mandatory=True)

    def can_admin(self, obj, data):
        return self.can_change(obj, data)

    def can_delete(self, obj):
        return self.can_change(obj, None)

    @check_superuser
    def can_start(self, obj, validate_license=True):
        if obj.organization is None:
            return False
        return self.user in obj.organization.notification_admin_role


class NotificationAccess(BaseAccess):
    '''
    I can see/use a notification if I have permission to
    '''
    model = Notification
    prefetch_related = ('notification_template',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(notification_template__organization__in=Organization.accessible_objects(self.user, 'notification_admin_role')) |
            Q(notification_template__organization__in=self.user.auditor_of_organizations)
        ).distinct()

    def can_delete(self, obj):
        return self.user.can_access(NotificationTemplate, 'delete', obj.notification_template)


class LabelAccess(BaseAccess):
    '''
    I can see/use a Label if I have permission to associated organization, or to a JT that the label is on
    '''
    model = Label
    prefetch_related = ('modified_by', 'created_by', 'organization',)

    def filtered_queryset(self):
        return self.model.objects.filter(
            Q(organization__in=Organization.accessible_pk_qs(self.user, 'read_role')) |
            Q(unifiedjobtemplate_labels__in=UnifiedJobTemplate.accessible_pk_qs(self.user, 'read_role'))
        )

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return True
        return self.check_related('organization', Organization, data, role_field='member_role', mandatory=True)

    @check_superuser
    def can_change(self, obj, data):
        if self.can_add(data) is False:
            return False

        return self.user in obj.organization.admin_role

    def can_delete(self, obj):
        return self.can_change(obj, None)


class ActivityStreamAccess(BaseAccess):
    '''
    I can see activity stream events only when I have permission on all objects included in the event
    '''

    model = ActivityStream
    prefetch_related = ('organization', 'user', 'inventory', 'host', 'group',
                        'inventory_update', 'credential', 'credential_type', 'team',
                        'ad_hoc_command', 'o_auth2_application', 'o_auth2_access_token',
                        'notification_template', 'notification', 'label', 'role', 'actor',
                        'schedule', 'custom_inventory_script', 'unified_job_template',
                        'workflow_job_template_node',)

    def filtered_queryset(self):
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
        # FIXME: the following fields will be attached to the wrong object
        # if they are included in prefetch_related because of
        # https://github.com/django-polymorphic/django-polymorphic/issues/68
        # 'job_template', 'job', 'project', 'project_update', 'workflow_job',
        # 'inventory_source', 'workflow_job_template'

        inventory_set = Inventory.accessible_objects(self.user, 'read_role')
        credential_set = Credential.accessible_objects(self.user, 'read_role')
        auditing_orgs = (
            Organization.accessible_objects(self.user, 'admin_role') |
            Organization.accessible_objects(self.user, 'auditor_role')
        ).distinct().values_list('id', flat=True)
        project_set = Project.accessible_objects(self.user, 'read_role')
        jt_set = JobTemplate.accessible_objects(self.user, 'read_role')
        team_set = Team.accessible_objects(self.user, 'read_role')
        wfjt_set = WorkflowJobTemplate.accessible_objects(self.user, 'read_role')
        app_set = OAuth2ApplicationAccess(self.user).filtered_queryset()
        token_set = OAuth2TokenAccess(self.user).filtered_queryset()

        return qs.filter(
            Q(ad_hoc_command__inventory__in=inventory_set) |
            Q(o_auth2_application__in=app_set) |
            Q(o_auth2_access_token__in=token_set) |
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
            Q(workflow_job_template__in=wfjt_set) |
            Q(workflow_job_template_node__workflow_job_template__in=wfjt_set) |
            Q(workflow_job__workflow_job_template__in=wfjt_set) |
            Q(notification_template__organization__in=auditing_orgs) |
            Q(notification__notification_template__organization__in=auditing_orgs) |
            Q(label__organization__in=auditing_orgs) |
            Q(role__in=Role.objects.filter(ancestors__in=self.user.roles.all()) if auditing_orgs else [])
        ).distinct()

    def can_add(self, data):
        return False

    def can_change(self, obj, data):
        return False

    def can_delete(self, obj):
        return False


class CustomInventoryScriptAccess(BaseAccess):

    model = CustomInventoryScript
    prefetch_related = ('created_by', 'modified_by', 'organization')

    def filtered_queryset(self):
        return self.model.accessible_objects(self.user, 'read_role').all()

    @check_superuser
    def can_add(self, data):
        if not data:  # So the browseable API will work
            return Organization.accessible_objects(self.user, 'admin_role').exists()
        return self.check_related('organization', Organization, data, mandatory=True)

    @check_superuser
    def can_admin(self, obj, data=None):
        return self.check_related('organization', Organization, data, obj=obj) and self.user in obj.admin_role

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
    prefetch_related = ('content_type',)

    def filtered_queryset(self):
        result = Role.visible_roles(self.user)
        # Sanity check: is the requesting user an orphaned non-admin/auditor?
        # if yes, make system admin/auditor mandatorily visible.
        if not self.user.is_superuser and not self.user.is_system_auditor and not self.user.organizations.exists():
            mandatories = ('system_administrator', 'system_auditor')
            super_qs = Role.objects.filter(singleton_name__in=mandatories)
            result = result | super_qs
        return result

    def can_add(self, obj, data):
        # Unsupported for now
        return False

    def can_attach(self, obj, sub_obj, relationship, *args, **kwargs):
        return self.can_unattach(obj, sub_obj, relationship, *args, **kwargs)

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

        # Being a user in the member_role or admin_role of an organization grants
        # administrators of that Organization the ability to edit that user. To prevent
        # unwanted escalations let's ensure that the Organization administrator has the ability
        # to admin the user being added to the role.
        if isinstance(obj.content_object, Organization) and obj.role_field in ['admin_role', 'member_role']:
            if not isinstance(sub_obj, User):
                logger.error('Unexpected attempt to associate {} with organization role.'.format(sub_obj))
                return False
            if not settings.MANAGE_ORGANIZATION_AUTH and not self.user.is_superuser:
                return False
            if not UserAccess(self.user).can_admin(sub_obj, None, allow_orphans=True):
                return False

        if isinstance(obj.content_object, Team) and obj.role_field in ['admin_role', 'member_role']:
            if not settings.MANAGE_ORGANIZATION_AUTH and not self.user.is_superuser:
                return False

        if isinstance(obj.content_object, ResourceMixin) and self.user in obj.content_object.admin_role:
            return True
        return False

    def can_delete(self, obj):
        # Unsupported for now
        return False


class WorkflowApprovalAccess(BaseAccess):
    '''
    A user can create a workflow approval if they are a superuser, an org admin
    of the org connected to the workflow, or if they are assigned as admins to
    the workflow.

    A user can approve a workflow when they are:
    - a superuser
    - a workflow admin
    - an organization admin
    - any user who has explicitly been assigned the "approver" role

    A user can see approvals if they have read access to the associated WorkflowJobTemplate.
    '''

    model = WorkflowApproval
    prefetch_related = ('created_by', 'modified_by',)

    def can_use(self, obj):
        return True

    def can_start(self, obj, validate_license=True):
        return True

    def filtered_queryset(self):
        return self.model.objects.filter(
            unified_job_node__workflow_job__unified_job_template__in=WorkflowJobTemplate.accessible_pk_qs(
                self.user, 'read_role'))

    def can_approve_or_deny(self, obj):
        if (
            (obj.workflow_job_template and self.user in obj.workflow_job_template.approval_role) or
            self.user.is_superuser
        ):
            return True


class WorkflowApprovalTemplateAccess(BaseAccess):
    '''
    A user can create a workflow approval if they are a superuser, an org admin
    of the org connected to the workflow, or if they are assigned as admins to
    the workflow.

    A user can approve a workflow when they are:
    - a superuser
    - a workflow admin
    - an organization admin
    - any user who has explicitly been assigned the "approver" role at the workflow or organization level

    A user can see approval templates if they have read access to the associated WorkflowJobTemplate.
    '''

    model = WorkflowApprovalTemplate
    prefetch_related = ('created_by', 'modified_by',)

    @check_superuser
    def can_add(self, data):
        if data is None:  # Hide direct creation in API browser
            return False
        else:
            return (self.check_related('workflow_approval_template', UnifiedJobTemplate, role_field='admin_role'))

    def can_change(self, obj, data):
        return self.user.can_access(WorkflowJobTemplate, 'change', obj.workflow_job_template, data={})

    def can_start(self, obj, validate_license=False):
        # for copying WFJTs that contain approval nodes
        if self.user.is_superuser:
            return True

        return self.user in obj.workflow_job_template.execute_role

    def filtered_queryset(self):
        return self.model.objects.filter(
            workflowjobtemplatenodes__workflow_job_template__in=WorkflowJobTemplate.accessible_pk_qs(
                self.user, 'read_role'))


for cls in BaseAccess.__subclasses__():
    access_registry[cls.model] = cls
