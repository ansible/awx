from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from django.utils.timezone import now
from django.db import IntegrityError, connection, transaction

from awx.main.dispatch.worker.callback import _is_unique_constraint_violation
from awx.main.models import AdHocCommandEvent, InventoryUpdateEvent, JobEvent, ProjectUpdateEvent, SystemJobEvent
from awx.main.utils.common import create_partition, table_exists

EVENT_CLASSES = [JobEvent, ProjectUpdateEvent, InventoryUpdateEvent, AdHocCommandEvent, SystemJobEvent]


def test_table_when_it_exists():
    with connection.cursor() as cursor:
        assert table_exists(cursor, 'main_job')


def test_table_when_it_does_not_exists():
    with connection.cursor() as cursor:
        assert not table_exists(cursor, 'main_not_a_table_check')


def test_create_partition_race_condition(mocker):
    mocker.patch('awx.main.utils.common.table_exists', return_value=False)

    create_partition('main_jobevent', start=now() - timedelta(days=2))
    create_partition('main_jobevent', start=now() - timedelta(days=2))


def _indexdef(index_name):
    with connection.cursor() as cursor:
        cursor.execute('SELECT indexdef FROM pg_indexes WHERE indexname = %s', [index_name])
        row = cursor.fetchone()
    return row[0] if row else None


@pytest.mark.parametrize('event_class', EVENT_CLASSES)
def test_event_table_has_a_unique_counter_index_for_new_partitions(event_class):
    """A unique (job, job_created, counter) index exists ON ONLY the parent, so partitions created after
    the migration inherit it; partitions that already existed are left alone."""
    table = event_class._meta.db_table
    indexdef = _indexdef(f'{table}_counter_uniq')
    assert indexdef is not None, f'{table} has no unique counter index'
    assert indexdef.startswith(f'CREATE UNIQUE INDEX {table}_counter_uniq ON ONLY public.{table} ')
    assert indexdef.endswith(f'({event_class.JOB_REFERENCE}, job_created, counter)')


def test_a_new_partition_rejects_a_duplicate_event():
    """A partition made by create_partition() gets the unique index on ATTACH, so a replayed event is refused."""
    start = datetime(2031, 1, 1, 5, tzinfo=timezone.utc)  # an hour nothing else creates a partition for
    fields = dict(job_id=1, job_created=start, created=start, modified=start, counter=7, event='runner_on_ok')
    with transaction.atomic():
        create_partition(JobEvent._meta.db_table, start=start)
        JobEvent.objects.create(uuid=str(uuid4()), **fields)
        with pytest.raises(IntegrityError) as raised, transaction.atomic():
            JobEvent.objects.create(uuid=str(uuid4()), **fields)
        assert _is_unique_constraint_violation(raised.value)  # the callback receiver drops it as already stored
        transaction.set_rollback(True)  # leave no partition or rows behind in the dev database
