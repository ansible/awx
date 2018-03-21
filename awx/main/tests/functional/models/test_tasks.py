import pytest
import mock
from contextlib import contextmanager

from awx.main.models.tasks import (
    lazy_task,
    TaskRescheduleFlag
)



def f():
    pass


lazy_f = lazy_task()(f)


@contextmanager
def mock_pg_lock(*args, **kwargs):
    yield False  # otherwise gives True with sqlite3 DB


@pytest.mark.django_db
class TestLazyTaskDecorator:
    def test_call_removes_flag(self):
        TaskRescheduleFlag.objects.create(name='mock_f:[42]')
        local_calls = []

        def mock_f(param):
            local_calls.append(param)

        this_f = lazy_task()(mock_f)
        this_f(42)
        assert local_calls == [42]
        assert not TaskRescheduleFlag.objects.filter(name='mock_f:[42]').exists()

    def test_sets_flag_does_not_run_without_lock(self):
        local_calls = []

        def mock_f(param):
            local_calls.append(param)

        this_f = lazy_task()(mock_f)
        with mock.patch('awx.main.models.tasks.advisory_lock', new=mock_pg_lock):
            this_f(42)
        assert local_calls == []
        assert TaskRescheduleFlag.objects.filter(name='mock_f:[42]').exists()
