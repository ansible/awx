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

"""libcloud driver for the Linode(R) API

This driver implements all libcloud functionality for the Linode API.
Since the API is a bit more fine-grained, create_node abstracts a significant
amount of work (and may take a while to run).

Linode home page                    http://www.linode.com/
Linode API documentation            http://www.linode.com/api/
Alternate bindings for reference    http://github.com/tjfontaine/linode-python

Linode(R) is a registered trademark of Linode, LLC.

"""

import os

try:
    import simplejson as json
except ImportError:
    import json

import itertools
import binascii

from copy import copy

from libcloud.utils.py3 import PY3

from libcloud.common.linode import (API_ROOT, LinodeException,
                                    LinodeConnection, LINODE_PLAN_IDS)
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.base import NodeDriver, NodeSize, Node, NodeLocation
from libcloud.compute.base import NodeAuthPassword, NodeAuthSSHKey
from libcloud.compute.base import NodeImage


class LinodeNodeDriver(NodeDriver):
    """libcloud driver for the Linode API

    Rough mapping of which is which:

        list_nodes              linode.list
        reboot_node             linode.reboot
        destroy_node            linode.delete
        create_node             linode.create, linode.update,
                                linode.disk.createfromdistribution,
                                linode.disk.create, linode.config.create,
                                linode.ip.addprivate, linode.boot
        list_sizes              avail.linodeplans
        list_images             avail.distributions
        list_locations          avail.datacenters

    For more information on the Linode API, be sure to read the reference:

        http://www.linode.com/api/
    """
    type = Provider.LINODE
    name = "Linode"
    website = 'http://www.linode.com/'
    connectionCls = LinodeConnection
    _linode_plan_ids = LINODE_PLAN_IDS
    features = {'create_node': ['ssh_key', 'password']}

    def __init__(self, key):
        """Instantiate the driver with the given API key

        :param   key: the API key to use (required)
        :type    key: ``str``

        :rtype: ``None``
        """
        self.datacenter = None
        NodeDriver.__init__(self, key)

    # Converts Linode's state from DB to a NodeState constant.
    LINODE_STATES = {
        (-2): NodeState.UNKNOWN,    # Boot Failed
        (-1): NodeState.PENDING,    # Being Created
        0: NodeState.PENDING,     # Brand New
        1: NodeState.RUNNING,     # Running
        2: NodeState.TERMINATED,  # Powered Off
        3: NodeState.REBOOTING,   # Shutting Down
        4: NodeState.UNKNOWN      # Reserved
    }

    def list_nodes(self):
        """
        List all Linodes that the API key can access

        This call will return all Linodes that the API key in use has access
         to.
        If a node is in this list, rebooting will work; however, creation and
        destruction are a separate grant.

        :return: List of node objects that the API key can access
        :rtype: ``list`` of :class:`Node`
        """
        params = {"api_action": "linode.list"}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        return self._to_nodes(data)

    def reboot_node(self, node):
        """
        Reboot the given Linode

        Will issue a shutdown job followed by a boot job, using the last booted
        configuration.  In most cases, this will be the only configuration.

        :param      node: the Linode to reboot
        :type       node: :class:`Node`

        :rtype: ``bool``
        """
        params = {"api_action": "linode.reboot", "LinodeID": node.id}
        self.connection.request(API_ROOT, params=params)
        return True

    def destroy_node(self, node):
        """Destroy the given Linode

        Will remove the Linode from the account and issue a prorated credit. A
        grant for removing Linodes from the account is required, otherwise this
        method will fail.

        In most cases, all disk images must be removed from a Linode before the
        Linode can be removed; however, this call explicitly skips those
        safeguards. There is no going back from this method.

        :param       node: the Linode to destroy
        :type        node: :class:`Node`

        :rtype: ``bool``
        """
        params = {"api_action": "linode.delete", "LinodeID": node.id,
                  "skipChecks": True}
        self.connection.request(API_ROOT, params=params)
        return True

    def create_node(self, **kwargs):
        """Create a new Linode, deploy a Linux distribution, and boot

        This call abstracts much of the functionality of provisioning a Linode
        and getting it booted.  A global grant to add Linodes to the account is
        required, as this call will result in a billing charge.

        Note that there is a safety valve of 5 Linodes per hour, in order to
        prevent a runaway script from ruining your day.

        :keyword name: the name to assign the Linode (mandatory)
        :type    name: ``str``

        :keyword image: which distribution to deploy on the Linode (mandatory)
        :type    image: :class:`NodeImage`

        :keyword size: the plan size to create (mandatory)
        :type    size: :class:`NodeSize`

        :keyword auth: an SSH key or root password (mandatory)
        :type    auth: :class:`NodeAuthSSHKey` or :class:`NodeAuthPassword`

        :keyword location: which datacenter to create the Linode in
        :type    location: :class:`NodeLocation`

        :keyword ex_swap: size of the swap partition in MB (128)
        :type    ex_swap: ``int``

        :keyword ex_rsize: size of the root partition in MB (plan size - swap).
        :type    ex_rsize: ``int``

        :keyword ex_kernel: a kernel ID from avail.kernels (Latest 2.6 Stable).
        :type    ex_kernel: ``str``

        :keyword ex_payment: one of 1, 12, or 24; subscription length (1)
        :type    ex_payment: ``int``

        :keyword ex_comment: a small comment for the configuration (libcloud)
        :type    ex_comment: ``str``

        :keyword ex_private: whether or not to request a private IP (False)
        :type    ex_private: ``bool``

        :keyword lconfig: what to call the configuration (generated)
        :type    lconfig: ``str``

        :keyword lroot: what to call the root image (generated)
        :type    lroot: ``str``

        :keyword lswap: what to call the swap space (generated)
        :type    lswap: ``str``

        :return: Node representing the newly-created Linode
        :rtype: :class:`Node`
        """
        name = kwargs["name"]
        image = kwargs["image"]
        size = kwargs["size"]
        auth = self._get_and_check_auth(kwargs["auth"])

        # Pick a location (resolves LIBCLOUD-41 in JIRA)
        if "location" in kwargs:
            chosen = kwargs["location"].id
        elif self.datacenter:
            chosen = self.datacenter
        else:
            raise LinodeException(0xFB, "Need to select a datacenter first")

        # Step 0: Parameter validation before we purchase
        # We're especially careful here so we don't fail after purchase, rather
        # than getting halfway through the process and having the API fail.

        # Plan ID
        plans = self.list_sizes()
        if size.id not in [p.id for p in plans]:
            raise LinodeException(0xFB, "Invalid plan ID -- avail.plans")

        # Payment schedule
        payment = "1" if "ex_payment" not in kwargs else \
            str(kwargs["ex_payment"])
        if payment not in ["1", "12", "24"]:
            raise LinodeException(0xFB, "Invalid subscription (1, 12, 24)")

        ssh = None
        root = None
        # SSH key and/or root password
        if isinstance(auth, NodeAuthSSHKey):
            ssh = auth.pubkey
        elif isinstance(auth, NodeAuthPassword):
            root = auth.password

        if not ssh and not root:
            raise LinodeException(0xFB, "Need SSH key or root password")
        if root is not None and len(root) < 6:
            raise LinodeException(0xFB, "Root password is too short")

        # Swap size
        try:
            swap = 128 if "ex_swap" not in kwargs else int(kwargs["ex_swap"])
        except:
            raise LinodeException(0xFB, "Need an integer swap size")

        # Root partition size
        imagesize = (size.disk - swap) if "ex_rsize" not in kwargs else\
            int(kwargs["ex_rsize"])
        if (imagesize + swap) > size.disk:
            raise LinodeException(0xFB, "Total disk images are too big")

        # Distribution ID
        distros = self.list_images()
        if image.id not in [d.id for d in distros]:
            raise LinodeException(0xFB,
                                  "Invalid distro -- avail.distributions")

        # Kernel
        if "ex_kernel" in kwargs:
            kernel = kwargs["ex_kernel"]
        else:
            if image.extra['64bit']:
                # For a list of available kernel ids, see
                # https://www.linode.com/kernels/
                kernel = 138
            else:
                kernel = 137
        params = {"api_action": "avail.kernels"}
        kernels = self.connection.request(API_ROOT, params=params).objects[0]
        if kernel not in [z["KERNELID"] for z in kernels]:
            raise LinodeException(0xFB, "Invalid kernel -- avail.kernels")

        # Comments
        comments = "Created by Apache libcloud <http://www.libcloud.org>" if\
            "ex_comment" not in kwargs else kwargs["ex_comment"]

        # Step 1: linode.create
        params = {
            "api_action": "linode.create",
            "DatacenterID": chosen,
            "PlanID": size.id,
            "PaymentTerm": payment
        }
        data = self.connection.request(API_ROOT, params=params).objects[0]
        linode = {"id": data["LinodeID"]}

        # Step 1b. linode.update to rename the Linode
        params = {
            "api_action": "linode.update",
            "LinodeID": linode["id"],
            "Label": name
        }
        self.connection.request(API_ROOT, params=params)

        # Step 1c. linode.ip.addprivate if it was requested
        if "ex_private" in kwargs and kwargs["ex_private"]:
            params = {
                "api_action": "linode.ip.addprivate",
                "LinodeID": linode["id"]
            }
            self.connection.request(API_ROOT, params=params)

        # Step 1d. Labels
        # use the linode id as the name can be up to 63 chars and the labels
        # are limited to 48 chars
        label = {
            "lconfig": "[%s] Configuration Profile" % linode["id"],
            "lroot": "[%s] %s Disk Image" % (linode["id"], image.name),
            "lswap": "[%s] Swap Space" % linode["id"]
        }
        for what in ["lconfig", "lroot", "lswap"]:
            if what in kwargs:
                label[what] = kwargs[what]

        # Step 2: linode.disk.createfromdistribution
        if not root:
            root = binascii.b2a_base64(os.urandom(8)).decode('ascii').strip()

        params = {
            "api_action": "linode.disk.createfromdistribution",
            "LinodeID": linode["id"],
            "DistributionID": image.id,
            "Label": label["lroot"],
            "Size": imagesize,
            "rootPass": root,
        }
        if ssh:
            params["rootSSHKey"] = ssh
        data = self.connection.request(API_ROOT, params=params).objects[0]
        linode["rootimage"] = data["DiskID"]

        # Step 3: linode.disk.create for swap
        params = {
            "api_action": "linode.disk.create",
            "LinodeID": linode["id"],
            "Label": label["lswap"],
            "Type": "swap",
            "Size": swap
        }
        data = self.connection.request(API_ROOT, params=params).objects[0]
        linode["swapimage"] = data["DiskID"]

        # Step 4: linode.config.create for main profile
        disks = "%s,%s,,,,,,," % (linode["rootimage"], linode["swapimage"])
        params = {
            "api_action": "linode.config.create",
            "LinodeID": linode["id"],
            "KernelID": kernel,
            "Label": label["lconfig"],
            "Comments": comments,
            "DiskList": disks
        }
        data = self.connection.request(API_ROOT, params=params).objects[0]
        linode["config"] = data["ConfigID"]

        # Step 5: linode.boot
        params = {
            "api_action": "linode.boot",
            "LinodeID": linode["id"],
            "ConfigID": linode["config"]
        }
        self.connection.request(API_ROOT, params=params)

        # Make a node out of it and hand it back
        params = {"api_action": "linode.list", "LinodeID": linode["id"]}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        nodes = self._to_nodes(data)

        if len(nodes) == 1:
            node = nodes[0]
            if getattr(auth, "generated", False):
                node.extra['password'] = auth.password
            return node

        return None

    def list_sizes(self, location=None):
        """
        List available Linode plans

        Gets the sizes that can be used for creating a Linode.  Since available
        Linode plans vary per-location, this method can also be passed a
        location to filter the availability.

        :keyword location: the facility to retrieve plans in
        :type    location: :class:`NodeLocation`

        :rtype: ``list`` of :class:`NodeSize`
        """
        params = {"api_action": "avail.linodeplans"}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        sizes = []
        for obj in data:
            n = NodeSize(id=obj["PLANID"], name=obj["LABEL"], ram=obj["RAM"],
                         disk=(obj["DISK"] * 1024), bandwidth=obj["XFER"],
                         price=obj["PRICE"], driver=self.connection.driver)
            sizes.append(n)
        return sizes

    def list_images(self):
        """
        List available Linux distributions

        Retrieve all Linux distributions that can be deployed to a Linode.

        :rtype: ``list`` of :class:`NodeImage`
        """
        params = {"api_action": "avail.distributions"}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        distros = []
        for obj in data:
            i = NodeImage(id=obj["DISTRIBUTIONID"],
                          name=obj["LABEL"],
                          driver=self.connection.driver,
                          extra={'pvops': obj['REQUIRESPVOPSKERNEL'],
                                 '64bit': obj['IS64BIT']})
            distros.append(i)
        return distros

    def list_locations(self):
        """
        List available facilities for deployment

        Retrieve all facilities that a Linode can be deployed in.

        :rtype: ``list`` of :class:`NodeLocation`
        """
        params = {"api_action": "avail.datacenters"}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        nl = []
        for dc in data:
            country = None
            if "USA" in dc["LOCATION"]:
                country = "US"
            elif "UK" in dc["LOCATION"]:
                country = "GB"
            elif "JP" in dc["LOCATION"]:
                country = "JP"
            else:
                country = "??"
            nl.append(NodeLocation(dc["DATACENTERID"],
                                   dc["LOCATION"],
                                   country,
                                   self))
        return nl

    def linode_set_datacenter(self, dc):
        """
        Set the default datacenter for Linode creation

        Since Linodes must be created in a facility, this function sets the
        default that :class:`create_node` will use.  If a location keyword is
        not passed to :class:`create_node`, this method must have already been
        used.

        :keyword dc: the datacenter to create Linodes in unless specified
        :type dc: :class:`NodeLocation`

        :rtype: ``bool``
        """
        did = dc.id
        params = {"api_action": "avail.datacenters"}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        for datacenter in data:
            if did == dc["DATACENTERID"]:
                self.datacenter = did
                return

        dcs = ", ".join([d["DATACENTERID"] for d in data])
        self.datacenter = None
        raise LinodeException(0xFD, "Invalid datacenter (use one of %s)" % dcs)

    def _to_nodes(self, objs):
        """Convert returned JSON Linodes into Node instances

        :keyword objs: ``list`` of JSON dictionaries representing the Linodes
        :type objs: ``list``
        :return: ``list`` of :class:`Node`s"""

        # Get the IP addresses for the Linodes
        nodes = {}
        batch = []
        for o in objs:
            lid = o["LINODEID"]
            nodes[lid] = n = Node(id=lid, name=o["LABEL"], public_ips=[],
                                  private_ips=[],
                                  state=self.LINODE_STATES[o["STATUS"]],
                                  driver=self.connection.driver)
            n.extra = copy(o)
            n.extra["PLANID"] = self._linode_plan_ids.get(o.get("TOTALRAM"))
            batch.append({"api_action": "linode.ip.list", "LinodeID": lid})

        # Avoid batch limitation
        ip_answers = []
        args = [iter(batch)] * 25

        if PY3:
            izip_longest = itertools.zip_longest
        else:
            izip_longest = getattr(itertools, 'izip_longest', _izip_longest)

        for twenty_five in izip_longest(*args):
            twenty_five = [q for q in twenty_five if q]
            params = {"api_action": "batch",
                      "api_requestArray": json.dumps(twenty_five)}
            req = self.connection.request(API_ROOT, params=params)
            if not req.success() or len(req.objects) == 0:
                return None
            ip_answers.extend(req.objects)

        # Add the returned IPs to the nodes and return them
        for ip_list in ip_answers:
            for ip in ip_list:
                lid = ip["LINODEID"]
                which = nodes[lid].public_ips if ip["ISPUBLIC"] == 1 else\
                    nodes[lid].private_ips
                which.append(ip["IPADDRESS"])
        return list(nodes.values())


def _izip_longest(*args, **kwds):
    """Taken from Python docs

    http://docs.python.org/library/itertools.html#itertools.izip
    """

    fillvalue = kwds.get('fillvalue')

    def sentinel(counter=([fillvalue] * (len(args) - 1)).pop):
        yield counter()  # yields the fillvalue, or raises IndexError

    fillers = itertools.repeat(fillvalue)
    iters = [itertools.chain(it, sentinel(), fillers) for it in args]
    try:
        for tup in itertools.izip(*iters):
            yield tup
    except IndexError:
        pass
