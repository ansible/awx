#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import pyrax
from ..base_identity import BaseIdentity
from .. import exceptions as exc


class KeystoneIdentity(BaseIdentity):
    """
    Implements the Keystone-specific behaviors for Identity. In most
    cases you will want to create specific subclasses to implement the
    _get_auth_endpoint() method if you want to use something other
    than the config file to control your auth endpoint.
    """

    _default_region = "RegionOne"

    def _get_auth_endpoint(self):
        ep = pyrax.get_setting("auth_endpoint")
        if ep is None:
            raise exc.EndpointNotDefined("No auth endpoint has been specified.")
        return ep
