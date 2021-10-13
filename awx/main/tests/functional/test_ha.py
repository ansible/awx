import pytest

# AWX
from awx.main.ha import is_ha_environment
from awx.main.models.ha import Instance


@pytest.mark.django_db
def test_multiple_instances():
    for i in range(2):
        Instance.objects.create(hostname=f'foo{i}', node_type='hybrid')
    assert is_ha_environment()


@pytest.mark.django_db
def test_db_localhost():
    Instance.objects.create(hostname='foo', node_type='hybrid')
    Instance.objects.create(hostname='bar', node_type='execution')
    assert is_ha_environment() is False
