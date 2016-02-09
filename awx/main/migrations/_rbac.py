from collections import defaultdict

def migrate_users(apps, schema_editor):
    migrations = list()
    User = apps.get_model('auth', "User")
    Role = apps.get_model('main', "Role")
    for user in User.objects.all():
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
        for perm in Permission.objects.filter(inventory=inventory):
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
