import pytest

from awx.api.versioning import reverse
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.ha import Instance


INSTANCE_KWARGS = dict(hostname='example-host', cpu=6, memory=36000000000, cpu_capacity=6, mem_capacity=42)


@pytest.mark.django_db
def test_disabled_zeros_capacity(patch, admin_user):
    instance = Instance.objects.create(**INSTANCE_KWARGS)
    assert ActivityStream.objects.filter(instance=instance).count() == 1

    url = reverse('api:instance_detail', kwargs={'pk': instance.pk})

    r = patch(url=url, data={'enabled': False}, user=admin_user)
    assert r.data['capacity'] == 0

    instance.refresh_from_db()
    assert instance.capacity == 0
    assert ActivityStream.objects.filter(instance=instance).count() == 2


@pytest.mark.django_db
def test_enabled_sets_capacity(patch, admin_user):
    instance = Instance.objects.create(enabled=False, capacity=0, **INSTANCE_KWARGS)
    assert instance.capacity == 0
    assert ActivityStream.objects.filter(instance=instance).count() == 1

    url = reverse('api:instance_detail', kwargs={'pk': instance.pk})

    r = patch(url=url, data={'enabled': True}, user=admin_user)
    assert r.data['capacity'] > 0

    instance.refresh_from_db()
    assert instance.capacity > 0
    assert ActivityStream.objects.filter(instance=instance).count() == 2


@pytest.mark.django_db
def test_auditor_user_health_check(get, post, system_auditor):
    instance = Instance.objects.create(**INSTANCE_KWARGS)
    url = reverse('api:instance_health_check', kwargs={'pk': instance.pk})
    get(url=url, user=system_auditor, expect=200)
    post(url=url, user=system_auditor, expect=403)


@pytest.mark.django_db
def test_health_check_usage(get, post, admin_user):
    instance = Instance.objects.create(**INSTANCE_KWARGS)
    url = reverse('api:instance_health_check', kwargs={'pk': instance.pk})
    get(url=url, user=admin_user, expect=200)
    r = post(url=url, user=admin_user, expect=200)
    assert r.data['msg'] == f"Health check is running for {instance.hostname}."
