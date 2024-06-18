# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.


# DRF
from rest_framework.request import Request


"""
Note that these methods operate on request.environ. This data is from uwsgi.
It is the source data from which request.headers (read-only) is constructed.
"""


def is_proxy_in_headers(request: Request, proxy_list: list[str], headers: list[str]) -> bool:
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
