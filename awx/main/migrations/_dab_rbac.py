import json
import logging
from collections import defaultdict

from django.apps import apps as global_apps
from django.db.models import ForeignKey
from django.conf import settings
from ansible_base.rbac.migrations._utils import give_permissions
from ansible_base.rbac.management import create_dab_permissions

from awx.main.fields import ImplicitRoleField
from awx.main.constants import role_name_to_perm_mapping

from ansible_base.rbac.permission_registry import permission_registry


logger = logging.getLogger('awx.main.migrations._dab_rbac')


def create_permissions_as_operation(apps, schema_editor):
    logger.info('Running data migration create_permissions_as_operation')
    # NOTE: the DAB ContentType changes adjusted how they fire
    # before they would fire on every app config, like contenttypes
    create_dab_permissions(global_apps.get_app_config("main"), apps=apps)
    # This changed to only fire once and do a global creation
    # so we need to call it for specifically the dab_rbac app
    # multiple calls will not hurt anything
    create_dab_permissions(global_apps.get_app_config("dab_rbac"), apps=apps)


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
    try:
        # After migration for remote permissions
        ContentType = apps.get_model('dab_rbac', 'DABContentType')
    except LookupError:
        # If using DAB from before remote permissions are implemented
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
        perm_list.append(Permission.objects.get(codename='view_notificationtemplate'))

    return perm_list


def model_class(ct, apps):
    """
    You can not use model methods in migrations, so this duplicates
    what ContentType.model_class does, using current apps
    """
    try:
        return apps.get_model(ct.app_label, ct.model)
    except LookupError:
        return None


def migrate_to_new_rbac(apps, schema_editor):
    """
    This method moves the assigned permissions from the old rbac.py models
    to the new RoleDefinition and ObjectRole models
    """
    logger.info('Running data migration migrate_to_new_rbac')
    Role = apps.get_model('main', 'Role')
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    RoleUserAssignment = apps.get_model('dab_rbac', 'RoleUserAssignment')
    Permission = apps.get_model('dab_rbac', 'DABPermission')

    if Permission.objects.count() == 0:
        raise RuntimeError('Running migrate_to_new_rbac requires DABPermission objects created first')

    # remove add premissions that are not valid for migrations from old versions
    for perm_str in ('add_organization', 'add_jobtemplate'):
        perm = Permission.objects.filter(codename=perm_str).first()
        if perm:
            perm.delete()

    managed_definitions = dict()
    for role_definition in RoleDefinition.objects.filter(managed=True).exclude(name__in=(settings.ANSIBLE_BASE_JWT_MANAGED_ROLES)):
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
            role_definition_name = f'{model_class(role.content_type, apps).__name__} {action.title()}'

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
                defaults={'description': description, 'content_type_id': role.content_type_id},
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
        name='Platform Auditor',
        defaults={'description': 'Migrated singleton role giving read permission to everything', 'managed': True},
    )
    new_system_auditor.permissions.add(*list(Permission.objects.filter(codename__startswith='view')))

    if created:
        logger.info(f'Created RoleDefinition {new_system_auditor.name} pk={new_system_auditor.pk} with {new_system_auditor.permissions.count()} permissions')

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


def get_or_create_managed(name, description, ct, permissions, RoleDefinition):
    role_definition, created = RoleDefinition.objects.get_or_create(name=name, defaults={'managed': True, 'description': description, 'content_type': ct})
    role_definition.permissions.set(list(permissions))

    if not role_definition.managed:
        role_definition.managed = True
        role_definition.save(update_fields=['managed'])

    if created:
        logger.info(f'Created RoleDefinition {role_definition.name} pk={role_definition} with {len(permissions)} permissions')

    return role_definition


