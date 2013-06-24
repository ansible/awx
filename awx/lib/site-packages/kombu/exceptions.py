"""
kombu.exceptions
================

Exceptions.

"""
from __future__ import absolute_import

import socket

__all__ = ['NotBoundError', 'MessageStateError', 'TimeoutError',
           'LimitExceeded', 'ConnectionLimitExceeded',
           'ChannelLimitExceeded', 'StdConnectionError',
           'StdChannelError', 'VersionMismatch', 'SerializerNotInstalled']

TimeoutError = socket.timeout


class KombuError(Exception):
    """Common subclass for all Kombu exceptions."""


class NotBoundError(KombuError):
    """Trying to call channel dependent method on unbound entity."""
    pass


class MessageStateError(KombuError):
    """The message has already been acknowledged."""
    pass


class LimitExceeded(KombuError):
    """Limit exceeded."""
    pass


class ConnectionLimitExceeded(LimitExceeded):
    """Maximum number of simultaneous connections exceeded."""
    pass


class ChannelLimitExceeded(LimitExceeded):
    """Maximum number of simultaneous channels exceeded."""
    pass


class StdConnectionError(KombuError):
    pass


class StdChannelError(KombuError):
    pass


class VersionMismatch(KombuError):
    pass


class SerializerNotInstalled(KombuError):
    """Support for the requested serialization type is not installed"""
    pass


class ContentDisallowed(SerializerNotInstalled):
    """Consumer does not allow this content-type."""
    pass


class InconsistencyError(StdConnectionError):
    """Data or environment has been found to be inconsistent,
    depending on the cause it may be possible to retry the operation."""
    pass
