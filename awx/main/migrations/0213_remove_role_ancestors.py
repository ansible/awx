from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0212_create_metrics_utility_functions'),
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
