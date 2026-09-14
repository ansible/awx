# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import logging
import threading
import contextlib
import re

# django-rest-framework
from rest_framework.serializers import ValidationError

# crum to impersonate users
from crum import impersonate

# Django
from django.db import models
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps

# Ansible_base app
from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment, RoleTeamAssignment
from ansible_base.rbac.sync import maybe_reverse_sync_assignment, maybe_reverse_sync_unassignment, maybe_reverse_sync_role_definition
from ansible_base.rbac import permission_registry
from ansible_base.resource_registry.signals.handlers import no_reverse_sync
from ansible_base.lib.utils.models import get_type_for_model

# AWX
from awx.api.versioning import reverse
from awx.main.migrations._dab_rbac import build_role_map, get_permissions_for_role
from awx.main.constants import role_name_to_perm_mapping, org_role_to_permission

__all__ = [
    'Role',
    'ROLE_SINGLETON_SYSTEM_ADMINISTRATOR',
    'ROLE_SINGLETON_SYSTEM_AUDITOR',
    'role_summary_fields_generator',
]

logger = logging.getLogger('awx.main.models.rbac')

ROLE_SINGLETON_SYSTEM_ADMINISTRATOR = 'system_administrator'
ROLE_SINGLETON_SYSTEM_AUDITOR = 'system_auditor'

role_names = {
    'system_administrator': _('System Administrator'),
    'system_auditor': _('System Auditor'),
    'adhoc_role': _('Ad Hoc'),
    'admin_role': _('Admin'),
    'project_admin_role': _('Project Admin'),
    'inventory_admin_role': _('Inventory Admin'),
    'credential_admin_role': _('Credential Admin'),
    'job_template_admin_role': _('Job Template Admin'),
    'execution_environment_admin_role': _('Execution Environment Admin'),
    'workflow_admin_role': _('Workflow Admin'),
    'notification_admin_role': _('Notification Admin'),
    'auditor_role': _('Auditor'),
    'execute_role': _('Execute'),
    'member_role': _('Member'),
    'read_role': _('Read'),
    'update_role': _('Update'),
    'use_role': _('Use'),
    'approval_role': _('Approve'),
}

role_descriptions = {
    'system_administrator': _('Can manage all aspects of the system'),
    'system_auditor': _('Can view all aspects of the system'),
    'adhoc_role': _('May run ad hoc commands on the %s'),
    'admin_role': _('Can manage all aspects of the %s'),
    'project_admin_role': _('Can manage all projects of the %s'),
    'inventory_admin_role': _('Can manage all inventories of the %s'),
    'credential_admin_role': _('Can manage all credentials of the %s'),
    'job_template_admin_role': _('Can manage all job templates of the %s'),
    'execution_environment_admin_role': _('Can manage all execution environments of the %s'),
    'workflow_admin_role': _('Can manage all workflows of the %s'),
    'notification_admin_role': _('Can manage all notifications of the %s'),
    'auditor_role': _('Can view all aspects of the %s'),
    'execute_role': {
        'organization': _('May run any executable resources in the organization'),
        'default': _('May run the %s'),
    },
    'member_role': _('User is a member of the %s'),
    'read_role': _('May view settings for the %s'),
    'update_role': _('May update the %s'),
    'use_role': _('Can use the %s in a job template'),
    'approval_role': _('Can approve or deny a workflow approval node'),
}


to_permissions = {}
for k, v in role_name_to_perm_mapping.items():
    to_permissions[k] = v[0].strip('_')


