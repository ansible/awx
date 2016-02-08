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


def unmigrate_organization(apps, schema_editor):
    pass
