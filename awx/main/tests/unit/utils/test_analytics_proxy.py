import pytest
import requests
from unittest import mock

from awx.main.utils.analytics_proxy import OIDCClient, TokenType, TokenError


MOCK_TOKEN_RESPONSE = {
    'access_token': 'bob-access-token',
    'expires_in': 500,
    'refresh_expires_in': 900,
    'token_type': 'Bearer',
    'not-before-policy': 6,
    'scope': 'fake-scope1, fake-scope2',
}


@pytest.fixture
def oidc_client():
    '''
    oidc client instantiation fixture.
    '''
    return OIDCClient(
        'fake-client-id',
        'fake-client-secret',
        'https://my-token-url.com/get/a/token/',
        ['api.console'],
    )


@pytest.fixture
def token():
    '''
    Create Token class out of example OIDC token response.
    '''
    return OIDCClient._json_response_to_token(MOCK_TOKEN_RESPONSE)


def test_generate_access_token(oidc_client):
    with mock.patch(
        'awx.main.utils.analytics_proxy.requests.post',
        return_value=mock.Mock(json=lambda: MOCK_TOKEN_RESPONSE, raise_for_status=mock.Mock(return_value=None)),  # No exception raised
    ):
        oidc_client._generate_access_token()

        assert oidc_client.token
        assert oidc_client.token.access_token == 'bob-access-token'
        assert oidc_client.token.expires_in == 500
        assert oidc_client.token.refresh_expires_in == 900
        assert oidc_client.token.token_type == TokenType.BEARER
        assert oidc_client.token.not_before_policy == 6
        assert oidc_client.token.scope == 'fake-scope1, fake-scope2'


def test_token_generation_error(oidc_client):
    '''
    Check that TokenError is raised for failure in token generation process
    '''
    exception_404 = requests.HTTPError('404 Client Error: Not Found for url')
    with mock.patch(
        'awx.main.utils.analytics_proxy.requests.post',
        return_value=mock.Mock(status_code=404, json=mock.Mock(return_value={'error': 'Not Found'}), raise_for_status=mock.Mock(side_effect=exception_404)),
    ):
        with pytest.raises(TokenError) as exc_info:
            oidc_client._generate_access_token()

        assert exc_info.value.__cause__ == exception_404


def test_make_request(oidc_client, token):
    '''
    Check that make_request makes an http request with a generated token.
    '''

    def fake_generate_access_token():
        oidc_client.token = token

    with (
        mock.patch.object(oidc_client, '_generate_access_token', side_effect=fake_generate_access_token),
        mock.patch('awx.main.utils.analytics_proxy.requests.request') as mock_request,
    ):
        oidc_client.make_request('GET', 'https://does_not_exist.com')

        mock_request.assert_called_with(
            'GET',
            'https://does_not_exist.com',
            headers={
                'Authorization': f'Bearer {token.access_token}',
                'Accept': 'application/json',
            },
        )


def test_make_request_existing_token(oidc_client, token):
    '''
    Check that make_request does not try and generate a token.
    '''
    oidc_client.token = token

    with (
        mock.patch.object(oidc_client, '_generate_access_token', side_effect=RuntimeError('expected not to be called')),
        mock.patch('awx.main.utils.analytics_proxy.requests.request') as mock_request,
    ):
        oidc_client.make_request('GET', 'https://does_not_exist.com')

        mock_request.assert_called_with(
            'GET',
            'https://does_not_exist.com',
            headers={
                'Authorization': f'Bearer {token.access_token}',
                'Accept': 'application/json',
            },
        )
