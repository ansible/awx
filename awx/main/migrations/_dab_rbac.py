import json
import logging

from django.apps import apps as global_apps
from django.db.models import ForeignKey
from django.utils.timezone import now
from ansible_base.rbac.migrations._utils import give_permissions
from ansible_base.rbac.management import create_dab_permissions

from awx.main.fields import ImplicitRoleField
from awx.main.constants import role_name_to_perm_mapping


logger = logging.getLogger('awx.main.migrations._dab_rbac')


def create_permissions_as_operation(apps, schema_editor):
    create_dab_permissions(global_apps.get_app_config("main"), apps=apps)


"""
Data structures and methods for the migration of old Role model to ObjectRole
"""

system_admin = ImplicitRoleField(name='system_administrator')
system_auditor = ImplicitRoleField(name='system_auditor')
system_admin.model = None
system_auditor.model = None


def resolve_parent_role(f, role_path):
    """
    Given a field and a path declared in parent_role from the field definition, like
        execute_role = ImplicitRoleField(parent_role='admin_role')
    This expects to be passed in (execute_role object, "admin_role")
    It hould return the admin_role from that object
    """
    if role_path == 'singleton:system_administrator':
        return system_admin
    elif role_path == 'singleton:system_auditor':
        return system_auditor
    else:
        related_field = f
        current_model = f.model
        for related_field_name in role_path.split('.'):
            related_field = current_model._meta.get_field(related_field_name)
            if isinstance(related_field, ForeignKey) and not isinstance(related_field, ImplicitRoleField):
                current_model = related_field.related_model
        return related_field


def build_role_map(apps):
    """
    For the old Role model, this builds and returns dictionaries (children, parents)
    which give a global mapping of the ImplicitRoleField instances according to the graph
    """
    models = set(apps.get_app_config('main').get_models())

    all_fields = set()
    parents = {}
    children = {}

    all_fields.add(system_admin)
    all_fields.add(system_auditor)

    for cls in models:
        for f in cls._meta.get_fields():
            if isinstance(f, ImplicitRoleField):
                all_fields.add(f)

    for f in all_fields:
        if f.parent_role is not None:
            if isinstance(f.parent_role, str):
                parent_roles = [f.parent_role]
            else:
                parent_roles = f.parent_role

            # SPECIAL CASE: organization auditor_role is not a child of admin_role
            # this makes no practical sense and conflicts with expected managed role
            # so we put it in as a hack here
            if f.name == 'auditor_role' and f.model._meta.model_name == 'organization':
                parent_roles.append('admin_role')

            parent_list = []
            for rel_name in parent_roles:
                parent_list.append(resolve_parent_role(f, rel_name))

            parents[f] = parent_list

    # build children lookup from parents lookup
    for child_field, parent_list in parents.items():
        for parent_field in parent_list:
            children.setdefault(parent_field, [])
            children[parent_field].append(child_field)

    return (parents, children)


def get_descendents(f, children_map):
    """
    Given ImplicitRoleField F and the children mapping, returns all descendents
    of that field, as a set of other fields, including itself
    """
    ret = {f}
    if f in children_map:
        for child_field in children_map[f]:
            ret.update(get_descendents(child_field, children_map))
    return ret


