from django.db import connection, transaction, reset_queries
from django.db.transaction import TransactionManagementError
from django.contrib.contenttypes.models import ContentType

from collections import defaultdict
import _old_access as old_access

def migrate_users(apps, schema_editor):
    migrations = list()

    User = apps.get_model('auth', "User")
    Role = apps.get_model('main', "Role")
    RolePermission = apps.get_model('main', "RolePermission")

    for user in User.objects.all():
        try:
            Role.objects.get(content_type=ContentType.objects.get_for_model(User), object_id=user.id)
        except Role.DoesNotExist:
            role = Role.objects.create(
                singleton_name = '%s-admin_role' % user.username,
                content_object = user,
            )
            role.members.add(user)
            RolePermission.objects.create(
                role = role,
                resource = user,
                create=1, read=1, write=1, delete=1, update=1,
                execute=1, scm_update=1, use=1,
            )

        if user.is_superuser:
            Role.singleton('System Administrator').members.add(user)
            migrations.append(user)
    return migrations

def migrate_organization(apps, schema_editor):
    migrations = defaultdict(list)
    organization = apps.get_model('main', "Organization")
    for org in organization.objects.all():
        for admin in org.admins.all():
            org.admin_role.members.add(admin)
            migrations[org.name].append(admin)
        for user in org.users.all():
            org.auditor_role.members.add(user)
            migrations[org.name].append(user)
    return migrations

def migrate_team(apps, schema_editor):
    migrations = defaultdict(list)
    team = apps.get_model('main', 'Team')
    for t in team.objects.all():
        for user in t.users.all():
            t.member_role.members.add(user)
            migrations[t.name].append(user)
    return migrations

def migrate_credential(apps, schema_editor):
    migrations = defaultdict(list)
    credential = apps.get_model('main', "Credential")
    for cred in credential.objects.all():
        if cred.user:
            cred.owner_role.members.add(cred.user)
            migrations[cred.name].append(cred.user)
        elif cred.team:
            cred.owner_role.parents.add(cred.team.admin_role)
            cred.usage_role.parents.add(cred.team.member_role)
            migrations[cred.name].append(cred.team)
    return migrations

def migrate_inventory(apps, schema_editor):
    migrations = defaultdict(dict)

    Inventory = apps.get_model('main', 'Inventory')
    Permission = apps.get_model('main', 'Permission')

    for inventory in Inventory.objects.all():
        teams, users = [], []
        for perm in Permission.objects.filter(inventory=inventory, active=True):
            role = None
            execrole = None
            if perm.permission_type == 'admin':
                role = inventory.admin_role
                pass
            elif perm.permission_type == 'read':
                role = inventory.auditor_role
                pass
            elif perm.permission_type == 'write':
                role = inventory.updater_role
                pass
            elif perm.permission_type == 'check':
                pass
            elif perm.permission_type == 'run':
                pass
            else:
                raise Exception('Unhandled permission type for inventory: %s' % perm.permission_type)
            if perm.run_ad_hoc_commands:
                execrole = inventory.executor_role

            if perm.team:
                if role:
                    perm.team.member_role.children.add(role)
                if execrole:
                    perm.team.member_role.children.add(execrole)

                teams.append(perm.team)

            if perm.user:
                if role:
                    role.members.add(perm.user)
                if execrole:
                    execrole.members.add(perm.user)
                users.append(perm.user)
        migrations[inventory.name]['teams'] = teams
        migrations[inventory.name]['users'] = users
    return migrations

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
    migrations = defaultdict(lambda: defaultdict(set))

    Project = apps.get_model('main', 'Project')
    Permission = apps.get_model('main', 'Permission')
    JobTemplate = apps.get_model('main', 'JobTemplate')

    # Migrate projects to single organizations, duplicating as necessary
    for project in [p for p in Project.objects.all()]:
        original_project_name = project.name
        project_orgs = project.deprecated_organizations.distinct().all()

        if project_orgs.count() > 1:
            first_org = None
            for org in project_orgs:
                if first_org is None:
                    # For the first org, re-use our existing Project object, so don't do the below duplication effort
                    first_org = org
                    project.name = first_org.name + ' - ' + original_project_name
                    project.organization = first_org
                    project.save()
                else:
                    print('Fork to %s ' % (org.name + ' - ' + original_project_name))
                    new_prj = Project.objects.create(
                        created                   = project.created,
                        description               = project.description,
                        name                      = org.name + ' - ' + original_project_name,
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
                    migrations[original_project_name]['projects'].add(new_prj)
                    job_templates = JobTemplate.objects.filter(inventory__organization=org).all()
                    for jt in job_templates:
                        jt.project = new_prj
                        print('Updating jt to point to %s' % repr(new_prj))
                        jt.save()

    # Migrate permissions
    for project in [p for p in Project.objects.all()]:
        if project.organization is not None and project.created_by is not None:
            project.admin_role.members.add(project.created_by)
            migrations[original_project_name]['users'].add(project.created_by)

        for team in project.teams.all():
            team.member_role.children.add(project.member_role)
            migrations[original_project_name]['teams'].add(team)

        if project.organization is not None:
            for user in project.organization.member_role.members.all():
                project.member_role.members.add(user)
                migrations[original_project_name]['users'].add(user)

        for perm in Permission.objects.filter(project=project, active=True):
            # All perms at this level just imply a user or team can read
            if perm.team:
                perm.team.member_role.children.add(project.member_role)
                migrations[original_project_name]['teams'].add(perm.team)

            if perm.user:
                project.member_role.members.add(perm.user)
                migrations[original_project_name]['users'].add(perm.user)

    return migrations



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

    migrations = defaultdict(lambda: defaultdict(set))

    User = apps.get_model('auth', 'User')
    JobTemplate = apps.get_model('main', 'JobTemplate')
    Team = apps.get_model('main', 'Team')
    Permission = apps.get_model('main', 'Permission')

    for jt in JobTemplate.objects.all():
        permission = Permission.objects.filter(
            inventory=jt.inventory,
            project=jt.project,
            active=True,
            permission_type__in=['create', 'check', 'run'] if jt.job_type == 'check' else ['create', 'run'],
        )

        for team in Team.objects.all():
            if permission.filter(team=team).exists():
                team.member_role.children.add(jt.executor_role)
                migrations[jt.name]['teams'].add(team)


        for user in User.objects.all():
            if permission.filter(user=user).exists():
                jt.executor_role.members.add(user)
                migrations[jt.name]['users'].add(user)

            if jt.accessible_by(user, {'execute': True}):
                # If the job template is already accessible by the user, because they
                # are a sytem, organization, or project admin, then don't add an explicit
                # role entry for them
                continue

            if old_access.check_user_access(user, jt.__class__, 'start', jt, False):
                jt.executor_role.members.add(user)
                migrations[jt.name]['users'].add(user)


    return migrations
