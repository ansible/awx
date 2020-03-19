# -*- coding: utf-8 -*-
from collections import namedtuple

from unittest.mock import patch
import pytest

from awxkit.ws import WSClient

ParseResult = namedtuple("ParseResult", ["port", "hostname", "secure"])

def test_explicit_hostname():
    client = WSClient("token", "some-hostname", 556, False)
    assert client.port == 556
    assert client.hostname == "some-hostname"
    assert client._use_ssl == False
    assert client.token == "token"


@pytest.mark.parametrize('url, result',
                         [['https://somename:123', ParseResult(123, "somename", True)],
                          ['http://othername:456', ParseResult(456, "othername", False)],
                          ['http://othername', ParseResult(80, "othername", False)],
                          ['https://othername', ParseResult(443, "othername", True)],
])
def test_urlparsing(url, result):
    with patch("awxkit.ws.config") as mock_config:
        mock_config.base_url = url

        client = WSClient("token")
        assert client.port == result.port
        assert client.hostname == result.hostname
        assert client._use_ssl == result.secure