def get_permissions_for_role(role_field, children_map, apps):
    Permission = apps.get_model('dab_rbac', 'DABPermission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    perm_list = []
    for child_field in get_descendents(role_field, children_map):
        if child_field.name in role_name_to_perm_mapping:
            for perm_name in role_name_to_perm_mapping[child_field.name]:
                if perm_name == 'add_' and role_field.model._meta.model_name != 'organization':
                    continue  # only organizations can contain add permissions
                perm = Permission.objects.filter(content_type=ContentType.objects.get_for_model(child_field.model), codename__startswith=perm_name).first()
                if perm is not None and perm not in perm_list:
                    perm_list.append(perm)

    # special case for two models that have object roles but no organization roles in old system
    if role_field.name == 'notification_admin_role' or (role_field.name == 'admin_role' and role_field.model._meta.model_name == 'organization'):
        ct = ContentType.objects.get_for_model(apps.get_model('main', 'NotificationTemplate'))
        perm_list.extend(list(Permission.objects.filter(content_type=ct)))
    if role_field.name == 'execution_environment_admin_role' or (role_field.name == 'admin_role' and role_field.model._meta.model_name == 'organization'):
        ct = ContentType.objects.get_for_model(apps.get_model('main', 'ExecutionEnvironment'))
        perm_list.extend(list(Permission.objects.filter(content_type=ct)))

    # more special cases for those same above special org-level roles
    if role_field.name == 'auditor_role':
        for codename in ('view_notificationtemplate', 'view_executionenvironment'):
            perm_list.append(Permission.objects.get(codename=codename))

    return perm_list


def migrate_to_new_rbac(apps, schema_editor):
    """
    This method moves the assigned permissions from the old rbac.py models
    to the new RoleDefinition and ObjectRole models
    """
    Role = apps.get_model('main', 'Role')
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    RoleUserAssignment = apps.get_model('dab_rbac', 'RoleUserAssignment')
    Permission = apps.get_model('dab_rbac', 'DABPermission')
    migration_time = now()

    # remove add premissions that are not valid for migrations from old versions
    for perm_str in ('add_organization', 'add_jobtemplate'):
        perm = Permission.objects.filter(codename=perm_str).first()
        if perm:
            perm.delete()

    managed_definitions = dict()
    for role_definition in RoleDefinition.objects.filter(managed=True):
        permissions = frozenset(role_definition.permissions.values_list('id', flat=True))
        managed_definitions[permissions] = role_definition

    # Build map of old role model
    parents, children = build_role_map(apps)

    # NOTE: this import is expected to break at some point, and then just move the data here
    from awx.main.models.rbac import role_descriptions

    for role in Role.objects.prefetch_related('members', 'parents').iterator():
        if role.singleton_name:
            continue  # only bothering to migrate object roles

        team_roles = []
        for parent in role.parents.all():
            if parent.id not in json.loads(role.implicit_parents):
                team_roles.append(parent)

        # we will not create any roles that do not have any users or teams
        if not (role.members.all() or team_roles):
            logger.debug(f'Skipping role {role.role_field} for {role.content_type.model}-{role.object_id} due to no members')
            continue

        # get a list of permissions that the old role would grant
        object_cls = apps.get_model(f'main.{role.content_type.model}')
        object = object_cls.objects.get(pk=role.object_id)  # WORKAROUND, role.content_object does not work in migrations
        f = object._meta.get_field(role.role_field)  # should be ImplicitRoleField
        perm_list = get_permissions_for_role(f, children, apps)

        permissions = frozenset(perm.id for perm in perm_list)

        # With the needed permissions established, obtain the RoleDefinition this will need, priorities:
        # 1. If it exists as a managed RoleDefinition then obviously use that
        # 2. If we already created this for a prior role, use that
        # 3. Create a new RoleDefinition that lists those permissions
        if permissions in managed_definitions:
            role_definition = managed_definitions[permissions]
        else:
            action = role.role_field.rsplit('_', 1)[0]  # remove the _field ending of the name
            role_definition_name = f'{role.content_type.model}-{action}'

            description = role_descriptions[role.role_field]
            if type(description) == dict:
                if role.content_type.model in description:
                    description = description.get(role.content_type.model)
                else:
                    description = description.get('default')
            if '%s' in description:
                description = description % role.content_type.model

            role_definition, created = RoleDefinition.objects.get_or_create(
                name=role_definition_name,
                defaults={'description': description, 'content_type_id': role.content_type_id, 'created_on': migration_time, 'modified_on': migration_time},
            )

            if created:
                logger.info(f'Created custom Role Definition {role_definition_name}, pk={role_definition.pk}')
                role_definition.permissions.set(perm_list)

        # Create the object role and add users to it
        give_permissions(
            apps,
            role_definition,
            users=role.members.all(),
            teams=[tr.object_id for tr in team_roles],
            object_id=role.object_id,
            content_type_id=role.content_type_id,
        )

    # Create new replacement system auditor role
    new_system_auditor, created = RoleDefinition.objects.get_or_create(
        name='System Auditor',
        defaults={
            'description': 'Migrated singleton role giving read permission to everything',
            'managed': True,
            'created_on': migration_time,
            'modified_on': migration_time,
        },
    )
    new_system_auditor.permissions.add(*list(Permission.objects.filter(codename__startswith='view')))

    # migrate is_system_auditor flag, because it is no longer handled by a system role
    old_system_auditor = Role.objects.filter(singleton_name='system_auditor').first()
    if old_system_auditor:
        # if the system auditor role is not present, this is a new install and no users should exist
        ct = 0
        for user in role.members.all():
            RoleUserAssignment.objects.create(user=user, role_definition=new_system_auditor)
            ct += 1
        if ct:
            logger.info(f'Migrated {ct} users to new system auditor flag')
