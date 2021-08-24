import pytest

from awx.api.versioning import reverse

from awx.main.models.ha import Instance


@pytest.mark.django_db
def test_disabled_zeros_capacity(patch, admin_user):
    instance = Instance.objects.create(hostname='example-host', cpu=6, memory=36000000000, cpu_capacity=6, mem_capacity=42)

    url = reverse('api:instance_detail', kwargs={'pk': instance.pk})

    r = patch(url=url, data={'enabled': False}, user=admin_user)
    assert r.data['capacity'] == 0

    instance.refresh_from_db()
    assert instance.capacity == 0


@pytest.mark.django_db
def test_enabled_sets_capacity(patch, admin_user):
    instance = Instance.objects.create(hostname='example-host', enabled=False, cpu=6, memory=36000000000, cpu_capacity=6, mem_capacity=42, capacity=0)
    assert instance.capacity == 0

    url = reverse('api:instance_detail', kwargs={'pk': instance.pk})

    r = patch(url=url, data={'enabled': True}, user=admin_user)
    assert r.data['capacity'] > 0

    instance.refresh_from_db()
    assert instance.capacity > 0
