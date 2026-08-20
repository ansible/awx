from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0208_fix_system_auditor_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='host',
            name='last_job',
        ),
        migrations.RemoveField(
            model_name='host',
            name='last_job_host_summary',
        ),
    ]
