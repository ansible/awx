from django.db import migrations

ORG_CHILD_ADMIN_ROLES = [
    'Organization Project Admin',
    'Organization Credential Admin',
    'Organization Inventory Admin',
    'Organization NotificationTemplate Admin',
    'Organization WorkflowJobTemplate Admin',
    'Organization ExecutionEnvironment Admin',
]


def add_member_organization_perm(apps, schema_editor):
    """
    Add member_organization permission to Organization *Child* Admin roles.

    Without this permission, users granted these roles receive 403 on create
    (POST) operations even though the specific add_* permission is present.
    See: AAP-82221
    """
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    DABPermission = apps.get_model('dab_rbac', 'DABPermission')

    try:
        DABContentType = apps.get_model('dab_rbac', 'DABContentType')
    except LookupError:
        DABContentType = apps.get_model('contenttypes', 'ContentType')

    Organization = apps.get_model('main', 'Organization')
    org_ct = DABContentType.objects.get_for_model(Organization)

    member_perm = DABPermission.objects.filter(codename='member_organization', content_type=org_ct).first()
    if not member_perm:
        return

    for rd in RoleDefinition.objects.filter(name__in=ORG_CHILD_ADMIN_ROLES, managed=True):
        rd.permissions.add(member_perm)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0207_alter_skip_tags_to_textfield'),
    ]

    operations = [
        migrations.RunPython(add_member_organization_perm, migrations.RunPython.noop),
    ]
