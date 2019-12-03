import pytest

from awx.main.models import SystemJobTemplate


@pytest.mark.parametrize("extra_data", [
    '{ "days": 1 }',
    '{ "days": 100 }',
    '{ "days": 0 }',
    {"days": 0},
    {"days": 1},
    {"days": 13435},
])
def test_valid__clean_extra_data_system_jobs(extra_data):
    accepted, rejected, errors = SystemJobTemplate(
        job_type='cleanup_jobs'
    ).accept_or_ignore_variables(extra_data)
    assert not rejected
    assert not errors


@pytest.mark.parametrize("extra_data", [
    '{ "days": 1.2 }',
    '{ "days": -1.2 }',
    '{ "days": -111 }',
    '{ "days": "-111" }',
    '{ "days": false }',
    '{ "days": "foobar" }',
    {"days": 1.2},
    {"days": -1.2},
    {"days": -111},
    {"days": "-111"},
    {"days": False},
    {"days": "foobar"},
])
def test_invalid__extra_data_system_jobs(extra_data):
    accepted, rejected, errors = SystemJobTemplate(
        job_type='cleanup_jobs'
    ).accept_or_ignore_variables(extra_data)
    assert str(errors['extra_vars'][0]) == u'days must be a positive integer.'


def test_unallowed_system_job_data():
    sjt = SystemJobTemplate(job_type='cleanup_jobs')
    accepted, ignored, errors = sjt.accept_or_ignore_variables({
        'days': 34,
        'foobar': 'baz'
    })
    assert 'foobar' in ignored
    assert 'days' in accepted


def test_reject_other_prommpts():
    sjt = SystemJobTemplate()
    accepted, ignored, errors = sjt._accept_or_ignore_job_kwargs(limit="")
    assert accepted == {}
    assert 'not allowed on launch' in errors['limit'][0]


def test_reject_some_accept_some():
    sjt = SystemJobTemplate(job_type='cleanup_jobs')
    accepted, ignored, errors = sjt._accept_or_ignore_job_kwargs(limit="", extra_vars={
        'days': 34,
        'foobar': 'baz'
    })
    assert accepted == {"extra_vars": {"days": 34}}
    assert ignored == {"limit": "", "extra_vars": {"foobar": "baz"}}
    assert 'not allowed on launch' in errors['limit'][0]

