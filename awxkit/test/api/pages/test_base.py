from http.client import NOT_FOUND
import pytest

from awxkit.config import config


@pytest.fixture(autouse=True)
def setup_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(config, "credentials", {"default": {"username": "foo", "password": "bar"}})
    monkeypatch.setitem(config, "base_url", "")


@pytest.fixture
def response(mocker):
    r = mocker.Mock()
    r.status_code = NOT_FOUND
    r.json.return_value = {
        "token": "my_personal_token",
        "access_token": "my_token",
    }
    return r
