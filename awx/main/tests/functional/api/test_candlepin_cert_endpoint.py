# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import pytest
from unittest import mock

from awx.api.versioning import reverse

SAMPLE_CERT = "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAKJ5VZ2cPQE5MA0GCSqGSIb3DQEBDUMMY\n-----END CERTIFICATE-----"
SAMPLE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEADUMMY\n-----END RSA PRIVATE KEY-----"
SAMPLE_UUID = "d7b374e5-a8d5-4a65-a84b-8588c5a27847"

MOCK_FETCH = 'awx.api.views.candlepin._fetch_candlepin_cert_from_db'
MOCK_REGISTER = 'awx.api.views.candlepin._register_candlepin_consumer'
MOCK_LIFECYCLE = 'awx.api.views.candlepin._run_candlepin_lifecycle'


@pytest.mark.django_db
class TestCandlepinCertView:
    def url(self):
        return reverse('api:candlepin_cert_view')

    def test_admin_gets_cert_when_registered(self, get, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)):
            r = get(self.url(), admin, expect=200)
        assert r.data['registered'] is True
        assert r.data['cert_pem'] == SAMPLE_CERT
        assert r.data['key_pem'] == SAMPLE_KEY
        assert r.data['consumer_uuid'] == SAMPLE_UUID

    def test_admin_gets_unregistered_response_when_no_cert(self, get, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)):
            r = get(self.url(), admin, expect=200)
        assert r.data['registered'] is False
        assert r.data['cert_pem'] == ''
        assert r.data['key_pem'] == ''
        assert r.data['consumer_uuid'] == ''

    def test_unauthenticated_is_rejected(self, get):
        get(self.url(), expect=401)

    def test_regular_user_is_forbidden(self, get, alice):
        get(self.url(), alice, expect=403)

    def test_system_auditor_is_forbidden(self, get, user):
        # Private key material — auditors should not have access
        auditor = user('auditor', is_superuser=False)
        auditor.is_system_auditor = True
        auditor.save()
        get(self.url(), auditor, expect=403)


@pytest.mark.django_db
class TestCandlepinRegisterView:
    def url(self):
        return reverse('api:candlepin_register_view')

    def test_register_success_returns_201(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)), mock.patch(MOCK_REGISTER, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)):
            r = post(self.url(), {}, admin, expect=201)
        assert r.data['registered'] is True
        assert r.data['consumer_uuid'] == SAMPLE_UUID

    def test_already_registered_returns_409(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)):
            r = post(self.url(), {}, admin, expect=409)
        assert 'error' in r.data

    def test_force_overwrites_existing_registration(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)), mock.patch(
            MOCK_REGISTER, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)
        ):
            r = post(self.url(), {'force': True}, admin, expect=201)
        assert r.data['registered'] is True

    def test_registration_failure_returns_400(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)), mock.patch(MOCK_REGISTER, return_value=(None, None, None)):
            r = post(self.url(), {}, admin, expect=400)
        assert 'error' in r.data

    def test_unauthenticated_is_rejected(self, post):
        post(self.url(), {}, expect=401)

    def test_regular_user_is_forbidden(self, post, alice):
        post(self.url(), {}, alice, expect=403)


@pytest.mark.django_db
class TestCandlepinRenewView:
    def url(self):
        return reverse('api:candlepin_renew_view')

    def test_renew_success_returns_200(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)), mock.patch(MOCK_LIFECYCLE, return_value=(SAMPLE_CERT, SAMPLE_KEY)):
            r = post(self.url(), {}, admin, expect=200)
        assert r.data['registered'] is True

    def test_renew_without_cert_returns_400(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)):
            r = post(self.url(), {}, admin, expect=400)
        assert 'error' in r.data

    def test_force_renew_bypasses_threshold(self, post, admin):
        new_cert = SAMPLE_CERT.replace('DUMMY', 'RENEWED')
        # run_candlepin_lifecycle is imported locally inside post(), so mock the source module
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)), mock.patch(
            'awx.main.utils.candlepin.lifecycle.run_candlepin_lifecycle', return_value=(new_cert, SAMPLE_KEY)
        ) as mock_lifecycle, mock.patch(MOCK_LIFECYCLE, return_value=(new_cert, SAMPLE_KEY)), mock.patch('awx.api.views.candlepin._save_candlepin_cert_to_db'):
            r = post(self.url(), {'force': True}, admin, expect=200)
        # renewal_days=0 was passed to force renewal regardless of days remaining
        call_kwargs = mock_lifecycle.call_args[1]
        assert call_kwargs.get('renewal_days') == 0

    def test_unauthenticated_is_rejected(self, post):
        post(self.url(), {}, expect=401)

    def test_regular_user_is_forbidden(self, post, alice):
        post(self.url(), {}, alice, expect=403)


@pytest.mark.django_db
class TestCandlepinLifecycleView:
    def url(self):
        return reverse('api:candlepin_lifecycle_view')

    def test_registers_and_returns_201_when_no_cert(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)), mock.patch(
            MOCK_REGISTER, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)
        ), mock.patch(MOCK_LIFECYCLE, return_value=(SAMPLE_CERT, SAMPLE_KEY)):
            r = post(self.url(), {}, admin, expect=201)
        assert r.data['registered'] is True
        assert r.data['consumer_uuid'] == SAMPLE_UUID

    def test_returns_200_when_cert_exists(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)), mock.patch(MOCK_LIFECYCLE, return_value=(SAMPLE_CERT, SAMPLE_KEY)):
            r = post(self.url(), {}, admin, expect=200)
        assert r.data['registered'] is True

    def test_runs_lifecycle_when_cert_exists(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)), mock.patch(
            MOCK_LIFECYCLE, return_value=(SAMPLE_CERT, SAMPLE_KEY)
        ) as mock_lc:
            post(self.url(), {}, admin, expect=200)
        mock_lc.assert_called_once_with(SAMPLE_CERT, SAMPLE_KEY, SAMPLE_UUID)

    def test_registration_failure_returns_400(self, post, admin):
        with mock.patch(MOCK_FETCH, return_value=(None, None, None)), mock.patch(MOCK_REGISTER, return_value=(None, None, None)):
            r = post(self.url(), {}, admin, expect=400)
        assert 'error' in r.data

    def test_unauthenticated_is_rejected(self, post):
        post(self.url(), {}, expect=401)

    def test_regular_user_is_forbidden(self, post, alice):
        post(self.url(), {}, alice, expect=403)
