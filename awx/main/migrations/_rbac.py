import logging

from django.utils.encoding import smart_text
from django.db.models import Q
from django.utils.timezone import now

from collections import defaultdict
from awx.main.utils import getattrd, set_current_apps

import _old_access as old_access
logger = logging.getLogger(__name__)

def log_migration(wrapped):
    '''setup the logging mechanism for each migration method
    as it runs, Django resets this, so we use a decorator
    to re-add the handler for each method.
    '''
    handler = logging.FileHandler("/tmp/tower_rbac_migrations.log", mode="a", encoding="UTF-8")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    def wrapper(*args, **kwargs):
        logger.handlers = []
        logger.addHandler(handler)
        return wrapped(*args, **kwargs)
    return wrapper

@log_migration
def init_rbac_migration(apps, schema_editor):
    set_current_apps(apps)

@log_migration
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

@log_migration
def migrate_organization(apps, schema_editor):
    Organization = apps.get_model('main', "Organization")
    for org in Organization.objects.iterator():
        org.save() # force creates missing roles
        for admin in org.deprecated_admins.all():
            org.admin_role.members.add(admin)
            logger.info(smart_text(u"added admin: {}, {}".format(org.name, admin.username)))
        for user in org.deprecated_users.all():
            org.auditor_role.members.add(user)
            logger.info(smart_text(u"added auditor: {}, {}".format(org.name, user.username)))

@log_migration
def migrate_team(apps, schema_editor):
    Team = apps.get_model('main', 'Team')
    for t in Team.objects.iterator():
        t.save()
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
    org.admin_role.children.add(cred.owner_role)
    org.member_role.children.add(cred.use_role)
    cred.deprecated_user, cred.deprecated_team = None, None
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
        orgs[orgfunc(inst)].append(inst)

    if len(orgs) == 1:
        _update_credential_parents(orgfunc(instances[0]), cred)
    else:
        for pos, org in enumerate(orgs):
            if pos == 0:
                _update_credential_parents(org, cred)
            else:
                # Create a new credential
                cred.pk = None
                cred.save()

                # Unlink the old information from the new credential
                cred.deprecated_user, cred.deprecated_team = None, None
                cred.owner_role, cred.use_role = None, None
                cred.save()

                for i in orgs[org]:
                    i.credential = cred
                    i.save()
                _update_credential_parents(org, cred)

@log_migration
def migrate_credential(apps, schema_editor):
    Credential = apps.get_model('main', "Credential")
    JobTemplate = apps.get_model('main', 'JobTemplate')
    Project = apps.get_model('main', 'Project')
    Role = apps.get_model('main', 'Role')
    User = apps.get_model('auth', 'User')
    InventorySource = apps.get_model('main', 'InventorySource')
    ContentType = apps.get_model('contenttypes', "ContentType")
    user_content_type = ContentType.objects.get_for_model(User)

    for cred in Credential.objects.iterator():
        cred.save()
        results = (JobTemplate.objects.filter(Q(credential=cred) | Q(cloud_credential=cred)).all() or
                   InventorySource.objects.filter(credential=cred).all())
        if results:
            if len(results) == 1:
                _update_credential_parents(results[0].inventory.organization, cred)
            else:
                _discover_credentials(results, cred, attrfunc('inventory.organization'))
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at organization level".format(cred.name, cred.kind, cred.host)))
            continue

        projs = Project.objects.filter(credential=cred).all()
        if projs:
            if len(projs) == 1:
                _update_credential_parents(projs[0].organization, cred)
            else:
                _discover_credentials(projs, cred, attrfunc('organization'))
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at organization level".format(cred.name, cred.kind, cred.host)))
            continue

        if cred.deprecated_team is not None:
            cred.deprecated_team.admin_role.children.add(cred.owner_role)
            cred.deprecated_team.member_role.children.add(cred.use_role)
            cred.deprecated_user, cred.deprecated_team = None, None
            cred.save()
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at user level".format(cred.name, cred.kind, cred.host)))
        elif cred.deprecated_user is not None:
            user_admin_role = Role.objects.get(content_type=user_content_type, object_id=cred.deprecated_user.id)
            user_admin_role.children.add(cred.owner_role)
            cred.deprecated_user, cred.deprecated_team = None, None
            cred.save()
            logger.info(smart_text(u"added Credential(name={}, kind={}, host={}) at user level".format(cred.name, cred.kind, cred.host, )))
        else:
            logger.warning(smart_text(u"orphaned credential found Credential(name={}, kind={}, host={}), superuser only".format(cred.name, cred.kind, cred.host, )))


