# Copyright 2011 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from novaclient import base
from novaclient import utils


class VirtualInterface(base.Resource):
    def create(self):
        self.manager.create()


class VirtualInterfaceManager(base.ManagerWithFind):
    resource_class = base.Resource

    def list(self, instance_id):
        return self._list("/servers/%s/os-virtual-interfacesv2" % instance_id,
                         "virtual_interfaces")

    def create(self, network_id, instance_id):
        body = {'virtual_interface': {'network_id': network_id}}
        return self._create('/servers/%s/os-virtual-interfacesv2' %
                            instance_id,
                            body, 'virtual_interfaces', return_raw=True)

    def delete(self, instance_id, interface_id):
        return self._delete('/servers/%s/os-virtual-interfacesv2/%s' %
                            (instance_id, interface_id))


def ip_dict_formatter(ip_dict):
    net_id = ip_dict["network_id"]
    ip_addr = ip_dict["address"]
    label = ip_dict["network_label"]
    return "label=%s, network_id=%s, ip_address=%s" % (label,
                                                       net_id, ip_addr)


def ip_address_formatter(field):
    addresses = [ip_dict_formatter(addr) for addr in field.ip_addresses]
    return ",".join(addresses)


@utils.arg('instance_id', metavar='<instance_id>',
           help="ID of the instance you want to display virtual"
                "interfaces for")
def do_virtual_interface_list(cs, args):
    """
    Lists the virtual interfaces for a specified server instance
    """
    vifs = cs.os_virtual_interfacesv2_python_novaclient_ext.list(
                                                        args.instance_id)
    utils.print_list(vifs, ["id", "mac_address", "ip_addresses"],
                     formatters={"ip_addresses": ip_address_formatter})


@utils.arg('network_id', metavar='<network_id>',
           help='Network ID to connect the new virtual interface to')
@utils.arg('instance_id', metavar='<instance_id>',
           help="Instance to attach the new virtual interface to")
def do_virtual_interface_create(cs, args):
    """
    Add a new virtual interface to an instance
    """
    addresses = cs.os_virtual_interfacesv2_python_novaclient_ext.create(
                                                             args.network_id,
                                                             args.instance_id)
    for address in addresses:
        addr_list = [ip_dict_formatter(a) for a in address["ip_addresses"]]
        addr_dict = {"id": address["id"],
                     "mac_address": address["mac_address"],
                     "ip_addresses": ','.join(addr_list)}
        utils.print_dict(addr_dict)


@utils.arg('instance_id', metavar='<instance_id>',
           help="Instance to remove the virtual interface from")
@utils.arg('interface_id', metavar='<interface_id>',
           help='ID of the virtual interface to delete')
def do_virtual_interface_delete(cs, args):
    """
    Removes the specified virtual interface from an instance
    """
    cs.os_virtual_interfacesv2_python_novaclient_ext.delete(args.instance_id,
                                                          args.interface_id)
