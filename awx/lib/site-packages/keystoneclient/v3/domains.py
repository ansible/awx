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


class Domain(base.Resource):
    """Represents an Identity domain.

    Attributes:
        * id: a uuid that identifies the domain

    """
    pass


class DomainManager(base.CrudManager):
    """Manager class for manipulating Identity domains."""
    resource_class = Domain
    collection_key = 'domains'
    key = 'domain'

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, name, description=None, enabled=True, **kwargs):
        return super(DomainManager, self).create(
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def get(self, domain):
        return super(DomainManager, self).get(
            domain_id=base.getid(domain))

    def list(self, **kwargs):
        """List domains.

        ``**kwargs`` allows filter criteria to be passed where
         supported by the server.
        """
        # Ref bug #1267530 we have to pass 0 for False to get the expected
        # results on all keystone versions
        if kwargs.get('enabled') is False:
            kwargs['enabled'] = 0
        return super(DomainManager, self).list(**kwargs)

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, domain, name=None,
               description=None, enabled=None, **kwargs):
        return super(DomainManager, self).update(
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, domain):
        return super(DomainManager, self).delete(
            domain_id=base.getid(domain))
