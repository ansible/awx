import pytest

from django.conf import settings
from datetime import timedelta


@pytest.mark.parametrize("job_name,function_path", [
    ('admin_checks', 'awx.main.tasks.run_administrative_checks'),
    ('tower_scheduler', 'awx.main.tasks.awx_periodic_scheduler'),
])
def test_CELERY_BEAT_SCHEDULE(mocker, job_name, function_path):
    assert job_name in settings.CELERY_BEAT_SCHEDULE
    assert 'schedule' in settings.CELERY_BEAT_SCHEDULE[job_name]
    assert type(settings.CELERY_BEAT_SCHEDULE[job_name]['schedule']) is timedelta
    assert settings.CELERY_BEAT_SCHEDULE[job_name]['task'] == function_path

    # Ensures that the function exists
    mocker.patch(function_path)
