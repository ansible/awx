import awx.main.fields
import awx.main.models.notifications
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0125_v410_project_exports'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='export_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AlterField(
            model_name='project',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.auditor_role', 'singleton:system_auditor', 'use_role', 'export_role'], to='main.Role', null='True'),
        ),
    ]
