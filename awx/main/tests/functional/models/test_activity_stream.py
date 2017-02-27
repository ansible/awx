import pytest

# AWX models
from awx.main.models.organization import Organization
from awx.main.models import ActivityStream



@pytest.mark.django_db
def test_activity_stream_create_entries():
    Organization.objects.create(name='test-organization2')
    assert ActivityStream.objects.filter(organization__isnull=False).count() == 1