class Role(models.Model):
    """
    Role model
    """

    class Meta:
        app_label = 'main'
        verbose_name_plural = _('roles')
        db_table = 'main_rbac_roles'
        indexes = [models.Index(fields=["content_type", "object_id"])]
        ordering = ("content_type", "object_id")

    role_field = models.TextField(null=False)
    singleton_name = models.TextField(null=True, default=None, db_index=True, unique=True)
    parents = models.ManyToManyField('Role', related_name='children')
    implicit_parents = models.TextField(null=False, default='[]')
    members = models.ManyToManyField('auth.User', related_name='roles')
    content_type = models.ForeignKey(ContentType, null=True, default=None, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        if 'role_field' in self.__dict__:
            return '%s-%s' % (self.name, self.pk)
        else:
            return '%s-%s' % (self._meta.verbose_name, self.pk)

    def get_absolute_url(self, request=None):
        return reverse('api:role_detail', kwargs={'pk': self.pk}, request=request)

    def __contains__(self, accessor):
        if accessor._meta.model_name == 'user':
            if accessor.is_superuser:
                return True
            if self.role_field == 'system_administrator':
                return accessor.is_superuser
            elif self.role_field == 'system_auditor':
                return accessor.is_system_auditor
            elif self.role_field in ('read_role', 'auditor_role') and accessor.is_system_auditor:
                return True

            if self.content_object and self.content_object._meta.model_name == 'organization' and self.role_field in org_role_to_permission:
                codename = org_role_to_permission[self.role_field]
                return accessor.has_obj_perm(self.content_object, codename)

            if self.role_field not in to_permissions:
                raise Exception(f'{self.role_field} evaluated but not a translatable permission')
            return accessor.has_obj_perm(self.content_object, to_permissions[self.role_field])
        else:
            raise RuntimeError(f'Role evaluations only valid for users, received {accessor}')

    @property
    def name(self):
        global role_names
        return role_names[self.role_field]

    @property
    def description(self):
        global role_descriptions
        description = role_descriptions[self.role_field]
        content_type = self.content_type

        model_name = None
        if content_type:
            model = content_type.model_class()
            model_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', model.__name__).lower()

        value = description
        if type(description) == dict:
            value = description.get(model_name)
            if value is None:
                value = description.get('default')

        if '%s' in value and content_type:
            value = value % model_name

        return value

    @staticmethod
    def visible_roles(user):
        return Role.filter_visible_roles(user, Role.objects.all())

    @staticmethod
    def filter_visible_roles(user, roles_qs):
        if user.is_superuser or user.is_system_auditor:
            return roles_qs

        from ansible_base.rbac.models import RoleEvaluation

        q = RoleEvaluation.objects.filter(role__in=user.has_roles.all()).values_list('object_id', 'content_type_id').query
        return roles_qs.extra(where=[f'(object_id,content_type_id) in ({q})'])

    @staticmethod
    def singleton(name):
        role, _ = Role.objects.get_or_create(singleton_name=name, role_field=name)
        return role

    def is_singleton(self):
        return self.singleton_name in [ROLE_SINGLETON_SYSTEM_ADMINISTRATOR, ROLE_SINGLETON_SYSTEM_AUDITOR]


def role_summary_fields_generator(content_object, role_field):
    global role_descriptions
    global role_names
    summary = {}
    description = role_descriptions[role_field]

    model_name = None
    content_type = ContentType.objects.get_for_model(content_object)
    if content_type:
        model = content_object.__class__
        model_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', model.__name__).lower()

    value = description
    if type(description) == dict:
        value = None
        if model_name:
            value = description.get(model_name)
        if value is None:
            value = description.get('default')

    if '%s' in value and model_name:
        value = value % model_name

    summary['description'] = value
    summary['name'] = role_names[role_field]
    summary['id'] = getattr(content_object, '{}_id'.format(role_field))
    return summary


# ----------------- Custom Role Compatibility -------------------------
# The following are methods to connect this (old) RBAC system to the new
# system which allows custom roles
# this follows the ORM interface layer documented in docs/rbac.md
def get_role_codenames(role):
    obj = role.content_object
    if obj is None:
        return
    f = obj._meta.get_field(role.role_field)
    parents, children = build_role_map(apps)
    return [perm.codename for perm in get_permissions_for_role(f, children, apps)]


def get_role_definition(role):
    """Given a old-style role, this gives a role definition in the new RBAC system for it"""
    obj = role.content_object
    if obj is None:
        return
    f = obj._meta.get_field(role.role_field)
    action_name = f.name.rsplit("_", 1)[0]
    model_print = type(obj).__name__
    rd_name = f'{model_print} {action_name.title()} Compat'
    perm_list = get_role_codenames(role)
    defaults = {
        'content_type': permission_registry.content_type_model.objects.get_by_natural_key(role.content_type.app_label, role.content_type.model),
        'description': f'Has {action_name.title()} permission to {model_print} for backwards API compatibility',
    }

    with impersonate(None):
        try:
            with no_reverse_sync():
                rd, created = RoleDefinition.objects.get_or_create(name=rd_name, permissions=perm_list, defaults=defaults)
        except ValidationError:
            # This is a tricky case - practically speaking, users should not be allowed to create team roles
            # or roles that include the team member permission.
            # If we need to create this for compatibility purposes then we will create it as a managed non-editable role
            defaults['managed'] = True
            with no_reverse_sync():
                rd, created = RoleDefinition.objects.get_or_create(name=rd_name, permissions=perm_list, defaults=defaults)

        if created and rbac_sync_enabled.enabled:
            maybe_reverse_sync_role_definition(rd, action='create')
    return rd


def get_role_from_object_role(object_role):
    """
    Given an object role from the new system, return the corresponding role from the old system
    reverses naming from get_role_definition, and the ANSIBLE_BASE_ROLE_PRECREATE setting.
    """
    rd = object_role.role_definition
    if rd.name.endswith(' Compat'):
        model_name, role_name, _ = rd.name.split()
        role_name = role_name.lower()
        role_name += '_role'
    elif rd.name.endswith(' Admin') and rd.name.count(' ') == 2:
        # cases like "Organization Project Admin"
        model_name, target_model_name, role_name = rd.name.split()
        role_name = role_name.lower()
        model_cls = apps.get_model('main', target_model_name)
        target_model_name = get_type_for_model(model_cls)

        # exception cases completely specific to one model naming convention
        if target_model_name == 'notification_template':
            target_model_name = 'notification'
        elif target_model_name == 'workflow_job_template':
            target_model_name = 'workflow'

        role_name = f'{target_model_name}_admin_role'
    elif rd.name.endswith(' Admin'):
        # cases like "project-admin"
        role_name = 'admin_role'
    elif rd.name == 'Organization Audit':
        role_name = 'auditor_role'
    else:
        model_name, role_name = rd.name.split()
        role_name = role_name.lower()
        role_name += '_role'
    return getattr(object_role.content_object, role_name, None)


def give_or_remove_permission(role, actor, giving=True, rd=None):
    obj = role.content_object
    if obj is None:
        return
    if not rd:
        rd = get_role_definition(role)
    assignment = rd.give_or_remove_permission(actor, obj, giving=giving)
    return assignment


class SyncEnabled(threading.local):
    def __init__(self):
        self.enabled = True


rbac_sync_enabled = SyncEnabled()


@contextlib.contextmanager
def disable_rbac_sync():
    try:
        previous_value = rbac_sync_enabled.enabled
        rbac_sync_enabled.enabled = False
        yield
    finally:
        rbac_sync_enabled.enabled = previous_value


def give_creator_permissions(user, obj):
    from awx.main.signals import disable_activity_stream

    assignment = RoleDefinition.objects.give_creator_permissions(user, obj)
    if assignment:
        with disable_rbac_sync():
            old_role = get_role_from_object_role(assignment.object_role)
            if old_role is None:
                return
            # The new-side assignment above is already recorded by
            # record_role_assignment_activity_stream. Suppress activity stream for this
            # mirrored write so it isn't recorded a second time.
            with disable_activity_stream():
                old_role.members.add(user)


def sync_members_to_new_rbac(instance, action, model, pk_set, reverse, **kwargs):
    if action.startswith('pre_'):
        return
    if not rbac_sync_enabled.enabled:
        return

    if action == 'post_add':
        is_giving = True
    elif action == 'post_remove':
        is_giving = False
    elif action == 'post_clear':
        raise RuntimeError('Clearing of role members not supported')

    if reverse:
        user = instance
    else:
        role = instance

    for user_or_role_id in pk_set:
        if reverse:
            role = Role.objects.get(pk=user_or_role_id)
        else:
            user = get_user_model().objects.get(pk=user_or_role_id)
        rd = get_role_definition(role)
        assignment = give_or_remove_permission(role, user, giving=is_giving, rd=rd)

        # sync to resource server
        if rbac_sync_enabled.enabled:
            if is_giving:
                maybe_reverse_sync_assignment(assignment)
            else:
                maybe_reverse_sync_unassignment(rd, user, role.content_object)


def sync_parents_to_new_rbac(instance, action, model, pk_set, reverse, **kwargs):
    if action.startswith('pre_'):
        return

    if action == 'post_add':
        is_giving = True
    elif action == 'post_remove':
        is_giving = False
    elif action == 'post_clear':
        raise RuntimeError('Clearing of role members not supported')

    if reverse:
        parent_role = instance
    else:
        child_role = instance

    for role_id in pk_set:
        if reverse:
            try:
                child_role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                continue
        else:
            try:
                parent_role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                continue

        # To a fault, we want to avoid running this if triggered from implicit_parents management
        # we only want to do anything if we know for sure this is a non-implicit team role
        if parent_role.role_field == 'member_role' and parent_role.content_type.model == 'team':
            # Team internal parents are member_role->read_role and admin_role->member_role
            # for the same object, this parenting will also be implicit_parents management
            # do nothing for internal parents, but OTHER teams may still be assigned permissions to a team
            if (child_role.content_type_id == parent_role.content_type_id) and (child_role.object_id == parent_role.object_id):
                return

            from awx.main.models.organization import Team

            team = Team.objects.get(pk=parent_role.object_id)
            rd = get_role_definition(child_role)
            assignment = give_or_remove_permission(child_role, team, giving=is_giving, rd=rd)

            # sync to resource server
            if rbac_sync_enabled.enabled:
                if is_giving:
                    maybe_reverse_sync_assignment(assignment)
                else:
                    maybe_reverse_sync_unassignment(rd, team, child_role.content_object)


ROLE_DEFINITION_TO_ROLE_FIELD = {
    'Organization Member': 'member_role',
    'WorkflowJobTemplate Admin': 'admin_role',
    'Organization WorkflowJobTemplate Admin': 'workflow_admin_role',
    'WorkflowJobTemplate Execute': 'execute_role',
    'WorkflowJobTemplate Approve': 'approval_role',
    'InstanceGroup Admin': 'admin_role',
    'InstanceGroup Use': 'use_role',
    'Organization ExecutionEnvironment Admin': 'execution_environment_admin_role',
    'Project Admin': 'admin_role',
    'Organization Project Admin': 'project_admin_role',
    'Project Use': 'use_role',
    'Project Update': 'update_role',
    'JobTemplate Admin': 'admin_role',
    'Organization JobTemplate Admin': 'job_template_admin_role',
    'JobTemplate Execute': 'execute_role',
    'Inventory Admin': 'admin_role',
    'Organization Inventory Admin': 'inventory_admin_role',
    'Inventory Use': 'use_role',
    'Inventory Adhoc': 'adhoc_role',
    'Inventory Update': 'update_role',
    'Organization NotificationTemplate Admin': 'notification_admin_role',
    'Credential Admin': 'admin_role',
    'Organization Credential Admin': 'credential_admin_role',
    'Credential Use': 'use_role',
    'Team Admin': 'admin_role',
    'Team Member': 'member_role',
    'Organization Admin': 'admin_role',
    'Organization Audit': 'auditor_role',
    'Organization Execute': 'execute_role',
    'Organization Approval': 'approval_role',
}


def _sync_assignments_to_old_rbac(instance, delete=True):
    from awx.main.signals import disable_activity_stream

    with disable_activity_stream():
        with disable_rbac_sync():
            field_name = ROLE_DEFINITION_TO_ROLE_FIELD.get(instance.role_definition.name)
            if not field_name:
                return
            try:
                role = getattr(instance.object_role.content_object, field_name)
            # in the case RoleUserAssignment is being cascade deleted, then
            # object_role might not exist. In which case the object is about to be removed
            # anyways so just return
            except ObjectDoesNotExist:
                return
            if isinstance(instance.actor, get_user_model()):
                # user
                if delete:
                    role.members.remove(instance.actor)
                else:
                    role.members.add(instance.actor)
            else:
                # team
                if delete:
                    instance.team.member_role.children.remove(role)
                else:
                    instance.team.member_role.children.add(role)


@receiver(post_delete, sender=RoleUserAssignment)
@receiver(post_delete, sender=RoleTeamAssignment)
def sync_assignments_to_old_rbac_delete(instance, origin=None, **kwargs):
    # Skip cascade deletes from non-assignment origins — sync is redundant:
    #  - Model origin with app_label != dab_rbac: a parent object (e.g.
    #    Organization) is being deleted and old Role M2M tables cascade from
    #    the same parent.
    #  - QuerySet of a different model (e.g. ObjectRole): bulk RBAC cleanup
    #    such as defer_rbac_computations flush — parent objects already gone.
    if isinstance(origin, models.Model) and origin._meta.app_label != 'dab_rbac':
        return
    if isinstance(origin, models.QuerySet) and origin.model is not type(instance):
        return
    _sync_assignments_to_old_rbac(instance, delete=True)


@receiver(post_save, sender=RoleUserAssignment)
@receiver(post_save, sender=RoleTeamAssignment)
def sync_user_assignments_to_old_rbac_create(instance, **kwargs):
    _sync_assignments_to_old_rbac(instance, delete=False)


m2m_changed.connect(sync_members_to_new_rbac, Role.members.through)
m2m_changed.connect(sync_parents_to_new_rbac, Role.parents.through)
