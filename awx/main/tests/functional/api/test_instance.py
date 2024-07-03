import pytest

from awx.api.versioning import reverse
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.ha import Instance

from django.test.utils import override_settings


INSTANCE_KWARGS = dict(hostname='example-host', cpu=6, node_type='execution', memory=36000000000, cpu_capacity=6, mem_capacity=42)


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


def test_custom_hostname_regex(post, admin_user):
    url = reverse('api:instance_list')
    with override_settings(IS_K8S=True):
        for value in [
            ("foo.bar.baz", 201),
            ("f.bar.bz", 201),
            ("foo.bar.b", 400),
            ("a.b.c", 400),
            ("localhost", 400),
            ("127.0.0.1", 400),
            ("192.168.56.101", 201),
            ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", 201),
            ("foobar", 201),
            ("--yoooo", 400),
            ("$3$@foobar@#($!@#*$", 400),
            ("999.999.999.999", 201),
            ("0000:0000:0000:0000:0000:0000:0000:0001", 400),
            ("whitespaces are bad for hostnames", 400),
            ("0:0:0:0:0:0:0:1", 400),
            ("192.localhost.domain.101", 201),
            ("F@$%(@#$H%^(I@#^HCTQEWRFG", 400),
        ]:
            data = {
                "hostname": value[0],
                "node_type": "execution",
                "node_state": "installed",
                "peers": [],
            }
            post(url=url, user=admin_user, data=data, expect=value[1])
