from datetime import timedelta

from django.utils.timezone import now
from django.db import connection

from awx.main.utils.common import create_partition, table_exists


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
