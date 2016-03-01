from collections import defaultdict
import _old_access as old_access

def migrate_users(apps, schema_editor):
    migrations = list()
    User = apps.get_model('auth', "User")
    Role = apps.get_model('main', "Role")

    for user in User.objects.all():
        ur = user.resource # implicitly creates the UserResource field if it didn't already exist
        ur.admin_role.members.add(user)

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

    for project in Project.objects.all():
        if project.organizations.count() == 0 and project.created_by is not None:
            project.admin_role.members.add(project.created_by)
            migrations[project.name]['users'].add(project.created_by)

        for team in project.teams.all():
            team.member_role.children.add(project.member_role)
            migrations[project.name]['teams'].add(team)

        if project.organizations.count() > 0:
            for org in project.organizations.all():
                for user in org.users.all():
                    project.member_role.members.add(user)
                    migrations[project.name]['users'].add(user)

        for perm in Permission.objects.filter(project=project, active=True):
            # All perms at this level just imply a user or team can read
            if perm.team:
                perm.team.member_role.children.add(project.member_role)
                migrations[project.name]['teams'].add(perm.team)

            if perm.user:
                project.member_role.members.add(perm.user)
                migrations[project.name]['users'].add(perm.user)

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
                jt.exector_role.members.add(user)
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
