from awx.main.tasks.callback import RunnerCallback
from awx.main.constants import ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE

from django.utils.translation import gettext_lazy as _


def test_delay_update(mock_me):
    rc = RunnerCallback()
    rc.delay_update(foo='bar')
    assert rc.extra_update_fields == {'foo': 'bar'}
    rc.delay_update(foo='foobar')
    assert rc.extra_update_fields == {'foo': 'foobar'}
    rc.delay_update(bar='foo')
    assert rc.get_delayed_update_fields() == {'foo': 'foobar', 'bar': 'foo', 'emitted_events': 0}


def test_delay_update_skip_if_set(mock_me):
    rc = RunnerCallback()
    rc.delay_update(foo='bar', skip_if_already_set=True)
    assert rc.extra_update_fields == {'foo': 'bar'}
    rc.delay_update(foo='foobar', skip_if_already_set=True)
    assert rc.extra_update_fields == {'foo': 'bar'}


def test_delay_update_failure_fields(mock_me):
    rc = RunnerCallback()
    rc.delay_update(job_explanation='1')
    rc.delay_update(job_explanation=_('2'))
    assert rc.extra_update_fields == {'job_explanation': '1\n2'}
    rc.delay_update(result_traceback='1')
    rc.delay_update(result_traceback=_('2'))
    rc.delay_update(result_traceback=_('3'), skip_if_already_set=True)
    assert rc.extra_update_fields == {'job_explanation': '1\n2', 'result_traceback': '1\n2'}


def test_duplicate_updates(mock_me):
    rc = RunnerCallback()
    rc.delay_update(job_explanation='really long summary...')
    rc.delay_update(job_explanation='really long summary...')
    rc.delay_update(job_explanation='really long summary...')
    assert rc.extra_update_fields == {'job_explanation': 'really long summary...'}


def test_special_ansible_runner_message(mock_me):
    rc = RunnerCallback()
    rc.delay_update(result_traceback='Traceback:\ngot an unexpected keyword argument\nFile: foo.py')
    rc.delay_update(result_traceback='Traceback:\ngot an unexpected keyword argument\nFile: bar.py')
    assert rc.get_delayed_update_fields().get('result_traceback') == (
        'Traceback:\ngot an unexpected keyword argument\nFile: foo.py\n'
        'Traceback:\ngot an unexpected keyword argument\nFile: bar.py\n'
        f'{ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE}'
    )
