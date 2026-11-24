"""Unique (job, job_created, counter) index on the partitioned event tables.

Adoption can stream one receptor work unit twice, so the callback receiver relies on this index to
refuse an event that is already stored. It is created ON ONLY each parent table: that is instant,
because no existing partition gets built, and every partition attached afterwards gets the index.
Partitions that already exist are left without it until cleanup drops them, and Postgres keeps
reporting the parent index as invalid for that reason. job_created is the partition key, so a
duplicate can never span partitions and the per-partition indexes are enough to keep it out.
"""

from django.db import migrations

from ._sqlite_helper import dbawaremigrations

EVENT_TABLES = (
    ('main_jobevent', 'job_id'),
    ('main_projectupdateevent', 'project_update_id'),
    ('main_inventoryupdateevent', 'inventory_update_id'),
    ('main_adhoccommandevent', 'ad_hoc_command_id'),
    ('main_systemjobevent', 'system_job_id'),
)


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0214_instance_departed_at'),
    ]

    operations = [
        dbawaremigrations.RunSQL(
            sql=[
                f'CREATE UNIQUE INDEX IF NOT EXISTS {table}_counter_uniq ON ONLY {table} ({job_ref}, job_created, counter)' for table, job_ref in EVENT_TABLES
            ],
            reverse_sql=[f'DROP INDEX IF EXISTS {table}_counter_uniq' for table, _ in EVENT_TABLES],
            sqlite_sql=dbawaremigrations.RunSQL.noop,
            sqlite_reverse_sql=dbawaremigrations.RunSQL.noop,
        ),
    ]
