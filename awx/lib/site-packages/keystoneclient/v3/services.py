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
from keystoneclient import utils


class Service(base.Resource):
    """Represents an Identity service.

    Attributes:
        * id: a uuid that identifies the service
        * name: user-facing name of the service (e.g. Keystone)
        * type: 'compute', 'identity', etc
        * enabled: determines whether the service appears in the catalog

    """
    pass


class ServiceManager(base.CrudManager):
    """Manager class for manipulating Identity services."""
    resource_class = Service
    collection_key = 'services'
    key = 'service'

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, name, type, enabled=True, description=None, **kwargs):
        return super(ServiceManager, self).create(
            name=name,
            type=type,
            description=description,
            enabled=enabled,
            **kwargs)

    def get(self, service):
        return super(ServiceManager, self).get(
            service_id=base.getid(service))

    @utils.positional(enforcement=utils.positional.WARN)
    def list(self, name=None, type=None, **kwargs):
        return super(ServiceManager, self).list(
            name=name,
            type=type,
            **kwargs)

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, service, name=None, type=None, enabled=None,
               description=None, **kwargs):
        return super(ServiceManager, self).update(
            service_id=base.getid(service),
            name=name,
            type=type,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, service):
        return super(ServiceManager, self).delete(
            service_id=base.getid(service))
