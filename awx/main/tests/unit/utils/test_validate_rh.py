import configparser

import pytest
from unittest.mock import patch
from awx.main.utils.licensing import Licenser


def test_validate_rh_basic_auth_rhsm():
    """
    Assert get_rhsm_subs is called when
    - basic_auth=True
    - REDHAT_CANDLEPIN_HOST is not set
    - host is subscription.rhsm.redhat.com
    """
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(
        licenser, 'get_host_from_rhsm_config', return_value='https://subscription.rhsm.redhat.com'
    ) as mock_get_host, patch.object(licenser, 'get_rhsm_subs', return_value=[]) as mock_get_rhsm, patch.object(
        licenser, 'get_satellite_subs'
    ) as mock_get_satellite, patch.object(
        licenser, 'get_crc_subs'
    ) as mock_get_crc, patch.object(
        licenser, 'generate_license_options_from_entitlements'
    ) as mock_generate:

        mock_settings.REDHAT_CANDLEPIN_HOST = None

        licenser.validate_rh('testuser', 'testpass', basic_auth=True)

        mock_get_host.assert_called_once()
        mock_get_rhsm.assert_called_once_with('https://subscription.rhsm.redhat.com', 'testuser', 'testpass')
        mock_get_satellite.assert_not_called()
        mock_get_crc.assert_not_called()
        mock_generate.assert_called_once_with([], is_candlepin=True)


def test_validate_rh_basic_auth_satellite():
    """
    Assert get_satellite_subs is called when
    - basic_auth=True
    - REDHAT_CANDLEPIN_HOST is not set
    - rhsm.conf points to a non-RHSM host
    """
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(
        licenser, 'get_host_from_rhsm_config', return_value='https://satellite.example.com'
    ) as mock_get_host, patch.object(licenser, 'get_rhsm_subs') as mock_get_rhsm, patch.object(
        licenser, 'get_satellite_subs', return_value=[]
    ) as mock_get_satellite, patch.object(
        licenser, 'get_crc_subs'
    ) as mock_get_crc, patch.object(
        licenser, 'generate_license_options_from_entitlements'
    ) as mock_generate:

        mock_settings.REDHAT_CANDLEPIN_HOST = None

        licenser.validate_rh('testuser', 'testpass', basic_auth=True)

        mock_get_host.assert_called_once()
        mock_get_rhsm.assert_not_called()
        mock_get_satellite.assert_called_once_with('https://satellite.example.com', 'testuser', 'testpass')
        mock_get_crc.assert_not_called()
        mock_generate.assert_called_once_with([], is_candlepin=True)


def test_validate_rh_service_account_crc():
    """
    Assert get_crc_subs is called when
    - basic_auth=False
    """
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(licenser, 'get_host_from_rhsm_config') as mock_get_host, patch.object(
        licenser, 'get_rhsm_subs'
    ) as mock_get_rhsm, patch.object(licenser, 'get_satellite_subs') as mock_get_satellite, patch.object(
        licenser, 'get_crc_subs', return_value=[]
    ) as mock_get_crc, patch.object(
        licenser, 'generate_license_options_from_entitlements'
    ) as mock_generate:

        mock_settings.SUBSCRIPTIONS_RHSM_URL = 'https://console.redhat.com/api/rhsm/v1/subscriptions'

        licenser.validate_rh('client_id', 'client_secret', basic_auth=False)

        mock_get_host.assert_not_called()
        mock_get_rhsm.assert_not_called()
        mock_get_satellite.assert_not_called()
        mock_get_crc.assert_called_once_with('https://console.redhat.com/api/rhsm/v1/subscriptions', 'client_id', 'client_secret')
        mock_generate.assert_called_once_with([], is_candlepin=False)


def test_validate_rh_candlepin_host_prioritized_over_rhsm_config():
    """Test REDHAT_CANDLEPIN_HOST takes priority over rhsm.conf
    - basic_auth=True
    - REDHAT_CANDLEPIN_HOST is set
    - rhsm.conf should NOT be consulted
    """
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(licenser, 'get_host_from_rhsm_config') as mock_get_host, patch.object(
        licenser, 'get_rhsm_subs'
    ) as mock_get_rhsm, patch.object(licenser, 'get_satellite_subs', return_value=[]) as mock_get_satellite, patch.object(
        licenser, 'get_crc_subs'
    ) as mock_get_crc, patch.object(
        licenser, 'generate_license_options_from_entitlements'
    ) as mock_generate:

        mock_settings.REDHAT_CANDLEPIN_HOST = 'https://satellite.example.com'
        licenser.validate_rh('testuser', 'testpass', basic_auth=True)

        mock_get_host.assert_not_called()
        mock_get_rhsm.assert_not_called()
        mock_get_satellite.assert_called_once_with('https://satellite.example.com', 'testuser', 'testpass')
        mock_get_crc.assert_not_called()
        mock_generate.assert_called_once_with([], is_candlepin=True)