def setup_managed_role_definitions(apps, schema_editor):
    """
    Idempotent method to create or sync the managed role definitions
    """
    logger.info('Running data migration setup_managed_role_definitions')
    to_create = {
        'object_admin': '{cls.__name__} Admin',
        'org_admin': 'Organization Admin',
        'org_children': 'Organization {cls.__name__} Admin',
        'special': '{cls.__name__} {action}',
    }

    try:
        # After migration for remote permissions
        ContentType = apps.get_model('dab_rbac', 'DABContentType')
    except LookupError:
        # If using DAB from before remote permissions are implemented
        ContentType = apps.get_model('contenttypes', 'ContentType')

    Permission = apps.get_model('dab_rbac', 'DABPermission')
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    Organization = apps.get_model(settings.ANSIBLE_BASE_ORGANIZATION_MODEL)
    org_ct = ContentType.objects.get_for_model(Organization)
    managed_role_definitions = []

    org_perms = set()
    for cls in permission_registry.all_registered_models:
        ct = ContentType.objects.get_for_model(cls)
        cls_name = cls._meta.model_name
        object_perms = set(Permission.objects.filter(content_type=ct))
        # Special case for InstanceGroup which has an organiation field, but is not an organization child object
        if cls_name != 'instancegroup':
            org_perms.update(object_perms)

        if 'object_admin' in to_create and cls_name != 'organization':
            indiv_perms = object_perms.copy()
            add_perms = [perm for perm in indiv_perms if perm.codename.startswith('add_')]
            if add_perms:
                for perm in add_perms:
                    indiv_perms.remove(perm)

            managed_role_definitions.append(
                get_or_create_managed(
                    to_create['object_admin'].format(cls=cls), f'Has all permissions to a single {cls._meta.verbose_name}', ct, indiv_perms, RoleDefinition
                )
            )

        if 'org_children' in to_create and (cls_name not in ('organization', 'instancegroup', 'team')):
            org_child_perms = object_perms.copy()
            org_child_perms.add(Permission.objects.get(codename='view_organization'))

            managed_role_definitions.append(
                get_or_create_managed(
                    to_create['org_children'].format(cls=cls),
                    f'Has all permissions to {cls._meta.verbose_name_plural} within an organization',
                    org_ct,
                    org_child_perms,
                    RoleDefinition,
                )
            )

        if 'special' in to_create:
            special_perms = []
            for perm in object_perms:
                # Organization auditor is handled separately
                if perm.codename.split('_')[0] not in ('add', 'change', 'delete', 'view', 'audit'):
                    special_perms.append(perm)
            for perm in special_perms:
                action = perm.codename.split('_')[0]
                view_perm = Permission.objects.get(content_type=ct, codename__startswith='view_')
                perm_list = [perm, view_perm]
                # Handle special-case where adhoc role also listed use permission
                if action == 'adhoc':
                    for other_perm in object_perms:
                        if other_perm.codename == 'use_inventory':
                            perm_list.append(other_perm)
                            break
                managed_role_definitions.append(
                    get_or_create_managed(
                        to_create['special'].format(cls=cls, action=action.title()),
                        f'Has {action} permissions to a single {cls._meta.verbose_name}',
                        ct,
                        perm_list,
                        RoleDefinition,
                    )
                )

    if 'org_admin' in to_create:
        managed_role_definitions.append(
            get_or_create_managed(
                to_create['org_admin'].format(cls=Organization),
                'Has all permissions to a single organization and all objects inside of it',
                org_ct,
                org_perms,
                RoleDefinition,
            )
        )

    # Special "organization action" roles
    audit_permissions = [perm for perm in org_perms if perm.codename.startswith('view_')]
    audit_permissions.append(Permission.objects.get(codename='audit_organization'))
    managed_role_definitions.append(
        get_or_create_managed(
            'Organization Audit',
            'Has permission to view all objects inside of a single organization',
            org_ct,
            audit_permissions,
            RoleDefinition,
        )
    )

    org_execute_permissions = {'view_jobtemplate', 'execute_jobtemplate', 'view_workflowjobtemplate', 'execute_workflowjobtemplate', 'view_organization'}
    managed_role_definitions.append(
        get_or_create_managed(
            'Organization Execute',
            'Has permission to execute all runnable objects in the organization',
            org_ct,
            [perm for perm in org_perms if perm.codename in org_execute_permissions],
            RoleDefinition,
        )
    )

    org_approval_permissions = {'view_organization', 'view_workflowjobtemplate', 'approve_workflowjobtemplate'}
    managed_role_definitions.append(
        get_or_create_managed(
            'Organization Approval',
            'Has permission to approve any workflow steps within a single organization',
            org_ct,
            [perm for perm in org_perms if perm.codename in org_approval_permissions],
            RoleDefinition,
        )
    )

    unexpected_role_definitions = RoleDefinition.objects.filter(managed=True).exclude(pk__in=[rd.pk for rd in managed_role_definitions])
    for role_definition in unexpected_role_definitions:
        logger.info(f'Deleting old managed role definition {role_definition.name}, pk={role_definition.pk}')
        role_definition.delete()