@log_migration
def migrate_inventory(apps, schema_editor):
    Inventory = apps.get_model('main', 'Inventory')
    Permission = apps.get_model('main', 'Permission')

    def role_from_permission():
        if perm.permission_type == 'admin':
            return inventory.admin_role
        elif perm.permission_type == 'read':
            return inventory.auditor_role
        elif perm.permission_type == 'write':
            return inventory.update_role
        elif perm.permission_type == 'check' or perm.permission_type == 'run':
            # These permission types are handled differntly in RBAC now, nothing to migrate.
            return False
        else:
            return None

    for inventory in Inventory.objects.iterator():
        inventory.save()
        for perm in Permission.objects.filter(inventory=inventory):
            role = None
            execrole = None

            role = role_from_permission()
            if role is None:
                raise Exception(smart_text(u'Unhandled permission type for inventory: {}'.format( perm.permission_type)))

            if perm.run_ad_hoc_commands:
                execrole = inventory.execute_role

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

@log_migration
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
        project.save()
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
                        description               = project.description,
                        name                      = smart_text(u'{} - {}'.format(org.name, original_project_name)),
                        old_pk                    = project.old_pk,
                        created_by_id             = project.created_by_id,
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
                    logger.warning(smart_text(u'cloning Project({}) onto {} as Project({})'.format(original_project_name, org, new_prj)))
                    job_templates = JobTemplate.objects.filter(inventory__organization=org).all()
                    for jt in job_templates:
                        jt.project = new_prj
                        jt.save()

    # Migrate permissions
    for project in Project.objects.iterator():
        if project.organization is None and project.created_by is not None:
            project.admin_role.members.add(project.created_by)
            logger.warn(smart_text(u'adding Project({}) admin: {}'.format(project.name, project.created_by.username)))

        for team in project.deprecated_teams.all():
            team.member_role.children.add(project.member_role)
            logger.info(smart_text(u'adding Team({}) access for Project({})'.format(team.name, project.name)))

        if project.organization is not None:
            for user in project.organization.deprecated_users.all():
                project.member_role.members.add(user)
                logger.info(smart_text(u'adding Organization({}) member access to Project({})'.format(project.organization.name, project.name)))

        for perm in Permission.objects.filter(project=project):
            # All perms at this level just imply a user or team can read
            if perm.team:
                perm.team.member_role.children.add(project.member_role)
                logger.info(smart_text(u'adding Team({}) access for Project({})'.format(perm.team.name, project.name)))

            if perm.user:
                project.member_role.members.add(perm.user)
                logger.info(smart_text(u'adding User({}) access for Project({})'.format(perm.user.username, project.name)))


@log_migration
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

    for jt in JobTemplate.objects.iterator():
        jt.save()
        permission = Permission.objects.filter(
            inventory=jt.inventory,
            project=jt.project,
            permission_type__in=['create', 'check', 'run'] if jt.job_type == 'check' else ['create', 'run'],
        )

        for team in Team.objects.iterator():
            if permission.filter(team=team).exists():
                team.member_role.children.add(jt.execute_role)
                logger.info(smart_text(u'adding Team({}) access to JobTemplate({})'.format(team.name, jt.name)))

        for user in User.objects.iterator():
            if permission.filter(user=user).exists():
                jt.execute_role.members.add(user)
                logger.info(smart_text(u'adding User({}) access to JobTemplate({})'.format(user.username, jt.name)))

            if user in jt.execute_role:
                # If the job template is already accessible by the user, because they
                # are a sytem, organization, or project admin, then don't add an explicit
                # role entry for them
                continue

            if old_access.check_user_access(user, jt.__class__, 'start', jt, False):
                jt.execute_role.members.add(user)
                logger.info(smart_text(u'adding User({}) access to JobTemplate({})'.format(user.username, jt.name)))
