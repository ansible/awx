# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Voxel VoxCloud driver
"""
import datetime
import hashlib

from libcloud.utils.py3 import b

from libcloud.common.base import XmlResponse, ConnectionUserAndKey
from libcloud.common.types import InvalidCredsError
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.base import NodeSize, NodeImage, NodeLocation

VOXEL_API_HOST = "api.voxel.net"


class VoxelResponse(XmlResponse):
    def __init__(self, response, connection):
        self.parsed = None
        super(VoxelResponse, self).__init__(response=response,
                                            connection=connection)

    def parse_body(self):
        if not self.body:
            return None
        if not self.parsed:
            self.parsed = super(VoxelResponse, self).parse_body()
        return self.parsed

    def parse_error(self):
        err_list = []
        if not self.body:
            return None
        if not self.parsed:
            self.parsed = super(VoxelResponse, self).parse_body()
        for err in self.parsed.findall('err'):
            code = err.get('code')
            err_list.append("(%s) %s" % (code, err.get('msg')))
            # From voxel docs:
            # 1: Invalid login or password
            # 9: Permission denied: user lacks access rights for this method
            if code == "1" or code == "9":
                # sucks, but only way to detect
                # bad authentication tokens so far
                raise InvalidCredsError(err_list[-1])
        return "\n".join(err_list)

    def success(self):
        if not self.parsed:
            self.parsed = super(VoxelResponse, self).parse_body()
        stat = self.parsed.get('stat')
        if stat != "ok":
            return False
        return True


class VoxelConnection(ConnectionUserAndKey):
    """
    Connection class for the Voxel driver
    """

    host = VOXEL_API_HOST
    responseCls = VoxelResponse

    def add_default_params(self, params):
        params = dict([(k, v) for k, v in list(params.items())
                       if v is not None])
        params["key"] = self.user_id
        params["timestamp"] = datetime.datetime.utcnow().isoformat() + "+0000"

        keys = list(params.keys())
        keys.sort()

        md5 = hashlib.md5()
        md5.update(b(self.key))
        for key in keys:
            if params[key]:
                if not params[key] is None:
                    md5.update(b("%s%s" % (key, params[key])))
                else:
                    md5.update(b(key))
        params['api_sig'] = md5.hexdigest()
        return params

VOXEL_INSTANCE_TYPES = {}
RAM_PER_CPU = 2048

NODE_STATE_MAP = {
    'IN_PROGRESS': NodeState.PENDING,
    'QUEUED': NodeState.PENDING,
    'SUCCEEDED': NodeState.RUNNING,
    'shutting-down': NodeState.TERMINATED,
    'terminated': NodeState.TERMINATED,
    'unknown': NodeState.UNKNOWN,
}


class VoxelNodeDriver(NodeDriver):
    """
    Voxel VoxCLOUD node driver
    """

    connectionCls = VoxelConnection
    type = Provider.VOXEL
    name = 'Voxel VoxCLOUD'
    website = 'http://www.voxel.net/'

    def _initialize_instance_types():
        for cpus in range(1, 14):
            if cpus == 1:
                name = "Single CPU"
            else:
                name = "%d CPUs" % cpus
            id = "%dcpu" % cpus
            ram = cpus * RAM_PER_CPU

            VOXEL_INSTANCE_TYPES[id] = {
                'id': id,
                'name': name,
                'ram': ram,
                'disk': None,
                'bandwidth': None,
                'price': None}

    features = {"create_node": [],
                "list_sizes": ["variable_disk"]}

    _initialize_instance_types()

    def list_nodes(self):
        params = {"method": "voxel.devices.list"}
        result = self.connection.request('/', params=params).object
        return self._to_nodes(result)

    def list_sizes(self, location=None):
        return [NodeSize(driver=self.connection.driver, **i)
                for i in list(VOXEL_INSTANCE_TYPES.values())]

    def list_images(self, location=None):
        params = {"method": "voxel.images.list"}
        result = self.connection.request('/', params=params).object
        return self._to_images(result)

    def create_node(self, **kwargs):
        """Create Voxel Node

        :keyword name: the name to assign the node (mandatory)
        :type    name: ``str``

        :keyword image: distribution to deploy
        :type    image: :class:`NodeImage`

        :keyword size: the plan size to create (mandatory)
                       Requires size.disk (GB) to be set manually
        :type    size: :class:`NodeSize`

        :keyword location: which datacenter to create the node in
        :type    location: :class:`NodeLocation`

        :keyword ex_privateip: Backend IP address to assign to node;
                               must be chosen from the customer's
                               private VLAN assignment.
        :type    ex_privateip: ``str``

        :keyword ex_publicip: Public-facing IP address to assign to node;
                              must be chosen from the customer's
                              public VLAN assignment.
        :type    ex_publicip: ``str``

        :keyword ex_rootpass: Password for root access; generated if unset.
        :type    ex_rootpass: ``str``

        :keyword ex_consolepass: Password for remote console;
                                 generated if unset.
        :type    ex_consolepass: ``str``

        :keyword ex_sshuser: Username for SSH access
        :type    ex_sshuser: ``str``

        :keyword ex_sshpass: Password for SSH access; generated if unset.
        :type    ex_sshpass: ``str``

        :keyword ex_voxel_access: Allow access Voxel administrative access.
                                  Defaults to False.
        :type    ex_voxel_access: ``bool``

        :rtype: :class:`Node` or ``None``
        """

        # assert that disk > 0
        if not kwargs["size"].disk:
            raise ValueError("size.disk must be non-zero")

        # convert voxel_access to string boolean if needed
        voxel_access = kwargs.get("ex_voxel_access", None)
        if voxel_access is not None:
            voxel_access = "true" if voxel_access else "false"

        params = {
            'method': 'voxel.voxcloud.create',
            'hostname': kwargs["name"],
            'disk_size': int(kwargs["size"].disk),
            'facility': kwargs["location"].id,
            'image_id': kwargs["image"].id,
            'processing_cores': kwargs["size"].ram / RAM_PER_CPU,
            'backend_ip': kwargs.get("ex_privateip", None),
            'frontend_ip': kwargs.get("ex_publicip", None),
            'admin_password': kwargs.get("ex_rootpass", None),
            'console_password': kwargs.get("ex_consolepass", None),
            'ssh_username': kwargs.get("ex_sshuser", None),
            'ssh_password': kwargs.get("ex_sshpass", None),
            'voxel_access': voxel_access,
        }

        object = self.connection.request('/', params=params).object

        if self._getstatus(object):
            return Node(
                id=object.findtext("device/id"),
                name=kwargs["name"],
                state=NODE_STATE_MAP[object.findtext("device/status")],
                public_ips=kwargs.get("publicip", None),
                private_ips=kwargs.get("privateip", None),
                driver=self.connection.driver
            )
        else:
            return None

    def reboot_node(self, node):
        params = {'method': 'voxel.devices.power',
                  'device_id': node.id,
                  'power_action': 'reboot'}
        return self._getstatus(
            self.connection.request('/', params=params).object)

    def destroy_node(self, node):
        params = {'method': 'voxel.voxcloud.delete',
                  'device_id': node.id}
        return self._getstatus(
            self.connection.request('/', params=params).object)

    def list_locations(self):
        params = {"method": "voxel.voxcloud.facilities.list"}
        result = self.connection.request('/', params=params).object
        nodes = self._to_locations(result)
        return nodes

    def _getstatus(self, element):
        status = element.attrib["stat"]
        return status == "ok"

    def _to_locations(self, object):
        return [NodeLocation(element.attrib["label"],
                             element.findtext("description"),
                             element.findtext("description"),
                             self)
                for element in object.findall('facilities/facility')]

    def _to_nodes(self, object):
        nodes = []
        for element in object.findall('devices/device'):
            if element.findtext("type") == "Virtual Server":
                try:
                    state = self.NODE_STATE_MAP[element.attrib['status']]
                except KeyError:
                    state = NodeState.UNKNOWN

                public_ip = private_ip = None
                ipassignments = element.findall("ipassignments/ipassignment")
                for ip in ipassignments:
                    if ip.attrib["type"] == "frontend":
                        public_ip = ip.text
                    elif ip.attrib["type"] == "backend":
                        private_ip = ip.text

                nodes.append(Node(id=element.attrib['id'],
                                  name=element.attrib['label'],
                                  state=state,
                                  public_ips=public_ip,
                                  private_ips=private_ip,
                                  driver=self.connection.driver))
        return nodes

    def _to_images(self, object):
        images = []
        for element in object.findall("images/image"):
            images.append(NodeImage(id=element.attrib["id"],
                                    name=element.attrib["summary"],
                                    driver=self.connection.driver))
        return images
