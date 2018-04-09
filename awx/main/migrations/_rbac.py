import logging
from time import time

from django.utils.encoding import smart_text
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError

from collections import defaultdict
from awx.main.utils import getattrd
from awx.main.models.rbac import Role, batch_role_ancestor_rebuilding

logger = logging.getLogger('rbac_migrations')

def create_roles(apps, schema_editor):
    '''
    Implicit role creation happens in our post_save hook for all of our
    resources. Here we iterate through all of our resource types and call
    .save() to ensure all that happens for every object in the system before we
    get busy with the actual migration work.

    This gets run after migrate_users, which does role creation for users a
    little differently.
    '''

    models = [
        apps.get_model('main', m) for m in [
            'Organization',
            'Team',
            'Inventory',
            'Project',
            'Credential',
            'CustomInventoryScript',
            'JobTemplate',
        ]
    ]

    with batch_role_ancestor_rebuilding():
        for model in models:
            for obj in model.objects.iterator():
                obj.save()


def migrate_users(apps, schema_editor):
    User = apps.get_model('auth', "User")
    Role = apps.get_model('main', "Role")
    ContentType = apps.get_model('contenttypes', "ContentType")
    user_content_type = ContentType.objects.get_for_model(User)

    for user in User.objects.iterator():
        user.save()
        try:
            Role.objects.get(content_type=user_content_type, object_id=user.id)
            logger.info(smart_text(u"found existing role for user: {}".format(user.username)))
        except Role.DoesNotExist:
            role = Role.objects.create(
                role_field='admin_role',
                content_type = user_content_type,
                object_id = user.id
            )
            role.members.add(user)
            logger.info(smart_text(u"migrating to new role for user: {}".format(user.username)))

        if user.is_superuser:
            if Role.objects.filter(singleton_name='system_administrator').exists():
                sa_role = Role.objects.get(singleton_name='system_administrator')
            else:
                sa_role = Role.objects.create(
                    singleton_name='system_administrator',
                    role_field='system_administrator'
                )

            sa_role.members.add(user)
            logger.warning(smart_text(u"added superuser: {}".format(user.username)))

def migrate_organization(apps, schema_editor):
    Organization = apps.get_model('main', "Organization")
    for org in Organization.objects.iterator():
        for admin in org.deprecated_admins.all():
            org.admin_role.members.add(admin)
            logger.info(smart_text(u"added admin: {}, {}".format(org.name, admin.username)))
        for user in org.deprecated_users.all():
            org.member_role.members.add(user)
            logger.info(smart_text(u"added member: {}, {}".format(org.name, user.username)))

def migrate_team(apps, schema_editor):
    Team = apps.get_model('main', 'Team')
    for t in Team.objects.iterator():
        for user in t.deprecated_users.all():
            t.member_role.members.add(user)
            logger.info(smart_text(u"team: {}, added user: {}".format(t.name, user.username)))

def attrfunc(attr_path):
    '''attrfunc returns a function that will
    attempt to use the attr_path to access the attribute
    of an instance that is passed in to the returned function.

    Example:
        get_org = attrfunc('inventory.organization')
        org = get_org(JobTemplateInstance)
    '''
    def attr(inst):
        return getattrd(inst, attr_path)
    return attr

def _update_credential_parents(org, cred):
    cred.organization = org
    cred.save()

def _discover_credentials(instances, cred, orgfunc):
    '''_discover_credentials will find shared credentials across
    organizations. If a shared credential is found, it will duplicate
    the credential, ensure the proper role permissions are added to the new
    credential, and update any references from the old to the newly created
    credential.

    instances is a list of all objects that were matched when filtered
    with cred.

    orgfunc is a function that when called with an instance from instances
    will produce an Organization object.
    '''
    orgs = defaultdict(list)
    for inst in instances:
        try:
            orgs[orgfunc(inst)].append(inst)
        except AttributeError:
            # JobTemplate.inventory can be NULL sometimes, eg when an inventory
            # has been deleted. This protects against that.
            pass

    if len(orgs) == 1:
        try:
            _update_credential_parents(orgfunc(instances[0]), cred)
        except AttributeError:
            # JobTemplate.inventory can be NULL sometimes, eg when an inventory
            # has been deleted. This protects against that.
            pass
    else:
        for pos, org in enumerate(orgs):
            if pos == 0:
                _update_credential_parents(org, cred)
            else:
                # Create a new credential
                cred.pk = None
                cred.organization = None
                cred.save()

                cred.admin_role, cred.use_role = None, None

                for i in orgs[org]:
                    i.credential = cred
                    i.save()

                _update_credential_parents(org, cred)

