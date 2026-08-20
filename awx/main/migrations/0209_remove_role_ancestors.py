from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0208_fix_system_auditor_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='ancestors',
        ),
        migrations.DeleteModel(
            name='RoleAncestorEntry',
        ),
    ]
