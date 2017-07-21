import pytest
import json

from django.core.exceptions import ValidationError

from awx.main.models import (
    Schedule,
    SystemJobTemplate,
    JobTemplate,
)


def test_clean_extra_data_system_job(mocker):
    jt = SystemJobTemplate()
    schedule = Schedule(unified_job_template=jt)
    schedule._clean_extra_data_system_jobs = mocker.MagicMock()

    schedule.clean_extra_data()

    schedule._clean_extra_data_system_jobs.assert_called_once()
 

def test_clean_extra_data_other_job(mocker):
    jt = JobTemplate()
    schedule = Schedule(unified_job_template=jt)
    schedule._clean_extra_data_system_jobs = mocker.MagicMock()

    schedule.clean_extra_data()

    schedule._clean_extra_data_system_jobs.assert_not_called()
    

@pytest.mark.parametrize("extra_data", [
    '{ "days": 1 }',
    '{ "days": 100 }',
    '{ "days": 0 }',
    {"days": 0},
    {"days": 1},
    {"days": 13435},
])
def test_valid__clean_extra_data_system_jobs(extra_data):
    schedule = Schedule()
    schedule.extra_data = extra_data
    schedule._clean_extra_data_system_jobs()


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
def test_invalid__clean_extra_data_system_jobs(extra_data):
    schedule = Schedule()
    schedule.extra_data = extra_data
    with pytest.raises(ValidationError) as e:
        schedule._clean_extra_data_system_jobs()

    assert json.dumps(str(e.value)) == json.dumps(str([u'days must be a positive integer.']))