def migrate_credential(apps, schema_editor):
    Credential = apps.get_model('main', "Credential")
    JobTemplate = apps.get_model('main', 'JobTemplate')
    Project = apps.get_model('main', 'Project')
    InventorySource = apps.get_model('main', 'InventorySource')

    for cred in Credential.objects.iterator():
        results = [x for x in JobTemplate.objects.filter(Q(credential=cred) | Q(cloud_credential=cred), inventory__isnull=False).all()] + \
                  [x for x in InventorySource.objects.filter(credential=cred).all()]
        if cred.deprecated_team is not None and results:
            if len(results) == 1:
                _update_credential_parents(results[0].inventory.organization, cred)
            else:
                _discover_credentials(results, cred, attrfunc('inventory.organization'))
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at organization level".format(cred.name, cred.kind, cred.host)))

        projs = Project.objects.filter(credential=cred).all()
        if cred.deprecated_team is not None and projs:
            if len(projs) == 1:
                _update_credential_parents(projs[0].organization, cred)
            else:
                _discover_credentials(projs, cred, attrfunc('organization'))
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at organization level".format(cred.name, cred.kind, cred.host)))

        if cred.deprecated_team is not None:
            cred.deprecated_team.admin_role.children.add(cred.admin_role)
            cred.deprecated_team.member_role.children.add(cred.use_role)
            cred.save()
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at user level".format(cred.name, cred.kind, cred.host)))
        elif cred.deprecated_user is not None:
            cred.admin_role.members.add(cred.deprecated_user)
            cred.save()
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at user level".format(cred.name, cred.kind, cred.host, )))
        else:
            logger.warning(smart_text(u"orphaned credential found Credential(name={}, kind={}, host={}), superuser only".format(cred.name, cred.kind, cred.host, )))


def migrate_inventory(apps, schema_editor):
    Inventory = apps.get_model('main', 'Inventory')
    Permission = apps.get_model('main', 'Permission')

    def role_from_permission(perm):
        if perm.permission_type == 'admin':
            return inventory.admin_role
        elif perm.permission_type == 'read':
            return inventory.read_role
        elif perm.permission_type == 'write':
            return inventory.update_role
        elif perm.permission_type == 'check' or perm.permission_type == 'run' or perm.permission_type == 'create':
            # These permission types are handled differntly in RBAC now, nothing to migrate.
            return False
        else:
            return None

    for inventory in Inventory.objects.iterator():
        for perm in Permission.objects.filter(inventory=inventory):
            role = None
            execrole = None

            role = role_from_permission(perm)
            if role is None:
                raise Exception(smart_text(u'Unhandled permission type for inventory: {}'.format( perm.permission_type)))

            if perm.run_ad_hoc_commands:
                execrole = inventory.use_role

            if perm.team:
                if role:
                    perm.team.member_role.children.add(role)
                if execrole:
                    perm.team.member_role.children.add(execrole)
                logger.info(smart_text(u'added Team({}) access to Inventory({})'.format(perm.team.name, inventory.name)))

            if perm.user:
                if role:
                    role.members.add(perm.user)
                if execrole:
                    execrole.members.add(perm.user)
                logger.info(smart_text(u'added User({}) access to Inventory({})'.format(perm.user.username, inventory.name)))

