import datetime
from unittest import mock

import pytest

from awx.api.versioning import reverse
from awx.main.models.activity_stream import ActivityStream
from awx.main.models.ha import Instance

from django.test.utils import override_settings
from django.http import HttpResponse

from rest_framework import status

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


def test_instance_install_bundle(get, admin_user, system_auditor):
    instance = Instance.objects.create(**INSTANCE_KWARGS)
    url = reverse('api:instance_install_bundle', kwargs={'pk': instance.pk})
    with mock.patch('awx.api.views.instance_install_bundle.InstanceInstallBundle.get', return_value=HttpResponse({'test': 'data'}, status=status.HTTP_200_OK)):
        get(url=url, user=admin_user, expect=200)
        get(url=url, user=system_auditor, expect=403)


@pytest.mark.django_db
def test_case_insensitive_hostname_guard(post, admin_user):
    """Case-variant of an existing hostname must be rejected and
    hostnames must be stored as lowercase."""
    url = reverse('api:instance_list')
    with override_settings(IS_K8S=True):
        # Permit: a unique hostname is accepted and stored lowercase
        data = {
            "hostname": "Exec-Node.Example.Com",
            "node_type": "execution",
            "node_state": "installed",
            "peers": [],
        }
        r = post(url=url, user=admin_user, data=data, expect=201)
        assert r.data['hostname'] == 'exec-node.example.com'
        inst = Instance.objects.get(pk=r.data['id'])
        assert inst.hostname == 'exec-node.example.com'

        # A second, genuinely different hostname is still accepted
        data_other = dict(data, hostname="other-node.example.com")
        post(url=url, user=admin_user, data=data_other, expect=201)

        # Reject: case-variant of the first hostname is blocked
        data_variant = dict(data, hostname="EXEC-NODE.EXAMPLE.COM")
        post(url=url, user=admin_user, data=data_variant, expect=400)


def test_receptor_cert_validity_capped(tmp_path):
    """Certificate from generate_receptor_tls must be valid <= 365 days."""
    from cryptography import x509 as crypto_x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    from awx.api.views.instance_install_bundle import generate_receptor_tls

    # Build a throwaway CA key + self-signed cert
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = crypto_x509.Name([crypto_x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    ca_cert = (
        crypto_x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(crypto_x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2030, 1, 1))
        .sign(ca_key, hashes.SHA256())
    )

    ca_key_path = tmp_path / "mesh-CA.key"
    ca_cert_path = tmp_path / "mesh-CA.crt"
    ca_key_path.write_bytes(
        ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    ca_cert_path.write_bytes(ca_cert.public_bytes(encoding=serialization.Encoding.PEM))

    instance_obj = mock.Mock(spec=Instance)
    instance_obj.hostname = "test-exec.example.com"

    original_open = open

    def patched_open(path, *args, **kwargs):
        if path == '/etc/receptor/tls/ca/mesh-CA.key':
            return original_open(str(ca_key_path), *args, **kwargs)
        if path == '/etc/receptor/tls/ca/mesh-CA.crt':
            return original_open(str(ca_cert_path), *args, **kwargs)
        return original_open(path, *args, **kwargs)

    with mock.patch('builtins.open', side_effect=patched_open):
        _key_pem, cert_pem = generate_receptor_tls(instance_obj)

    cert = crypto_x509.load_pem_x509_certificate(cert_pem)
    validity = cert.not_valid_after_utc - cert.not_valid_before_utc
    assert validity.days <= 365, f"Certificate valid for {validity.days} days, expected <= 365"
