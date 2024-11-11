from http.client import NOT_FOUND
import pytest

from awxkit.config import config


@pytest.fixture(autouse=True)
def setup_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "credentials", {"default": {"username": "foo", "password": "bar"}}, raising=False)
    monkeypatch.setattr(config, "base_url", "", raising=False)


@pytest.fixture
def response(mocker):
    r = mocker.Mock()
    r.status_code = NOT_FOUND
    r.json.return_value = {
        "token": "my_personal_token",
        "access_token": "my_token",
    }
    return r
