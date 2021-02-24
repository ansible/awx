from datetime import datetime

from django.db import migrations, models, connection
from django.utils.timezone import now

from awx.main.utils.common import create_partition


def migrate_event_data(apps, schema_editor):
    # see: https://github.com/ansible/awx/issues/9039
    #
    # the goal of this function is -- for each job event table -- to:
    # - create a parent partition table
    # - .. with a single partition
    # - .. that includes all existing job events
    #
    # the new main_jobevent_parent table should have a new
    # denormalized column, job_created, this is used as a
    # basis for partitioning job event rows
    #
    # The initial partion will be a unique case. After
    # the migration is completed, awx should create
    # new partitions on an hourly basis, as needed.
    # All events for a given job should be placed in
    # a partition based on the job's _created time_.

    for tblname in (
        'main_jobevent', 'main_inventoryupdateevent',
        'main_projectupdateevent', 'main_adhoccommandevent',
        'main_systemjobevent'
    ):
        with connection.cursor() as cursor:
            # mark existing table as *_old;
            # we will drop this table after its data
            # has been moved over
            cursor.execute(
                f'ALTER TABLE {tblname} RENAME TO {tblname}_old'
            )

            # drop primary key constraint; in a partioned table
            # constraints must include the partition key itself
            # TODO: do more generic search for pkey constraints
            # instead of hardcoding this one that applies to main_jobevent
            cursor.execute(
                f'ALTER TABLE {tblname}_old DROP CONSTRAINT {tblname}_pkey1'
            )

            # create parent table
            cursor.execute(
                f'CREATE TABLE {tblname} '
                f'(LIKE {tblname}_old INCLUDING ALL, job_created TIMESTAMP WITH TIME ZONE NOT NULL) '
                f'PARTITION BY RANGE(job_created);'
            )

            # recreate primary key constraint
            cursor.execute(
                f'ALTER TABLE ONLY {tblname} '
                f'ADD CONSTRAINT {tblname}_pkey_new PRIMARY KEY (id, job_created);'
            )

            current_time = now()

            # .. as well as initial partition containing all existing events
            epoch = datetime(2000, 1, 1, 0, 0)
            create_partition(epoch, current_time, 'old_events')

            # .. and first partition
            # .. which is a special case, as it only covers remainder of current hour
            create_partition(tblname, current_time)

            # copy over all job events into partitioned table
            # TODO: https://github.com/ansible/awx/issues/9257
            cursor.execute(
                f'INSERT INTO {tblname} '
                f'SELECT {tblname}_old.*, main_unifiedjob.created '
                f'FROM {tblname}_old '
                f'INNER JOIN main_unifiedjob ON {tblname}_old.job_id = main_unifiedjob.id;'
            )

            # drop old table
            cursor.execute(
                f'DROP TABLE {tblname}_old'
            )


class FakeAddField(migrations.AddField):

    def database_forwards(self, *args):
        # this is intentionally left blank, because we're
        # going to accomplish the migration with some custom raw SQL
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0123_drop_hg_support'),
    ]

    operations = [
        migrations.RunPython(migrate_event_data),
        FakeAddField(
            model_name='jobevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
    ]
