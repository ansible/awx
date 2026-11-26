from contextlib import contextmanager
from unittest import mock
import pytest
from django.db import connection

from awx.main.models import TowerScheduleState
from awx.main.tasks.system import awx_periodic_scheduler


@pytest.mark.django_db
def test_get_or_heal_solo_healthy_single_row():
    state = TowerScheduleState.get_or_heal_solo()
    assert TowerScheduleState.objects.count() == 1
    assert state.pk == 1
    assert state.schedule_last_run is not None


@pytest.mark.django_db
def test_get_or_heal_solo_removes_extra_rows():
    TowerScheduleState.get_solo()  # ensure id=1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO main_towerschedulestate (id, schedule_last_run)
            SELECT 2, schedule_last_run FROM main_towerschedulestate WHERE id = 1
            """
        )
    assert TowerScheduleState.objects.count() == 2

    state = TowerScheduleState.get_or_heal_solo()

    assert state.pk == 1
    assert TowerScheduleState.objects.count() == 1


@contextmanager
def _lock_acquired(*args, **kwargs):
    yield True


@pytest.mark.django_db
def test_awx_periodic_scheduler_uses_heal():
    TowerScheduleState.get_solo()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO main_towerschedulestate (id, schedule_last_run)
            SELECT 2, schedule_last_run FROM main_towerschedulestate WHERE id = 1
            """
        )
    assert TowerScheduleState.objects.count() == 2

    with mock.patch('awx.main.tasks.system.advisory_lock', _lock_acquired):
        awx_periodic_scheduler()

    assert TowerScheduleState.objects.count() == 1
    assert TowerScheduleState.objects.get().pk == 1
