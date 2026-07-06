from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='jobhostsummary',
            index=models.Index(
                fields=['host', '-id'],
                name='main_jobhostsumm_host_id_desc',
            ),
        ),
    ]
