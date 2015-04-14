# Copyright (c) 2013 The Johns Hopkins University/Applied Physics Laboratory
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
Volume Encryption Type interface
"""

from cinderclient import base


class VolumeEncryptionType(base.Resource):
    """
    A Volume Encryption Type is a collection of settings used to conduct
    encryption for a specific volume type.
    """
    def __repr__(self):
        return "<VolumeEncryptionType: %s>" % self.name


class VolumeEncryptionTypeManager(base.ManagerWithFind):
    """
    Manage :class: `VolumeEncryptionType` resources.
    """
    resource_class = VolumeEncryptionType

    def list(self, search_opts=None):
        """
        List all volume encryption types.

        :param volume_types: a list of volume types
        :return: a list of :class: VolumeEncryptionType instances
        """
        # Since the encryption type is a volume type extension, we cannot get
        # all encryption types without going through all volume types.
        volume_types = self.api.volume_types.list()
        encryption_types = []
        for volume_type in volume_types:
            encryption_type = self._get("/types/%s/encryption"
                                        % base.getid(volume_type))
            if hasattr(encryption_type, 'volume_type_id'):
                encryption_types.append(encryption_type)
        return encryption_types

    def get(self, volume_type):
        """
        Get the volume encryption type for the specified volume type.

        :param volume_type: the volume type to query
        :return: an instance of :class: VolumeEncryptionType
        """
        return self._get("/types/%s/encryption" % base.getid(volume_type))

    def create(self, volume_type, specs):
        """
        Creates encryption type for a volume type. Default: admin only.

        :param volume_type: the volume type on which to add an encryption type
        :param specs: the encryption type specifications to add
        :return: an instance of :class: VolumeEncryptionType
        """
        body = {'encryption': specs}
        return self._create("/types/%s/encryption" % base.getid(volume_type),
                            body, "encryption")

    def update(self, volume_type, specs):
        """
        Update the encryption type information for the specified volume type.

        :param volume_type: the volume type whose encryption type information
                            must be updated
        :param specs: the encryption type specifications to update
        :return: an instance of :class: VolumeEncryptionType
        """
        raise NotImplementedError()

    def delete(self, volume_type):
        """
        Delete the encryption type information for the specified volume type.

        :param volume_type: the volume type whose encryption type information
                            must be deleted
        """
        return self._delete("/types/%s/encryption/provider" %
                            base.getid(volume_type))
