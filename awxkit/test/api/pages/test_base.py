from unittest.mock import Mock, PropertyMock

from http.client import NOT_FOUND
import pytest

from awxkit.api.pages import Base
from awxkit.config import config


@pytest.fixture(autouse=True)
def setup_config():
    config.credentials = {"default": {"username": "foo", "password": "bar"}}
    config.base_url = ""


@pytest.fixture
def response():
    r = Mock()
    r.status_code = NOT_FOUND
    r.json.return_value = {
        "token": "my_personal_token",
        "access_token": "my_token",
    }
    return r


@pytest.mark.parametrize(
    "kwargs,url,token",
    [
        ({"client_id": "foo", "client_secret": "bar"}, "/o/token/", "my_token"),
        ({"client_id": "foo"}, "/o/token/", "my_token"),
        ({}, "/api/gateway/v1/tokens/", "my_personal_token"),
    ],
)
def test_get_oauth2_token_from_gateway(mocker, response, kwargs, url, token):
    post = mocker.patch("requests.Session.post", return_value=response)
    base = Base()
    ret = base.get_oauth2_token(**kwargs)
    assert post.call_count == 1
    assert post.call_args.args[0] == url
    assert ret == token


@pytest.mark.parametrize(
    "kwargs,url,token",
    [
        ({"client_id": "foo", "client_secret": "bar"}, "/api/o/token/", "my_token"),
        ({"client_id": "foo"}, "/api/o/token/", "my_token"),
        ({}, "/api/v2/users/foo/personal_tokens/", "my_personal_token"),
    ],
)
def test_get_oauth2_token_from_controller(mocker, response, kwargs, url, token):
    type(response).ok = PropertyMock(side_effect=[False, True])
    post = mocker.patch("requests.Session.post", return_value=response)
    base = Base()
    ret = base.get_oauth2_token(**kwargs)
    assert post.call_count == 2
    assert post.call_args.args[0] == url
    assert ret == token
