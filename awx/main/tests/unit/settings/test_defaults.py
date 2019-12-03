import pytest

from django.conf import settings
from datetime import timedelta


@pytest.mark.parametrize("job_name,function_path", [
    ('tower_scheduler', 'awx.main.tasks.awx_periodic_scheduler'),
])
def test_CELERYBEAT_SCHEDULE(mocker, job_name, function_path):
    assert job_name in settings.CELERYBEAT_SCHEDULE
    assert 'schedule' in settings.CELERYBEAT_SCHEDULE[job_name]
    assert type(settings.CELERYBEAT_SCHEDULE[job_name]['schedule']) is timedelta
    assert settings.CELERYBEAT_SCHEDULE[job_name]['task'] == function_path

    # Ensures that the function exists
    mocker.patch(function_path)
