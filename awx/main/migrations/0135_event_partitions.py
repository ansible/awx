from django.db import migrations, models, connection


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

    for tblname in ('main_jobevent', 'main_inventoryupdateevent', 'main_projectupdateevent', 'main_adhoccommandevent', 'main_systemjobevent'):
        with connection.cursor() as cursor:
            # mark existing table as _unpartitioned_*
            # we will drop this table after its data
            # has been moved over
            cursor.execute(f'ALTER TABLE {tblname} RENAME TO _unpartitioned_{tblname}')

            # create a copy of the table that we will use as a reference for schema
            # otherwise, the schema changes we would make on the old jobevents table
            # (namely, dropping the primary key constraint) would cause the migration
            # to suffer a serious performance degradation
            cursor.execute(f'CREATE TABLE tmp_{tblname} ' f'(LIKE _unpartitioned_{tblname} INCLUDING ALL)')

            # drop primary key constraint; in a partioned table
            # constraints must include the partition key itself
            # TODO: do more generic search for pkey constraints
            # instead of hardcoding this one that applies to main_jobevent
            cursor.execute(f'ALTER TABLE tmp_{tblname} DROP CONSTRAINT tmp_{tblname}_pkey')

            # create parent table
            cursor.execute(
                f'CREATE TABLE {tblname} '
                f'(LIKE tmp_{tblname} INCLUDING ALL, job_created TIMESTAMP WITH TIME ZONE NOT NULL) '
                f'PARTITION BY RANGE(job_created);'
            )

            cursor.execute(f'DROP TABLE tmp_{tblname}')

            # let's go ahead and add and subtract a few indexes while we're here
            cursor.execute(f'CREATE INDEX {tblname}_modified_idx ON {tblname} (modified);')
            cursor.execute(f'DROP INDEX IF EXISTS {tblname}_job_id_brin_idx;')

            # recreate primary key constraint
            cursor.execute(f'ALTER TABLE ONLY {tblname} ' f'ADD CONSTRAINT {tblname}_pkey_new PRIMARY KEY (id, job_created);')


class FakeAddField(migrations.AddField):
    def database_forwards(self, *args):
        # this is intentionally left blank, because we're
        # going to accomplish the migration with some custom raw SQL
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0134_unifiedjob_ansible_version'),
    ]

    operations = [
        migrations.RunPython(migrate_event_data),
        FakeAddField(
            model_name='jobevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
        FakeAddField(
            model_name='inventoryupdateevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
        FakeAddField(
            model_name='projectupdateevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
        FakeAddField(
            model_name='adhoccommandevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
        FakeAddField(
            model_name='systemjobevent',
            name='job_created',
            field=models.DateTimeField(null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='job',
            field=models.ForeignKey(editable=False, null=True, on_delete=models.deletion.SET_NULL, related_name='job_events', to='main.Job'),
        ),
        migrations.CreateModel(
            name='UnpartitionedAdHocCommandEvent',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.adhoccommandevent',),
        ),
        migrations.CreateModel(
            name='UnpartitionedInventoryUpdateEvent',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.inventoryupdateevent',),
        ),
        migrations.CreateModel(
            name='UnpartitionedJobEvent',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.jobevent',),
        ),
        migrations.CreateModel(
            name='UnpartitionedProjectUpdateEvent',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.projectupdateevent',),
        ),
        migrations.CreateModel(
            name='UnpartitionedSystemJobEvent',
            fields=[],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.systemjobevent',),
        ),
    ]
