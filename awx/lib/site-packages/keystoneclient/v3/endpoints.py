# Copyright 2011 OpenStack Foundation
# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _
from keystoneclient import utils


VALID_INTERFACES = ['public', 'admin', 'internal']


class Endpoint(base.Resource):
    """Represents an Identity endpoint.

    Attributes:
        * id: a uuid that identifies the endpoint
        * interface: 'public', 'admin' or 'internal' network interface
        * region: geographic location of the endpoint
        * service_id: service to which the endpoint belongs
        * url: fully qualified service endpoint
        * enabled: determines whether the endpoint appears in the catalog

    """
    pass


class EndpointManager(base.CrudManager):
    """Manager class for manipulating Identity endpoints."""
    resource_class = Endpoint
    collection_key = 'endpoints'
    key = 'endpoint'

    def _validate_interface(self, interface):
        if interface is not None and interface not in VALID_INTERFACES:
            msg = _('"interface" must be one of: %s')
            msg = msg % ', '.join(VALID_INTERFACES)
            raise exceptions.ValidationError(msg)

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, service, url, interface=None, region=None, enabled=True,
               **kwargs):
        self._validate_interface(interface)
        return super(EndpointManager, self).create(
            service_id=base.getid(service),
            interface=interface,
            url=url,
            region=region,
            enabled=enabled,
            **kwargs)

    def get(self, endpoint):
        return super(EndpointManager, self).get(
            endpoint_id=base.getid(endpoint))

    @utils.positional(enforcement=utils.positional.WARN)
    def list(self, service=None, interface=None, region=None, enabled=None,
             **kwargs):
        """List endpoints.

        If ``**kwargs`` are provided, then filter endpoints with
        attributes matching ``**kwargs``.
        """
        self._validate_interface(interface)
        return super(EndpointManager, self).list(
            service_id=base.getid(service),
            interface=interface,
            region=region,
            enabled=enabled,
            **kwargs)

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, endpoint, service=None, url=None, interface=None,
               region=None, enabled=None, **kwargs):
        self._validate_interface(interface)
        return super(EndpointManager, self).update(
            endpoint_id=base.getid(endpoint),
            service_id=base.getid(service),
            interface=interface,
            url=url,
            region=region,
            enabled=enabled,
            **kwargs)

    def delete(self, endpoint):
        return super(EndpointManager, self).delete(
            endpoint_id=base.getid(endpoint))