def migrate_projects(apps, schema_editor):
    '''
    I can see projects when:
     X I am a superuser.
     X I am an admin in an organization associated with the project.
     X I am a user in an organization associated with the project.
     X I am on a team associated with the project.
     X I have been explicitly granted permission to run/check jobs using the
       project.
     X I created the project but it isn't associated with an organization
    I can change/delete when:
     X I am a superuser.
     X I am an admin in an organization associated with the project.
     X I created the project but it isn't associated with an organization
    '''
    Project = apps.get_model('main', 'Project')
    Permission = apps.get_model('main', 'Permission')
    JobTemplate = apps.get_model('main', 'JobTemplate')

    # Migrate projects to single organizations, duplicating as necessary
    for project in Project.objects.iterator():
        original_project_name = project.name
        project_orgs = project.deprecated_organizations.distinct().all()

        if len(project_orgs) >= 1:
            first_org = None
            for org in project_orgs:
                if first_org is None:
                    # For the first org, re-use our existing Project object, so don't do the below duplication effort
                    first_org = org
                    if len(project_orgs) > 1:
                        project.name = smart_text(u'{} - {}'.format(first_org.name, original_project_name))
                    project.organization = first_org
                    project.save()
                else:
                    new_prj = Project.objects.create(
                        created                   = project.created,
                        modified                  = project.modified,
                        polymorphic_ctype_id      = project.polymorphic_ctype_id,
                        description               = project.description,
                        name                      = smart_text(u'{} - {}'.format(org.name, original_project_name)),
                        old_pk                    = project.old_pk,
                        created_by_id             = project.created_by_id,
                        modified_by_id            = project.modified_by_id,
                        scm_type                  = project.scm_type,
                        scm_url                   = project.scm_url,
                        scm_branch                = project.scm_branch,
                        scm_clean                 = project.scm_clean,
                        scm_delete_on_update      = project.scm_delete_on_update,
                        scm_delete_on_next_update = project.scm_delete_on_next_update,
                        scm_update_on_launch      = project.scm_update_on_launch,
                        scm_update_cache_timeout  = project.scm_update_cache_timeout,
                        credential                = project.credential,
                        organization              = org
                    )
                    if project.scm_type == "":
                        new_prj.local_path = project.local_path
                        new_prj.save()
                    for team in project.deprecated_teams.iterator():
                        new_prj.deprecated_teams.add(team)
                    logger.warning(smart_text(u'cloning Project({}) onto {} as Project({})'.format(original_project_name, org, new_prj)))
                    job_templates = JobTemplate.objects.filter(project=project, inventory__organization=org).all()
                    for jt in job_templates:
                        jt.project = new_prj
                        jt.save()
                    for perm in Permission.objects.filter(project=project):
                        Permission.objects.create(
                            created                   = perm.created,
                            modified                  = perm.modified,
                            created_by                = perm.created_by,
                            modified_by               = perm.modified_by,
                            description               = perm.description,
                            name                      = perm.name,
                            user                      = perm.user,
                            team                      = perm.team,
                            project                   = new_prj,
                            inventory                 = perm.inventory,
                            permission_type           = perm.permission_type,
                            run_ad_hoc_commands       = perm.run_ad_hoc_commands,
                        )

    # Migrate permissions
    for project in Project.objects.iterator():
        if project.organization is None and project.created_by is not None:
            project.admin_role.members.add(project.created_by)
            logger.warn(smart_text(u'adding Project({}) admin: {}'.format(project.name, project.created_by.username)))

        for team in project.deprecated_teams.all():
            team.member_role.children.add(project.read_role)
            logger.info(smart_text(u'adding Team({}) access for Project({})'.format(team.name, project.name)))

        for perm in Permission.objects.filter(project=project):
            if perm.permission_type == 'create':
                role = project.use_role
            else:
                role = project.read_role

            if perm.team:
                perm.team.member_role.children.add(role)
                logger.info(smart_text(u'adding Team({}) access for Project({})'.format(perm.team.name, project.name)))

            if perm.user:
                role.members.add(perm.user)
                logger.info(smart_text(u'adding User({}) access for Project({})'.format(perm.user.username, project.name)))

        if project.organization is not None:
            for user in project.organization.deprecated_users.all():
                if not (project.use_role.members.filter(pk=user.id).exists() or project.admin_role.members.filter(pk=user.id).exists()):
                    project.read_role.members.add(user)
                    logger.info(smart_text(u'adding Organization({}) member access to Project({})'.format(project.organization.name, project.name)))



