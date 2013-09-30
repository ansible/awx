# Copyright 2011 OpenStack Foundation
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

"""
Keypair interface (1.1 extension).
"""

from novaclient import base


class Keypair(base.Resource):
    """
    A keypair is a ssh key that can be injected into a server on launch.
    """

    def __repr__(self):
        return "<Keypair: %s>" % self.id

    def _add_details(self, info):
        dico = 'keypair' in info and \
            info['keypair'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)

    @property
    def id(self):
        return self.name

    def delete(self):
        self.manager.delete(self)


class KeypairManager(base.ManagerWithFind):
    resource_class = Keypair

    def get(self, keypair):
        """
        Get a keypair.

        :param keypair: The ID of the keypair to get.
        :rtype: :class:`Keypair`
        """
        return self._get("/os-keypairs/%s" % base.getid(keypair), "keypair")

    def create(self, name, public_key=None):
        """
        Create a keypair

        :param name: name for the keypair to create
        :param public_key: existing public key to import
        """
        body = {'keypair': {'name': name}}
        if public_key:
            body['keypair']['public_key'] = public_key
        return self._create('/os-keypairs', body, 'keypair')

    def delete(self, key):
        """
        Delete a keypair

        :param key: The :class:`Keypair` (or its ID) to delete.
        """
        self._delete('/os-keypairs/%s' % (base.getid(key)))

    def list(self):
        """
        Get a list of keypairs.
        """
        return self._list('/os-keypairs', 'keypairs')
