from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='host',
            index=models.Index(
                Lower('name'),
                name='main_host_name_lower_idx',
            ),
        ),
    ]