def test_validate_rh_prepends_scheme_when_missing():
    """REDHAT_CANDLEPIN_HOST without a scheme gets https:// prepended"""
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(licenser, 'get_host_from_rhsm_config'), patch.object(
        licenser, 'get_rhsm_subs'
    ) as mock_get_rhsm, patch.object(licenser, 'get_satellite_subs', return_value=[]) as mock_get_satellite, patch.object(
        licenser, 'get_crc_subs'
    ), patch.object(
        licenser, 'generate_license_options_from_entitlements'
    ):

        mock_settings.REDHAT_CANDLEPIN_HOST = 'satellite.example.com'
        licenser.validate_rh('testuser', 'testpass', basic_auth=True)

        mock_get_satellite.assert_called_once_with('https://satellite.example.com', 'testuser', 'testpass')
        mock_get_rhsm.assert_not_called()


def test_validate_rh_missing_user_raises_error():
    """Test validate_rh raises ValueError when user is missing"""
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(
        licenser, 'get_host_from_rhsm_config', return_value='https://subscription.rhsm.redhat.com'
    ):
        mock_settings.REDHAT_CANDLEPIN_HOST = None
        with pytest.raises(ValueError, match='subscriptions_client_id or subscriptions_username is required'):
            licenser.validate_rh(None, 'testpass', basic_auth=True)


def test_validate_rh_missing_password_raises_error():
    """Test validate_rh raises ValueError when password is missing"""
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(
        licenser, 'get_host_from_rhsm_config', return_value='https://subscription.rhsm.redhat.com'
    ):
        mock_settings.REDHAT_CANDLEPIN_HOST = None
        with pytest.raises(ValueError, match='subscriptions_client_secret or subscriptions_password is required'):
            licenser.validate_rh('testuser', None, basic_auth=True)


@pytest.mark.parametrize(
    'host_input, rhsm_port, expected_in_url, not_expected_in_url',
    [
        ('https://satellite.example.com:8443', '443', ':8443', ':8443:443'),
        ('https://satellite.example.com', '8443', ':8443', None),
        ('https://satellite.example.com/', '8443', ':8443', '/:'),
    ],
    ids=['skip-port-when-present', 'append-port-when-missing', 'strip-trailing-slash'],
)
def test_get_satellite_subs_port_handling(host_input, rhsm_port, expected_in_url, not_expected_in_url):
    licenser = Licenser()
    licenser.config = configparser.ConfigParser()
    licenser.config.read_string(f"[server]\nhostname=satellite.example.com\nport={rhsm_port}\n[rhsm]\nrepo_ca_cert=/etc/rhsm/ca/redhat-uep.pem\n")

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch('awx.main.utils.licensing.requests') as mock_requests:
        mock_settings.REDHAT_CANDLEPIN_VERIFY = None
        mock_orgs = mock_requests.get.return_value
        mock_orgs.json.return_value = {'results': []}

        licenser.get_satellite_subs(host_input, 'user', 'pw')

        called_url = mock_requests.get.call_args[0][0]
        assert expected_in_url in called_url
        if not_expected_in_url:
            assert not_expected_in_url not in called_url


def test_get_satellite_subs_uses_candlepin_verify_setting():
    """REDHAT_CANDLEPIN_VERIFY should take priority over rhsm.conf ca_cert"""
    licenser = Licenser()
    licenser.config = configparser.ConfigParser()
    licenser.config.read_string("[server]\nhostname=satellite.example.com\n[rhsm]\nrepo_ca_cert=/etc/rhsm/ca/redhat-uep.pem\n")

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch('awx.main.utils.licensing.requests') as mock_requests:
        mock_settings.REDHAT_CANDLEPIN_VERIFY = False
        mock_orgs = mock_requests.get.return_value
        mock_orgs.json.return_value = {'results': []}

        licenser.get_satellite_subs('https://satellite.example.com', 'user', 'pw')

        assert mock_requests.get.call_args[1]['verify'] is False


def test_validate_rh_no_host_raises_error():
    """Test validate_rh raises ValueError when no host is available
    - basic_auth=True
    - REDHAT_CANDLEPIN_HOST is not set
    - rhsm.conf returns None
    """
    licenser = Licenser()

    with patch('awx.main.utils.licensing.settings') as mock_settings, patch.object(licenser, 'get_host_from_rhsm_config', return_value=None):
        mock_settings.REDHAT_CANDLEPIN_HOST = None
        with pytest.raises(ValueError, match='Could not get host url for subscriptions'):
            licenser.validate_rh('testuser', 'testpass', basic_auth=True)
