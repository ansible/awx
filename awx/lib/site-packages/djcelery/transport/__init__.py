"""

This module is an alias to :mod:`kombu.transport.django`

"""
from __future__ import absolute_import, unicode_literals

import kombu.transport.django as transport

__path__.extend(transport.__path__)
