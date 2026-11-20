"""create_partition gives each new event partition a unique (job, job_created, counter) index.

job_created is both in the key and the partition key, so a duplicate never spans partitions and
the per-partition index keeps a job's events unique without a constraint on the parent table.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from django.db import IntegrityError, connection, transaction

from awx.main.dispatch.worker.callback import _is_unique_constraint_violation
from awx.main.models import AdHocCommandEvent, InventoryUpdateEvent, JobEvent, ProjectUpdateEvent, SystemJobEvent
from awx.main.utils.common import create_partition

on_postgres = pytest.mark.skipif(connection.vendor != 'postgresql', reason='event tables are partitioned only on PostgreSQL')

START = datetime(2031, 1, 1, 5, tzinfo=timezone.utc)  # an hour no other test creates a partition for


def _indexdef(index_name):
    with connection.cursor() as cursor:
        cursor.execute('SELECT indexdef FROM pg_indexes WHERE indexname = %s', [index_name])
        row = cursor.fetchone()
    return row[0] if row else None


@on_postgres
@pytest.mark.django_db
@pytest.mark.parametrize('event_class', [JobEvent, AdHocCommandEvent, ProjectUpdateEvent, InventoryUpdateEvent, SystemJobEvent])
def test_a_new_partition_gets_a_unique_counter_index(event_class):
    create_partition(event_class, start=START)

    partition = f'{event_class._meta.db_table}_20310101_05'
    indexdef = _indexdef(f'{partition}_counter_uniq')
    assert indexdef.startswith(f'CREATE UNIQUE INDEX {partition}_counter_uniq ON public.{partition} ')
    assert indexdef.endswith(f'({event_class.JOB_REFERENCE}, job_created, counter)')


@on_postgres
@pytest.mark.django_db
def test_a_duplicate_event_is_rejected_as_a_unique_violation():
    create_partition(JobEvent, start=START)
    fields = dict(job_id=1, job_created=START, created=START, modified=START, counter=7, event='runner_on_ok')
    JobEvent.objects.create(uuid=str(uuid4()), **fields)

    with pytest.raises(IntegrityError) as raised, transaction.atomic():
        JobEvent.objects.create(uuid=str(uuid4()), **fields)

    assert _is_unique_constraint_violation(raised.value)  # the callback receiver then drops it as already stored
