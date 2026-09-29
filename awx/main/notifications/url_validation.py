import ipaddress
import logging
import socket
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger('awx.main.notifications.url_validation')


class SSRFBlockedError(Exception):
    pass


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
    unless the resolved IP or hostname is in NOTIFICATION_IP_ALLOW_LIST."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError(f"Notification URL has no hostname: {url}")

    allow_list = getattr(settings, 'NOTIFICATION_IP_ALLOW_LIST', [])

    if _is_hostname_allowed(hostname, allow_list):
        return url

    try:
        addrinfo = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SSRFBlockedError(f"Cannot resolve notification URL hostname {hostname!r}: {e}")

    for family, _, _, _, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            if not _is_ip_allowed(ip, allow_list):
                raise SSRFBlockedError(f"Notification URL {hostname!r} resolves to blocked address {ip}")

    return url


def get_hostname(url):
    return urlparse(url).hostname
