import ipaddress
import logging
import socket
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger('awx.main.notifications.url_validation')

# Link-local addresses are always blocked regardless of allowlist settings.
# Protects cloud metadata endpoints (169.254.169.254) even if DNS is subverted
# for an allowlisted hostname.
_DENY_NETWORKS = (
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('fe80::/10'),
)


class SSRFBlockedError(Exception):
    pass


def _is_always_denied(ip):
    check_ip = getattr(ip, 'ipv4_mapped', None) or ip
    for net in _DENY_NETWORKS:
        if check_ip in net:
            return True
    return False


def _is_ip_allowed(ip, allow_list):
    for entry in allow_list:
        try:
            if ip in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            pass
    return False


def _is_hostname_allowed(hostname, allow_list):
    hostname = hostname.lower()
    for entry in allow_list:
        try:
            ipaddress.ip_network(entry, strict=False)
            continue
        except ValueError:
            pass
        entry = entry.lower()
        if hostname == entry:
            return True
        # ".example.com" matches "foo.example.com" but not "example.com"
        if entry.startswith('.') and hostname.endswith(entry):
            return True
    return False


def validate_url(url):
    """Resolve the URL's hostname and reject private, loopback, and link-local addresses
    unless the resolved IP or hostname is in NOTIFICATION_IP_ALLOW_LIST.
    Link-local addresses (169.254.0.0/16, fe80::/10) are always blocked."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError(f"Notification URL has no hostname: {url}")

    allow_list = getattr(settings, 'NOTIFICATION_IP_ALLOW_LIST', [])
    hostname_allowed = _is_hostname_allowed(hostname, allow_list)

    try:
        addrinfo = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        if hostname_allowed:
            return url
        raise SSRFBlockedError(f"Cannot resolve notification URL hostname {hostname!r}: {e}")

    for family, _, _, _, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if _is_always_denied(ip):
            raise SSRFBlockedError(f"Notification URL {hostname!r} resolves to link-local address {ip} (always blocked)")
        if not hostname_allowed:
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                if not _is_ip_allowed(ip, allow_list):
                    raise SSRFBlockedError(f"Notification URL {hostname!r} resolves to blocked address {ip}")

    return url


def get_hostname(url):
    return urlparse(url).hostname
