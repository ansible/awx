from collections import defaultdict

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
