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
from django.db import models, transaction, connection
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.conf import settings

# Ansible_base app
from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment, RoleTeamAssignment
from ansible_base.lib.utils.models import get_type_for_model

# AWX
from awx.api.versioning import reverse
from awx.main.migrations._dab_rbac import build_role_map, get_permissions_for_role
from awx.main.constants import role_name_to_perm_mapping, org_role_to_permission

__all__ = [
    'Role',
    'batch_role_ancestor_rebuilding',
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


tls = threading.local()  # thread local storage


def check_singleton(func):
    """
    check_singleton is a decorator that checks if a user given
    to a `visible_roles` method is in either of our singleton roles (Admin, Auditor)
    and if so, returns their full list of roles without filtering.
    """

    def wrapper(*args, **kwargs):
        user = args[0]
        if user.is_superuser or user.is_system_auditor:
            if len(args) == 2:
                return args[1]
            return Role.objects.all()
        return func(*args, **kwargs)

    return wrapper


@contextlib.contextmanager
def batch_role_ancestor_rebuilding(allow_nesting=False):
    """
    Batches the role ancestor rebuild work necessary whenever role-role
    relations change. This can result in a big speedup when performing
    any bulk manipulation.

    WARNING: Calls to anything related to checking access/permissions
    while within the context of the batch_role_ancestor_rebuilding will
    likely not work.
    """

    batch_role_rebuilding = getattr(tls, 'batch_role_rebuilding', False)

    try:
        setattr(tls, 'batch_role_rebuilding', True)
        if not batch_role_rebuilding:
            setattr(tls, 'additions', set())
            setattr(tls, 'removals', set())
        yield

    finally:
        setattr(tls, 'batch_role_rebuilding', batch_role_rebuilding)
        if not batch_role_rebuilding:
            additions = getattr(tls, 'additions')
            removals = getattr(tls, 'removals')
            with transaction.atomic():
                Role.rebuild_role_ancestor_list(list(additions), list(removals))
            delattr(tls, 'additions')
            delattr(tls, 'removals')


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
    ancestors = models.ManyToManyField(
        'Role', through='RoleAncestorEntry', through_fields=('descendent', 'ancestor'), related_name='descendents'
    )  # auto-generated by `rebuild_role_ancestor_list`
    members = models.ManyToManyField('auth.User', related_name='roles')
    content_type = models.ForeignKey(ContentType, null=True, default=None, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        if 'role_field' in self.__dict__:
            return u'%s-%s' % (self.name, self.pk)
        else:
            return u'%s-%s' % (self._meta.verbose_name, self.pk)

    def save(self, *args, **kwargs):
        super(Role, self).save(*args, **kwargs)
        self.rebuild_role_ancestor_list([self.id], [])

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

            if settings.ANSIBLE_BASE_ROLE_SYSTEM_ACTIVATED:
                if self.content_object and self.content_object._meta.model_name == 'organization' and self.role_field in org_role_to_permission:
                    codename = org_role_to_permission[self.role_field]

                    return accessor.has_obj_perm(self.content_object, codename)

                if self.role_field not in to_permissions:
                    raise Exception(f'{self.role_field} evaluated but not a translatable permission')
                return accessor.has_obj_perm(self.content_object, to_permissions[self.role_field])
            return self.ancestors.filter(members=accessor).exists()
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
    def rebuild_role_ancestor_list(additions, removals):
        """
        Updates our `ancestors` map to accurately reflect all of the ancestors for a role

        You should never need to call this. Signal handlers should be calling
        this method when the role hierachy changes automatically.
        """
        # The ancestry table
        # =================================================
        #
        #   The role ancestors table denormalizes the parental relations
        #   between all roles in the system. If you have role A which is a
        #   parent of B which is a parent of C, then the ancestors table will
        #   contain a row noting that B is a descendent of A, and two rows for
        #   denoting that C is a descendent of both A and B. In addition to
        #   storing entries for each descendent relationship, we also store an
        #   entry that states that C is a 'descendent' of itself, C. This makes
        #   usage of this table simple in our queries as it enables us to do
        #   straight joins where we would have to do unions otherwise.
        #
        # The simple version of what this function is doing
        # =================================================
        #
        #   When something changes in our role "hierarchy", we need to update
        #   the `Role.ancestors` mapping to reflect these changes. The basic
        #   idea, which the code in this method is modeled after, is to do
        #   this: When a change happens to a role's parents list, we update
        #   that role's ancestry list, then we recursively update any child
        #   roles ancestry lists.  Because our role relationships are not
        #   strictly hierarchical, and can even have loops, this process may
        #   necessarily visit the same nodes more than once. To handle this
        #   without having to keep track of what should be updated (again) and
        #   in what order, we simply use the termination condition of stopping
        #   when our stored ancestry list matches what our list should be, eg,
        #   when nothing changes. This can be simply implemented:
        #
        #      if actual_ancestors != stored_ancestors:
        #          for id in actual_ancestors - stored_ancestors:
        #              self.ancestors.add(id)
        #          for id in stored_ancestors - actual_ancestors:
        #              self.ancestors.remove(id)
        #
        #          for child in self.children.all():
        #              child.rebuild_role_ancestor_list()
        #
        #   However this results in a lot of calls to the database, so the
        #   optimized implementation below effectively does this same thing,
        #   but we update all children at once, so effectively we sweep down
        #   through our hierarchy one layer at a time instead of one node at a
        #   time. Because of how this method works, we can also start from many
        #   roots at once and sweep down a large set of roles, which we take
        #   advantage of when performing bulk operations.
        #
        #
        # SQL Breakdown
        # =============
        #   We operate under the assumption that our parent's ancestor list is
        #   correct, thus we can always compute what our ancestor list should
        #   be by taking the union of our parent's ancestor lists and adding
        #   our self reference entry where ancestor_id = descendent_id
        #
        #   The DELETE query deletes all entries in the ancestor table that
        #   should no longer be there (as determined by the NOT EXISTS query,
        #   which checks to see if the ancestor is still an ancestor of one
        #   or more of our parents)
        #
        #   The INSERT query computes the list of what our ancestor maps should
        #   be, and inserts any missing entries.
        #
        #   Once complete, we select all of the children for the roles we are
        #   working with, this list becomes the new role list we are working
        #   with.
        #
        #   When our delete or insert query return that they have not performed
        #   any work, then we know that our children will also not need to be
        #   updated, and so we can terminate our loop.
        #
        #

        if settings.ANSIBLE_BASE_ROLE_SYSTEM_ACTIVATED:
            return

        if len(additions) == 0 and len(removals) == 0:
            return

        global tls
        batch_role_rebuilding = getattr(tls, 'batch_role_rebuilding', False)

        if batch_role_rebuilding:
            getattr(tls, 'additions').update(set(additions))
            getattr(tls, 'removals').update(set(removals))
            return

        cursor = connection.cursor()
        loop_ct = 0

        sql_params = {
            'ancestors_table': Role.ancestors.through._meta.db_table,
            'parents_table': Role.parents.through._meta.db_table,
            'roles_table': Role._meta.db_table,
        }

        # SQLlite has a 1M sql statement limit.. since the django sqllite
        # driver isn't letting us pass in the ids through the preferred
        # parameter binding system, this function exists to obey this.
        # est max 12 bytes per number, used up to 2 times in a query,
        # minus 4k of padding for the other parts of the query, leads us
        # to the magic number of 41496, or 40000 for a nice round number
        def split_ids_for_sqlite(role_ids):
            for i in range(0, len(role_ids), 40000):
                yield role_ids[i : i + 40000]

        with transaction.atomic():
            while len(additions) > 0 or len(removals) > 0:
                if loop_ct > 100:
                    raise Exception('Role ancestry rebuilding error: infinite loop detected')
                loop_ct += 1

                delete_ct = 0
                if len(removals) > 0:
                    for ids in split_ids_for_sqlite(removals):
                        sql_params['ids'] = ','.join(str(x) for x in ids)
                        cursor.execute(
                            '''
                            DELETE FROM %(ancestors_table)s
                            WHERE descendent_id IN (%(ids)s)
                                  AND descendent_id != ancestor_id
                                  AND NOT EXISTS (
                                      SELECT 1
                                        FROM %(parents_table)s as parents
                                             INNER JOIN %(ancestors_table)s as inner_ancestors
                                                     ON (parents.to_role_id = inner_ancestors.descendent_id)
                                       WHERE parents.from_role_id = %(ancestors_table)s.descendent_id
                                             AND %(ancestors_table)s.ancestor_id = inner_ancestors.ancestor_id
                                  )
                        '''
                            % sql_params
                        )

                        delete_ct += cursor.rowcount

                insert_ct = 0
                if len(additions) > 0:
                    for ids in split_ids_for_sqlite(additions):
                        sql_params['ids'] = ','.join(str(x) for x in ids)
                        cursor.execute(
                            '''
                            INSERT INTO %(ancestors_table)s (descendent_id, ancestor_id, role_field, content_type_id, object_id)
                            SELECT from_id, to_id, new_ancestry_list.role_field, new_ancestry_list.content_type_id, new_ancestry_list.object_id FROM  (
                                  SELECT roles.id from_id,
                                         ancestors.ancestor_id to_id,
                                         roles.role_field,
                                         COALESCE(roles.content_type_id, 0) content_type_id,
                                         COALESCE(roles.object_id, 0) object_id
                                    FROM %(roles_table)s as roles
                                         INNER JOIN %(parents_table)s as parents
                                                 ON (parents.from_role_id = roles.id)
                                         INNER JOIN %(ancestors_table)s as ancestors
                                                 ON (parents.to_role_id = ancestors.descendent_id)
                                   WHERE roles.id IN (%(ids)s)

                                   UNION

                                  SELECT id from_id,
                                         id to_id,
                                         role_field,
                                         COALESCE(content_type_id, 0) content_type_id,
                                         COALESCE(object_id, 0) object_id
                                   from %(roles_table)s WHERE id IN (%(ids)s)
                             ) new_ancestry_list
                             WHERE NOT EXISTS (
                                SELECT 1 FROM %(ancestors_table)s
                                 WHERE %(ancestors_table)s.descendent_id = new_ancestry_list.from_id
                                       AND %(ancestors_table)s.ancestor_id = new_ancestry_list.to_id
                             )

                        '''
                            % sql_params
                        )
                        insert_ct += cursor.rowcount

                if insert_ct == 0 and delete_ct == 0:
                    break

                new_additions = set()
                for ids in split_ids_for_sqlite(additions):
                    sql_params['ids'] = ','.join(str(x) for x in ids)
                    # get all children for the roles we're operating on
                    cursor.execute('SELECT DISTINCT from_role_id FROM %(parents_table)s WHERE to_role_id IN (%(ids)s)' % sql_params)
                    new_additions.update([row[0] for row in cursor.fetchall()])
                additions = list(new_additions)

                new_removals = set()
                for ids in split_ids_for_sqlite(removals):
                    sql_params['ids'] = ','.join(str(x) for x in ids)
                    # get all children for the roles we're operating on
                    cursor.execute('SELECT DISTINCT from_role_id FROM %(parents_table)s WHERE to_role_id IN (%(ids)s)' % sql_params)
                    new_removals.update([row[0] for row in cursor.fetchall()])
                removals = list(new_removals)

    @staticmethod
    def visible_roles(user):
        return Role.filter_visible_roles(user, Role.objects.all())

    @staticmethod
    @check_singleton
    def filter_visible_roles(user, roles_qs):
        """
        Visible roles include all roles that are ancestors of any
        roles that the user has access to.
        Case in point - organization auditor_role must see all roles
        in their organization, but some of those roles descend from
        organization admin_role, but not auditor_role.
        """
        if settings.ANSIBLE_BASE_ROLE_SYSTEM_ACTIVATED:
            from ansible_base.rbac.models import RoleEvaluation

            q = RoleEvaluation.objects.filter(role__in=user.has_roles.all()).values_list('object_id', 'content_type_id').query
            return roles_qs.extra(where=[f'(object_id,content_type_id) in ({q})'])

        return roles_qs.filter(
            id__in=RoleAncestorEntry.objects.filter(
                descendent__in=RoleAncestorEntry.objects.filter(ancestor_id__in=list(user.roles.values_list('id', flat=True))).values_list(
                    'descendent', flat=True
                )
            )
            .distinct()
            .values_list('ancestor', flat=True)
        )

    @staticmethod
    def singleton(name):
        role, _ = Role.objects.get_or_create(singleton_name=name, role_field=name)
        return role

    def is_ancestor_of(self, role):
        return role.ancestors.filter(id=self.id).exists()

    def is_singleton(self):
        return self.singleton_name in [ROLE_SINGLETON_SYSTEM_ADMINISTRATOR, ROLE_SINGLETON_SYSTEM_AUDITOR]


class AncestorManager(models.Manager):
    def get_queryset(self):
        if settings.ANSIBLE_BASE_ROLE_SYSTEM_ACTIVATED:
            raise RuntimeError('The old RBAC system has been disabled, this should never be called')
        return super(AncestorManager, self).get_queryset()


class RoleAncestorEntry(models.Model):
    class Meta:
        app_label = 'main'
        verbose_name_plural = _('role_ancestors')
        db_table = 'main_rbac_role_ancestors'
        indexes = [
            models.Index(fields=["ancestor", "content_type_id", "object_id"]),  # used by get_roles_on_resource
            models.Index(fields=["ancestor", "content_type_id", "role_field"]),  # used by accessible_objects
            models.Index(fields=["ancestor", "descendent"]),  # used by rebuild_role_ancestor_list in the NOT EXISTS clauses.
        ]

    descendent = models.ForeignKey(Role, null=False, on_delete=models.CASCADE, related_name='+')
    ancestor = models.ForeignKey(Role, null=False, on_delete=models.CASCADE, related_name='+')
    role_field = models.TextField(null=False)
    content_type_id = models.PositiveIntegerField(null=False)
    object_id = models.PositiveIntegerField(null=False)

    objects = AncestorManager()


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
    perm_list = get_role_codenames(role)
    defaults = {
        'content_type_id': role.content_type_id,
        'description': f'Has {action_name.title()} permission to {model_print} for backwards API compatibility',
    }
    # use Controller-specific role definitions for Team/Organization and member/admin
    # instead of platform role definitions
    # these should exist in the system already, so just do a lookup by role definition name
    if model_print in ['Team', 'Organization'] and action_name in ['member', 'admin']:
        rd_name = f'Controller {model_print} {action_name.title()}'
        rd = RoleDefinition.objects.filter(name=rd_name).first()
        if rd:
            return rd
        else:
            return RoleDefinition.objects.create_from_permissions(permissions=perm_list, name=rd_name, managed=True, **defaults)

    else:
        rd_name = f'{model_print} {action_name.title()} Compat'

    with impersonate(None):
        try:
            rd, created = RoleDefinition.objects.get_or_create(name=rd_name, permissions=perm_list, defaults=defaults)
        except ValidationError:
            # This is a tricky case - practically speaking, users should not be allowed to create team roles
            # or roles that include the team member permission.
            # If we need to create this for compatibility purposes then we will create it as a managed non-editable role
            defaults['managed'] = True
            rd, created = RoleDefinition.objects.get_or_create(name=rd_name, permissions=perm_list, defaults=defaults)
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
    elif rd.name.startswith('Controller') and rd.name.endswith(' Admin'):
        # Controller Organization Admin and Controller Team Admin
        role_name = 'admin_role'
    elif rd.name.startswith('Controller') and rd.name.endswith(' Member'):
        # Controller Organization Member and Controller Team Member
        role_name = 'member_role'
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
    return getattr(object_role.content_object, role_name)


def give_or_remove_permission(role, actor, giving=True):
    obj = role.content_object
    if obj is None:
        return
    rd = get_role_definition(role)
    rd.give_or_remove_permission(actor, obj, giving=giving)


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
    assignment = RoleDefinition.objects.give_creator_permissions(user, obj)
    if assignment:
        with disable_rbac_sync():
            old_role = get_role_from_object_role(assignment.object_role)
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
        give_or_remove_permission(role, user, giving=is_giving)


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
            give_or_remove_permission(child_role, team, giving=is_giving)


ROLE_DEFINITION_TO_ROLE_FIELD = {
    'Organization Member': 'member_role',
    'Controller Organization Member': 'member_role',
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
    'Controller Team Admin': 'admin_role',
    'Team Member': 'member_role',
    'Controller Team Member': 'member_role',
    'Organization Admin': 'admin_role',
    'Controller Organization Admin': 'admin_role',
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
def sync_assignments_to_old_rbac_delete(instance, **kwargs):
    _sync_assignments_to_old_rbac(instance, delete=True)


@receiver(post_save, sender=RoleUserAssignment)
@receiver(post_save, sender=RoleTeamAssignment)
def sync_user_assignments_to_old_rbac_create(instance, **kwargs):
    _sync_assignments_to_old_rbac(instance, delete=False)


m2m_changed.connect(sync_members_to_new_rbac, Role.members.through)
m2m_changed.connect(sync_parents_to_new_rbac, Role.parents.through)