def migrate_job_templates(apps, schema_editor):
    '''
    NOTE: This must be run after orgs, inventory, projects, credential, and
    users have been migrated
    '''


    '''
    I can see job templates when:
     X I am a superuser.
     - I can read the inventory, project and credential (which means I am an
       org admin or member of a team with access to all of the above).
     - I have permission explicitly granted to check/deploy with the inventory
       and project.


    #This does not mean I would be able to launch a job from the template or
    #edit the template.
     - access.py can_read for JobTemplate enforces that you can only
       see it if you can launch it, so the above imply launch too
    '''


    '''
    Tower administrators, organization administrators, and project
    administrators, within a project under their purview, may create and modify
    new job templates for that project.

    When editing a job template, they may select among the inventory groups and
    credentials in the organization for which they have usage permissions, or
    they may leave either blank to be selected at runtime.

    Additionally, they may specify one or more users/teams that have execution
    permission for that job template, among the users/teams that are a member
    of that project.

    That execution permission is valid irrespective of any explicit permissions
    the user has or has not been granted to the inventory group or credential
    specified in the job template.

    '''

    User = apps.get_model('auth', 'User')
    JobTemplate = apps.get_model('main', 'JobTemplate')
    Team = apps.get_model('main', 'Team')
    Permission = apps.get_model('main', 'Permission')
    Credential = apps.get_model('main', 'Credential')

    jt_queryset = JobTemplate.objects.select_related('inventory', 'project', 'inventory__organization', 'execute_role')

    for jt in jt_queryset.iterator():
        if jt.inventory is None:
            # If inventory is None, then only system admins and org admins can
            # do anything with the JT in 2.4
            continue

        jt_permission_qs = Permission.objects.filter(
            inventory=jt.inventory,
            project=jt.project,
        )

        inventory_permission_qs = Permission.objects.filter(
            inventory=jt.inventory,
            project__isnull=True,
        )

        team_create_permissions = set(
            jt_permission_qs
            .filter(permission_type__in=['create'])
            .values_list('team__id', flat=True)
        )
        team_run_permissions = set(
            jt_permission_qs
            .filter(permission_type__in=['check', 'run'] if jt.job_type == 'check' else ['run'])
            .values_list('team__id', flat=True)
        )
        user_create_permissions = set(
            jt_permission_qs
            .filter(permission_type__in=['create'])
            .values_list('user__id', flat=True)
        )
        user_run_permissions = set(
            jt_permission_qs
            .filter(permission_type__in=['check', 'run'] if jt.job_type == 'check' else ['run'])
            .values_list('user__id', flat=True)
        )

        team_inv_permissions = defaultdict(set)
        user_inv_permissions = defaultdict(set)

        for user_id, team_id, inventory_id in inventory_permission_qs.values_list('user_id', 'team_id', 'inventory_id'):
            if user_id:
                user_inv_permissions[user_id].add(inventory_id)
            if team_id:
                team_inv_permissions[team_id].add(inventory_id)


        for team in Team.objects.filter(id__in=team_create_permissions).iterator():
            if jt.inventory.id in team_inv_permissions[team.id] and \
                ((not jt.credential and not jt.cloud_credential) or
                    Credential.objects.filter(deprecated_team=team, jobtemplates=jt).exists()):
                team.member_role.children.add(jt.admin_role)
                logger.info(smart_text(u'transfering admin access on JobTemplate({}) to Team({})'.format(jt.name, team.name)))
        for team in Team.objects.filter(id__in=team_run_permissions).iterator():
            if jt.inventory.id in team_inv_permissions[team.id] and \
               ((not jt.credential and not jt.cloud_credential) or
                    Credential.objects.filter(deprecated_team=team, jobtemplates=jt).exists()):
                team.member_role.children.add(jt.execute_role)
                logger.info(smart_text(u'transfering execute access on JobTemplate({}) to Team({})'.format(jt.name, team.name)))

        for user in User.objects.filter(id__in=user_create_permissions).iterator():
            cred = jt.credential or jt.cloud_credential
            if (jt.inventory.id in user_inv_permissions[user.id] or
                    any([jt.inventory.id in team_inv_permissions[team.id] for team in user.deprecated_teams.all()])) and \
                    (not cred or cred.deprecated_user == user or
                        (cred.deprecated_team and cred.deprecated_team.deprecated_users.filter(pk=user.id).exists())):
                jt.admin_role.members.add(user)
                logger.info(smart_text(u'transfering admin access on JobTemplate({}) to User({})'.format(jt.name, user.username)))
        for user in User.objects.filter(id__in=user_run_permissions).iterator():
            cred = jt.credential or jt.cloud_credential

            if (jt.inventory.id in user_inv_permissions[user.id] or
                    any([jt.inventory.id in team_inv_permissions[team.id] for team in user.deprecated_teams.all()])) and \
                    (not cred or cred.deprecated_user == user or
                        (cred.deprecated_team and cred.deprecated_team.deprecated_users.filter(pk=user.id).exists())):
                jt.execute_role.members.add(user)
                logger.info(smart_text(u'transfering execute access on JobTemplate({}) to User({})'.format(jt.name, user.username)))



def rebuild_role_hierarchy(apps, schema_editor):
        logger.info('Computing role roots..')
        start = time()
        roots = Role.objects \
                    .all() \
                    .values_list('id', flat=True)
        stop = time()
        logger.info('Found %d roots in %f seconds, rebuilding ancestry map' % (len(roots), stop - start))
        start = time()
        Role.rebuild_role_ancestor_list(roots, [])
        stop = time()
        logger.info('Rebuild completed in %f seconds' % (stop - start))
        logger.info('Done.')


def infer_credential_org_from_team(apps, schema_editor):
    Credential = apps.get_model('main', "Credential")
    for cred in Credential.objects.exclude(deprecated_team__isnull=True):
        try:
            with transaction.atomic():
                _update_credential_parents(cred.deprecated_team.organization, cred)
        except IntegrityError:
            logger.info("Organization<{}> credential for old Team<{}> credential already created".format(cred.deprecated_team.organization.pk, cred.pk))


def delete_all_user_roles(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', "ContentType")
    Role = apps.get_model('main', "Role")
    User = apps.get_model('auth', "User")
    user_content_type = ContentType.objects.get_for_model(User)
    for role in Role.objects.filter(content_type=user_content_type).iterator():
        role.delete()
