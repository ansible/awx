from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0210_remove_host_last_job_fields'),
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