def get_team_to_team_relationships(apps, team_member_role):
    """
    Find all team-to-team relationships where one team is a member of another.
    Returns a dict mapping parent_team_id -> [child_team_id, ...]
    """
    team_to_team_relationships = defaultdict(list)

    # Find all team assignments with the Team Member role
    RoleTeamAssignment = apps.get_model('dab_rbac', 'RoleTeamAssignment')
    team_assignments = RoleTeamAssignment.objects.filter(role_definition=team_member_role).select_related('team')

    for assignment in team_assignments:
        parent_team_id = int(assignment.object_id)
        child_team_id = assignment.team.id
        team_to_team_relationships[parent_team_id].append(child_team_id)

    return team_to_team_relationships


def get_all_user_members_of_team(apps, team_member_role, team_id, team_to_team_map, visited=None):
    """
    Recursively find all users who are members of a team, including through nested teams.
    """
    if visited is None:
        visited = set()

    if team_id in visited:
        return set()  # Avoid infinite recursion

    visited.add(team_id)
    all_users = set()

    # Get direct user assignments to this team
    RoleUserAssignment = apps.get_model('dab_rbac', 'RoleUserAssignment')
    user_assignments = RoleUserAssignment.objects.filter(role_definition=team_member_role, object_id=team_id).select_related('user')

    for assignment in user_assignments:
        all_users.add(assignment.user)

    # Get team-to-team assignments and recursively find their users
    child_team_ids = team_to_team_map.get(team_id, [])
    for child_team_id in child_team_ids:
        nested_users = get_all_user_members_of_team(apps, team_member_role, child_team_id, team_to_team_map, visited.copy())
        all_users.update(nested_users)

    return all_users


def remove_team_to_team_assignment(apps, team_member_role, parent_team_id, child_team_id):
    """
    Remove team-to-team memberships.
    """
    Team = apps.get_model('main', 'Team')
    RoleTeamAssignment = apps.get_model('dab_rbac', 'RoleTeamAssignment')

    parent_team = Team.objects.get(id=parent_team_id)
    child_team = Team.objects.get(id=child_team_id)

    # Remove all team-to-team RoleTeamAssignments
    RoleTeamAssignment.objects.filter(role_definition=team_member_role, object_id=parent_team_id, team=child_team).delete()

    # Check mirroring Team model for children under member_role
    parent_team.member_role.children.filter(object_id=child_team_id).delete()


def consolidate_indirect_user_roles(apps, schema_editor):
    """
    A user should have a member role for every team they were indirectly
    a member of. ex. Team A is a member of Team B. All users in Team A
    previously were only members of Team A. They should now be members of
    Team A and Team B.
    """

    # get models for membership on teams
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    Team = apps.get_model('main', 'Team')

    team_member_role = RoleDefinition.objects.get(name='Team Member')

    team_to_team_map = get_team_to_team_relationships(apps, team_member_role)

    if not team_to_team_map:
        return  # No team-to-team relationships to consolidate

    # Get content type for Team - needed for give_permissions
    try:
        from django.contrib.contenttypes.models import ContentType

        team_content_type = ContentType.objects.get_for_model(Team)
    except ImportError:
        # Fallback if ContentType is not available
        ContentType = apps.get_model('contenttypes', 'ContentType')
        team_content_type = ContentType.objects.get_for_model(Team)

    # Get all users who should be direct members of a team
    for parent_team_id, child_team_ids in team_to_team_map.items():
        all_users = get_all_user_members_of_team(apps, team_member_role, parent_team_id, team_to_team_map)

        # Create direct RoleUserAssignments for all users
        if all_users:
            give_permissions(apps=apps, rd=team_member_role, users=list(all_users), object_id=parent_team_id, content_type_id=team_content_type.id)

        # Mirror assignments to Team model
        parent_team = Team.objects.get(id=parent_team_id)
        for user in all_users:
            parent_team.member_role.members.add(user.id)

        # Remove all team-to-team assignments for parent team
        for child_team_id in child_team_ids:
            remove_team_to_team_assignment(apps, team_member_role, parent_team_id, child_team_id)
