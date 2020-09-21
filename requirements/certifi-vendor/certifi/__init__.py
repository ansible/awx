# -*- coding: utf-8 -*-

"""
(fake) certifi
~~~~~~~~~~~~~~

A minimal, system-CA-store-only, implementation of certifi.
"""


def where():
    """Return the absolute path to the system CA bundle."""
    return '/etc/pki/tls/certs/ca-bundle.crt'


def contents():
    with open(where(), "r", encoding="utf-8") as data:
        return data.read()
