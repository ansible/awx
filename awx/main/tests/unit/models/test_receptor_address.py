from awx.main.models import ReceptorAddress
import pytest

ReceptorAddress()


@pytest.mark.parametrize(
    'address, protocol, port, websocket_path, expected',
    [
        ('foo', 'tcp', 27199, '', 'foo:27199'),
        ('bar', 'ws', 6789, '', 'wss://bar:6789'),
        ('mal', 'ws', 6789, 'path', 'wss://mal:6789/path'),
        ('example.com', 'ws', 443, 'path', 'wss://example.com:443/path'),
    ],
)
def test_get_full_address(address, protocol, port, websocket_path, expected):
    receptor_address = ReceptorAddress(address=address, protocol=protocol, port=port, websocket_path=websocket_path)
    assert receptor_address.get_full_address() == expected


@pytest.mark.parametrize(
    'protocol, expected',
    [
        ('tcp', 'tcp-peer'),
        ('ws', 'ws-peer'),
        ('wss', 'ws-peer'),
        ('foo', None),
    ],
)
def test_get_peer_type(protocol, expected):
    receptor_address = ReceptorAddress(protocol=protocol)
    assert receptor_address.get_peer_type() == expected
