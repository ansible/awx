import pytest

from awx.main.utils.subscriptions import (
    SubscriptionManager,
    SubscriptionManagerSettingsError,
    SubscriptionManagerRefreshError,
)


@pytest.fixture(autouse=True)
def set_valid_subscription_settings(settings):
    settings.ENTITLEMENT_CONSUMER = {
        'uuid': 'c1234',
    }
    settings.SUBSCRIPTIONS_USERNAME = 'abc'
    settings.SUBSCRIPTIONS_PASSWORD = '123'
    settings.REDHAT_CANDLEPIN_VERIFY = False


class TestSubscriptionManagerSettings():

    def test_get_init_params(self):
        (username, password, consumer_uuid, verify) = SubscriptionManager.get_init_params()
        assert username == 'abc'
        assert password == '123'
        assert not verify

    def test_get_init_params_fail(self, settings):
        settings.ENTITLEMENT_CONSUMER = {}
        settings.SUBSCRIPTIONS_USERNAME = ''
        settings.SUBSCRIPTIONS_PASSWORD = ''
        with pytest.raises(SubscriptionManagerSettingsError) as e:
            SubscriptionManager.get_init_params()

        msg = str(e.value.error_msgs)
        assert 'Setting ENTITLEMENT_CONSUMER is empty' in msg
        assert "Setting ENTITLEMENT_CONSUMER['uuid'] not found" in msg
        assert "Setting SUBSCRIPTIONS_USERNAME is empty" in msg
        assert "Setting SUBSCRIPTIONS_PASSWORD is empty" in msg


class TestSubscriptionManagerRefresh():
    def test_refresh_entitlement_certs(self, settings, mocker):
        settings.ENTITLEMENT_CERT = 'blah'

        params = SubscriptionManager.get_init_params()
        submgr = SubscriptionManager(*params)

        submgr.get_entitlement_id = lambda: '1234'
        submgr.get_certificate_for_entitlement = mocker.MagicMock(side_effect=['old_cert', 'new_cert'])
        submgr.rhsm.regenEntitlementCertificate = lambda consumer_id, entitlement_id, **kwargs: True

        (new, old) = submgr.refresh_entitlement_certs()
        assert new == 'new_cert'
        assert old == 'old_cert'

    def test_refresh_entitlement_certs_old_cert_not_found(self, settings, mocker):
        settings.ENTITLEMENT_CERT = 'blah'

        params = SubscriptionManager.get_init_params()
        submgr = SubscriptionManager(*params)

        submgr.get_entitlement_id = lambda: '1234'
        submgr.get_certificate_for_entitlement = mocker.MagicMock(side_effect=[SubscriptionManagerRefreshError('404'), 'new_cert'])
        submgr.rhsm.regenEntitlementCertificate = lambda consumer_id, entitlement_id, **kwargs: True

        (new, old) = submgr.refresh_entitlement_certs()
        assert new == 'new_cert'
        assert old == ''

    def test_refresh_entitlement_certs_old_and_new_cert_not_found(self, settings, mocker):
        settings.ENTITLEMENT_CERT = 'blah'

        params = SubscriptionManager.get_init_params()
        submgr = SubscriptionManager(*params)

        submgr.get_entitlement_id = lambda: '1234'
        submgr.get_certificate_for_entitlement = mocker.MagicMock(side_effect=[
            SubscriptionManagerRefreshError('404 old cert'), SubscriptionManagerRefreshError('404 new cert')])
        submgr.rhsm.regenEntitlementCertificate = lambda consumer_id, entitlement_id, **kwargs: True

        (new, old) = submgr.refresh_entitlement_certs()
        assert new == ''
        assert old == ''

    def test_refresh_entitlement_certs_regen_fail(self, settings, mocker):
        settings.ENTITLEMENT_CERT = 'blah'

        params = SubscriptionManager.get_init_params()
        submgr = SubscriptionManager(*params)

        submgr.get_entitlement_id = lambda: '1234'
        submgr.get_certificate_for_entitlement = mocker.MagicMock(side_effect=['old_cert', SubscriptionManagerRefreshError('404 new cert')])
        submgr.rhsm.regenEntitlementCertificate = lambda consumer_id, entitlement_id, **kwargs: False

        with pytest.raises(SubscriptionManagerRefreshError) as e:
            submgr.refresh_entitlement_certs()
        assert "Failed to refresh entitlement '1234' for consumer 'c1234' on the remote server." == e.value.message

