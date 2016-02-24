import pytest

from awx.main.models import UnifiedJob
from django.core.urlresolvers import reverse

@pytest.mark.django_db
def test_options_fields_choices(instance, options, user):

    url = reverse('api:unified_job_list')
    response = options(url, None, user('admin', True))

    assert 'launch_type' in response.data['actions']['GET']
    assert 'choice' == response.data['actions']['GET']['launch_type']['type']
    assert UnifiedJob.LAUNCH_TYPE_CHOICES == response.data['actions']['GET']['launch_type']['choices']
    assert 'choice' == response.data['actions']['GET']['status']['type']
    assert UnifiedJob.STATUS_CHOICES == response.data['actions']['GET']['status']['choices']

