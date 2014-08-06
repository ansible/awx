#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c)2013 Rackspace US, Inc.

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

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils

# Constants to represent the 'special' network IDs.
PUBLIC_NET_ID = "00000000-0000-0000-0000-000000000000"
SERVICE_NET_ID = "11111111-1111-1111-1111-111111111111"
PSEUDO_NETWORKS = (PUBLIC_NET_ID, SERVICE_NET_ID)


def _get_server_networks(network, public=False, private=False):
    net_id = utils.get_id(network)
    ret = [{"net-id": net_id}]
    if public:
        ret.append({"net-id": PUBLIC_NET_ID})
    if private:
        ret.append({"net-id": SERVICE_NET_ID})
    return ret



class CloudNetwork(BaseResource):
    """
    This represents a network in the cloud. It can be either an isolated
    network, the public network, or the ServiceNet network.

    While resources generally use 'name' as the text identifier, the Cloud
    Networks API uses 'label' instead. This module aliases the attributes andi
    methods so that you can use either in your code.
    """
    id = None
    cidr = None
    label = None


    def _get_name(self):
        return self.label

    def _set_name(self, name):
        self.label = name

    name = property(_get_name, _set_name)


    @property
    def is_isolated(self):
        """Returns True if this is a user-defined network."""
        return self.id not in PSEUDO_NETWORKS


    def get(self):
        if not self.is_isolated:
            # These are placeholders, not actual networks
            return
        return super(CloudNetwork, self).get()


    def delete(self):
        """
        Wraps the standard delete() method to catch expected exceptions and
        raise the appropriate pyrax exceptions.
        """
        try:
            return super(CloudNetwork, self).delete()
        except exc.Forbidden as e:
            # Network is in use
            raise exc.NetworkInUse("Cannot delete a network in use by a server.")


    def get_server_networks(self, public=False, private=False):
        """
        Creates the dict of network UUIDs required by Cloud Servers when
        creating a new server with isolated networks.

        By default only this network is included. If you wish to create a
        server that has either the public (internet) or private (ServiceNet)
        networks, you have to pass those parameters in with values of True.
        """
        return _get_server_networks(self, public=public, private=private)



class CloudNetworkManager(BaseManager):
    """
    Does nothing special, but is used in testing.
    """
    def _create_body(self, name, label=None, cidr=None):
        """
        Used to create the dict required to create a network. Accepts either
        'label' or 'name' as the keyword parameter for the label attribute.
        """
        label = label or name
        body = {"network": {
                "label": label,
                "cidr": cidr,
                }}
        return body



class CloudNetworkClient(BaseClient):
    """
    This is the base client for creating and managing Cloud Networks.
    """

    def __init__(self, *args, **kwargs):
        super(CloudNetworkClient, self).__init__(*args, **kwargs)
        self.name = "Cloud Networks"
        # Constants to represent the 'special' network IDs.
        self.PUBLIC_NET_ID = PUBLIC_NET_ID
        self.SERVICE_NET_ID = SERVICE_NET_ID
        self.PSEUDO_NETWORKS = PSEUDO_NETWORKS


    def _configure_manager(self):
        """
        Creates the Manager instance to handle networks.
        """
        self._manager = CloudNetworkManager(self, resource_class=CloudNetwork,
                response_key="network", uri_base="os-networksv2")


    def create(self, label=None, name=None, cidr=None):
        """
        Wraps the basic create() call to handle specific failures.
        """
        try:
            return super(CloudNetworkClient, self).create(label=label,
                    name=name, cidr=cidr)
        except exc.BadRequest as e:
            msg = e.message
            if "too many networks" in msg:
                raise exc.NetworkCountExceeded("Cannot create network; the "
                        "maximum number of isolated networks already exist.")
            elif "does not contain enough" in msg:
                raise exc.NetworkCIDRInvalid("Networks must contain two or "
                        "more hosts; the CIDR '%s' is too restrictive." % cidr)
            elif "CIDR is malformed" in msg:
                raise exc.NetworkCIDRMalformed("The CIDR '%s' is not valid." % cidr)
            else:
                # Something unexpected
                raise


    def delete(self, network):
        """
        Wraps the standard delete() method to catch expected exceptions and
        raise the appropriate pyrax exceptions.
        """
        try:
            return super(CloudNetworkClient, self).delete(network)
        except exc.Forbidden as e:
            # Network is in use
            raise exc.NetworkInUse("Cannot delete a network in use by a server.")


    def find_network_by_label(self, label):
        """
        This is inefficient; it gets all the networks and then filters on
        the client side to find the matching name.
        """
        networks = self.list()
        match = [network for network in networks
                if network.label == label]
        if not match:
            raise exc.NetworkNotFound("No network with the label '%s' exists" %
                    label)
        elif len(match) > 1:
            raise exc.NetworkLabelNotUnique("There were %s matches for the label "
                    "'%s'." % (len(match), label))
        return match[0]
    # Create an alias using 'name'
    find_network_by_name = find_network_by_label


    def get_server_networks(self, network, public=False, private=False):
        """
        Creates the dict of network UUIDs required by Cloud Servers when
        creating a new server with isolated networks.

        By default only the specified network is included. If you wish to
        create a server that has either the public (internet) or private
        (ServiceNet) networks, you have to pass those parameters in with
        values of True.
        """
        return _get_server_networks(network, public=public, private=private)
