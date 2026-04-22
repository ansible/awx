from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
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
