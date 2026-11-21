from django.db import migrations, models

from ._sqlite_helper import dbawaremigrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('main', '0212_create_metrics_utility_functions'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                dbawaremigrations.RunSQL(
                    sql=('CREATE INDEX CONCURRENTLY IF NOT EXISTS main_as_object1_id_idx ON main_activitystream (object1, id)'),
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS main_as_object1_id_idx',
                    sqlite_sql=dbawaremigrations.RunSQL.noop,
                    sqlite_reverse_sql=dbawaremigrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='activitystream',
                    index=models.Index(
                        fields=['object1', 'id'],
                        name='main_as_object1_id_idx',
                    ),
                ),
            ],
        ),
    ]
