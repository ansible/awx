from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="CREATE INDEX IF NOT EXISTS main_jobhostsumm_host_id_desc ON main_jobhostsummary (host_id, id DESC)",
                    reverse_sql="DROP INDEX IF EXISTS main_jobhostsumm_host_id_desc",
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='jobhostsummary',
                    index=models.Index(
                        fields=['host', '-id'],
                        name='main_jobhostsumm_host_id_desc',
                    ),
                ),
            ],
        ),
    ]
