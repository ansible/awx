# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.


# DRF
from rest_framework.request import Request

"""
Note that these methods operate on request.environ. This data is from uwsgi.
It is the source data from which request.headers (read-only) is constructed.
"""


def is_proxy_in_headers(request: Request, proxy_list: list[str], headers: list[str]) -> bool:
    """
    Determine if the request went through at least one proxy in the list.
    Example:
    request.environ = {
        "HTTP_X_FOO": "8.8.8.8, 192.168.2.1",
        "REMOTE_ADDR": "192.168.2.1",
        "REMOTE_HOST": "foobar"
    }
    proxy_list = ["192.168.2.1"]
    headers = ["HTTP_X_FOO", "REMOTE_ADDR", "REMOTE_HOST"]

    The above would return True since 192.168.2.1 is a value for the header HTTP_X_FOO

    request: The DRF/Django request. request.environ dict will be used for searching for proxies
    proxy_list: A list of known and trusted proxies may be ip or hostnames
    headers: A list of keys for which to consider values that may contain a proxy
    """

    remote_hosts = set()

    for header in headers:
        for value in request.environ.get(header, '').split(','):
            value = value.strip()
            if value:
                remote_hosts.add(value)

    return bool(remote_hosts.intersection(set(proxy_list)))


def delete_headers_starting_with_http(request: Request, headers: list[str]):
    for header in headers:
        if header.startswith('HTTP_'):
            request.environ.pop(header, None)


def get_first_remote_host_from_headers(request: Request, headers: list[str]) -> set[str]:
    """
    Extract remote host addresses from headers, considering only the first entry
    in comma-separated values.

    For headers like X-Forwarded-For that may contain multiple IPs (e.g., "client, proxy1, proxy2"),
    only the first entry (the original client) is considered.

    Example:
    request.environ = {
        "HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1, 172.16.0.1",
        "REMOTE_ADDR": "192.168.1.1",
        "REMOTE_HOST": "proxy.example.com"
    }
    headers = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR", "REMOTE_HOST"]

    Returns: {"10.0.0.1", "192.168.1.1", "proxy.example.com"}
    (Only the first IP "10.0.0.1" from X-Forwarded-For, not the full chain)

    request: The DRF/Django request. request.environ dict will be used for extracting hosts
    headers: A list of header keys to check for remote host values
    """
    remote_hosts = set()

    for header in headers:
        header_value = request.environ.get(header, '')
        if header_value:
            # Only take the first entry if comma-separated
            first_value = header_value.split(',')[0].strip()
            if first_value:
                remote_hosts.add(first_value)

    return remote_hosts
