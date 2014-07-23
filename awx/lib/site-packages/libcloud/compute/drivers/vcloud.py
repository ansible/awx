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
VMware vCloud driver.
"""
import copy
import sys
import re
import base64
import os
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlencode
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import b
from libcloud.utils.py3 import next

urlparse = urlparse.urlparse

import time

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from xml.parsers.expat import ExpatError

from libcloud.common.base import XmlResponse, ConnectionUserAndKey
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.compute.providers import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.base import Node, NodeDriver, NodeLocation
from libcloud.compute.base import NodeSize, NodeImage

"""
From vcloud api "The VirtualQuantity element defines the number of MB
of memory. This should be either 512 or a multiple of 1024 (1 GB)."
"""
VIRTUAL_MEMORY_VALS = [512] + [1024 * i for i in range(1, 9)]

# Default timeout (in seconds) for long running tasks
DEFAULT_TASK_COMPLETION_TIMEOUT = 600

DEFAULT_API_VERSION = '0.8'

"""
Valid vCloud API v1.5 input values.
"""
VIRTUAL_CPU_VALS_1_5 = [i for i in range(1, 9)]
FENCE_MODE_VALS_1_5 = ['bridged', 'isolated', 'natRouted']
IP_MODE_VALS_1_5 = ['POOL', 'DHCP', 'MANUAL', 'NONE']


def fixxpath(root, xpath):
    """ElementTree wants namespaces in its xpaths, so here we add them."""
    namespace, root_tag = root.tag[1:].split("}", 1)
    fixed_xpath = "/".join(["{%s}%s" % (namespace, e)
                            for e in xpath.split("/")])
    return fixed_xpath


def get_url_path(url):
    return urlparse(url.strip()).path


class Vdc(object):
    """
    Virtual datacenter (vDC) representation
    """
    def __init__(self, id, name, driver, allocation_model=None, cpu=None,
                 memory=None, storage=None):
        self.id = id
        self.name = name
        self.driver = driver
        self.allocation_model = allocation_model
        self.cpu = cpu
        self.memory = memory
        self.storage = storage

    def __repr__(self):
        return ('<Vdc: id=%s, name=%s, driver=%s  ...>'
                % (self.id, self.name, self.driver.name))


class Capacity(object):
    """
    Represents CPU, Memory or Storage capacity of vDC.
    """
    def __init__(self, limit, used, units):
        self.limit = limit
        self.used = used
        self.units = units

    def __repr__(self):
        return ('<Capacity: limit=%s, used=%s, units=%s>'
                % (self.limit, self.used, self.units))


class ControlAccess(object):
    """
    Represents control access settings of a node
    """
    class AccessLevel(object):
        READ_ONLY = 'ReadOnly'
        CHANGE = 'Change'
        FULL_CONTROL = 'FullControl'

    def __init__(self, node, everyone_access_level, subjects=None):
        self.node = node
        self.everyone_access_level = everyone_access_level
        if not subjects:
            subjects = []
        self.subjects = subjects

    def __repr__(self):
        return ('<ControlAccess: node=%s, everyone_access_level=%s, '
                'subjects=%s>'
                % (self.node, self.everyone_access_level, self.subjects))


class Subject(object):
    """
    User or group subject
    """
    def __init__(self, type, name, access_level, id=None):
        self.type = type
        self.name = name
        self.access_level = access_level
        self.id = id

    def __repr__(self):
        return ('<Subject: type=%s, name=%s, access_level=%s>'
                % (self.type, self.name, self.access_level))


class InstantiateVAppXML(object):

    def __init__(self, name, template, net_href, cpus, memory,
                 password=None, row=None, group=None):
        self.name = name
        self.template = template
        self.net_href = net_href
        self.cpus = cpus
        self.memory = memory
        self.password = password
        self.row = row
        self.group = group

        self._build_xmltree()

    def tostring(self):
        return ET.tostring(self.root)

    def _build_xmltree(self):
        self.root = self._make_instantiation_root()

        self._add_vapp_template(self.root)
        instantiation_params = ET.SubElement(self.root,
                                             "InstantiationParams")

        # product and virtual hardware
        self._make_product_section(instantiation_params)
        self._make_virtual_hardware(instantiation_params)

        network_config_section = ET.SubElement(instantiation_params,
                                               "NetworkConfigSection")

        network_config = ET.SubElement(network_config_section,
                                       "NetworkConfig")
        self._add_network_association(network_config)

    def _make_instantiation_root(self):
        return ET.Element(
            "InstantiateVAppTemplateParams",
            {'name': self.name,
             'xml:lang': 'en',
             'xmlns': "http://www.vmware.com/vcloud/v0.8",
             'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"}
        )

    def _add_vapp_template(self, parent):
        return ET.SubElement(
            parent,
            "VAppTemplate",
            {'href': self.template}
        )

    def _make_product_section(self, parent):
        prod_section = ET.SubElement(
            parent,
            "ProductSection",
            {'xmlns:q1': "http://www.vmware.com/vcloud/v0.8",
             'xmlns:ovf': "http://schemas.dmtf.org/ovf/envelope/1"}
        )

        if self.password:
            self._add_property(prod_section, 'password', self.password)

        if self.row:
            self._add_property(prod_section, 'row', self.row)

        if self.group:
            self._add_property(prod_section, 'group', self.group)

        return prod_section

    def _add_property(self, parent, ovfkey, ovfvalue):
        return ET.SubElement(
            parent,
            "Property",
            {'xmlns': 'http://schemas.dmtf.org/ovf/envelope/1',
             'ovf:key': ovfkey,
             'ovf:value': ovfvalue}
        )

    def _make_virtual_hardware(self, parent):
        vh = ET.SubElement(
            parent,
            "VirtualHardwareSection",
            {'xmlns:q1': "http://www.vmware.com/vcloud/v0.8"}
        )

        self._add_cpu(vh)
        self._add_memory(vh)

        return vh

    def _add_cpu(self, parent):
        cpu_item = ET.SubElement(
            parent,
            "Item",
            {'xmlns': "http://schemas.dmtf.org/ovf/envelope/1"}
        )
        self._add_instance_id(cpu_item, '1')
        self._add_resource_type(cpu_item, '3')
        self._add_virtual_quantity(cpu_item, self.cpus)

        return cpu_item

    def _add_memory(self, parent):
        mem_item = ET.SubElement(
            parent,
            'Item',
            {'xmlns': "http://schemas.dmtf.org/ovf/envelope/1"}
        )
        self._add_instance_id(mem_item, '2')
        self._add_resource_type(mem_item, '4')
        self._add_virtual_quantity(mem_item, self.memory)

        return mem_item

    def _add_instance_id(self, parent, id):
        elm = ET.SubElement(
            parent,
            'InstanceID',
            {'xmlns': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                      'CIM_ResourceAllocationSettingData'}
        )
        elm.text = id
        return elm

    def _add_resource_type(self, parent, type):
        elm = ET.SubElement(
            parent,
            'ResourceType',
            {'xmlns': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                      'CIM_ResourceAllocationSettingData'}
        )
        elm.text = type
        return elm

    def _add_virtual_quantity(self, parent, amount):
        elm = ET.SubElement(
            parent,
            'VirtualQuantity',
            {'xmlns': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                      'CIM_ResourceAllocationSettingData'}
        )
        elm.text = amount
        return elm

    def _add_network_association(self, parent):
        return ET.SubElement(
            parent,
            'NetworkAssociation',
            {'href': self.net_href}
        )


class VCloudResponse(XmlResponse):

    def success(self):
        return self.status in (httplib.OK, httplib.CREATED,
                               httplib.NO_CONTENT, httplib.ACCEPTED)


class VCloudConnection(ConnectionUserAndKey):

    """
    Connection class for the vCloud driver
    """

    responseCls = VCloudResponse
    token = None
    host = None

    def request(self, *args, **kwargs):
        self._get_auth_token()
        return super(VCloudConnection, self).request(*args, **kwargs)

    def check_org(self):
        # the only way to get our org is by logging in.
        self._get_auth_token()

    def _get_auth_headers(self):
        """Some providers need different headers than others"""
        return {
            'Authorization': "Basic %s" % base64.b64encode(
                b('%s:%s' % (self.user_id, self.key))).decode('utf-8'),
            'Content-Length': '0',
            'Accept': 'application/*+xml'
        }

    def _get_auth_token(self):
        if not self.token:
            conn = self.conn_classes[self.secure](self.host,
                                                  self.port)
            conn.request(method='POST', url='/api/v0.8/login',
                         headers=self._get_auth_headers())

            resp = conn.getresponse()
            headers = dict(resp.getheaders())
            body = ET.XML(resp.read())

            try:
                self.token = headers['set-cookie']
            except KeyError:
                raise InvalidCredsError()

            self.driver.org = get_url_path(
                body.find(fixxpath(body, 'Org')).get('href')
            )

    def add_default_headers(self, headers):
        headers['Cookie'] = self.token
        headers['Accept'] = 'application/*+xml'
        return headers


class VCloudNodeDriver(NodeDriver):

    """
    vCloud node driver
    """

    type = Provider.VCLOUD
    name = 'vCloud'
    website = 'http://www.vmware.com/products/vcloud/'
    connectionCls = VCloudConnection
    org = None
    _vdcs = None

    NODE_STATE_MAP = {'0': NodeState.PENDING,
                      '1': NodeState.PENDING,
                      '2': NodeState.PENDING,
                      '3': NodeState.PENDING,
                      '4': NodeState.RUNNING}

    features = {'create_node': ['password']}

    def __new__(cls, key, secret=None, secure=True, host=None, port=None,
                api_version=DEFAULT_API_VERSION, **kwargs):
        if cls is VCloudNodeDriver:
            if api_version == '0.8':
                cls = VCloudNodeDriver
            elif api_version == '1.5':
                cls = VCloud_1_5_NodeDriver
            elif api_version == '5.1':
                cls = VCloud_5_1_NodeDriver
            else:
                raise NotImplementedError(
                    "No VCloudNodeDriver found for API version %s" %
                    (api_version))
        return super(VCloudNodeDriver, cls).__new__(cls)

    @property
    def vdcs(self):
        """
        vCloud virtual data centers (vDCs).

        :return: list of vDC objects
        :rtype: ``list`` of :class:`Vdc`
        """
        if not self._vdcs:
            self.connection.check_org()  # make sure the org is set.
            res = self.connection.request(self.org)
            self._vdcs = [
                self._to_vdc(
                    self.connection.request(get_url_path(i.get('href'))).object
                )
                for i in res.object.findall(fixxpath(res.object, "Link"))
                if i.get('type') == 'application/vnd.vmware.vcloud.vdc+xml'
            ]
        return self._vdcs

    def _to_vdc(self, vdc_elm):
        return Vdc(vdc_elm.get('href'), vdc_elm.get('name'), self)

    def _get_vdc(self, vdc_name):
        vdc = None
        if not vdc_name:
            # Return the first organisation VDC found
            vdc = self.vdcs[0]
        else:
            for v in self.vdcs:
                if v.name == vdc_name:
                    vdc = v
            if vdc is None:
                raise ValueError('%s virtual data centre could not be found',
                                 vdc_name)
        return vdc

    @property
    def networks(self):
        networks = []
        for vdc in self.vdcs:
            res = self.connection.request(get_url_path(vdc.id)).object
            networks.extend(
                [network
                 for network in res.findall(
                     fixxpath(res, 'AvailableNetworks/Network')

                 )]
            )

        return networks

    def _to_image(self, image):
        image = NodeImage(id=image.get('href'),
                          name=image.get('name'),
                          driver=self.connection.driver)
        return image

    def _to_node(self, elm):
        state = self.NODE_STATE_MAP[elm.get('status')]
        name = elm.get('name')
        public_ips = []
        private_ips = []

        # Following code to find private IPs works for Terremark
        connections = elm.findall('%s/%s' % (
            '{http://schemas.dmtf.org/ovf/envelope/1}NetworkConnectionSection',
            fixxpath(elm, 'NetworkConnection'))
        )
        if not connections:
            connections = elm.findall(
                fixxpath(
                    elm,
                    'Children/Vm/NetworkConnectionSection/NetworkConnection'))

        for connection in connections:
            ips = [ip.text
                   for ip
                   in connection.findall(fixxpath(elm, "IpAddress"))]
            if connection.get('Network') == 'Internal':
                private_ips.extend(ips)
            else:
                public_ips.extend(ips)

        node = Node(id=elm.get('href'),
                    name=name,
                    state=state,
                    public_ips=public_ips,
                    private_ips=private_ips,
                    driver=self.connection.driver)

        return node

    def _get_catalog_hrefs(self):
        res = self.connection.request(self.org)
        catalogs = [
            i.get('href')
            for i in res.object.findall(fixxpath(res.object, "Link"))
            if i.get('type') == 'application/vnd.vmware.vcloud.catalog+xml'
        ]

        return catalogs

    def _wait_for_task_completion(self, task_href,
                                  timeout=DEFAULT_TASK_COMPLETION_TIMEOUT):
        start_time = time.time()
        res = self.connection.request(get_url_path(task_href))
        status = res.object.get('status')
        while status != 'success':
            if status == 'error':
                # Get error reason from the response body
                error_elem = res.object.find(fixxpath(res.object, 'Error'))
                error_msg = "Unknown error"
                if error_elem is not None:
                    error_msg = error_elem.get('message')
                raise Exception("Error status returned by task %s.: %s"
                                % (task_href, error_msg))
            if status == 'canceled':
                raise Exception("Canceled status returned by task %s."
                                % task_href)
            if (time.time() - start_time >= timeout):
                raise Exception("Timeout (%s sec) while waiting for task %s."
                                % (timeout, task_href))
            time.sleep(5)
            res = self.connection.request(get_url_path(task_href))
            status = res.object.get('status')

    def destroy_node(self, node):
        node_path = get_url_path(node.id)
        # blindly poweroff node, it will throw an exception if already off
        try:
            res = self.connection.request('%s/power/action/poweroff'
                                          % node_path,
                                          method='POST')
            self._wait_for_task_completion(res.object.get('href'))
        except Exception:
            pass

        try:
            res = self.connection.request('%s/action/undeploy' % node_path,
                                          method='POST')
            self._wait_for_task_completion(res.object.get('href'))
        except ExpatError:
            # The undeploy response is malformed XML atm.
            # We can remove this whent he providers fix the problem.
            pass
        except Exception:
            # Some vendors don't implement undeploy at all yet,
            # so catch this and move on.
            pass

        res = self.connection.request(node_path, method='DELETE')
        return res.status == httplib.ACCEPTED

    def reboot_node(self, node):
        res = self.connection.request('%s/power/action/reset'
                                      % get_url_path(node.id),
                                      method='POST')
        return res.status in [httplib.ACCEPTED, httplib.NO_CONTENT]

    def list_nodes(self):
        return self.ex_list_nodes()

    def ex_list_nodes(self, vdcs=None):
        """
        List all nodes across all vDCs. Using 'vdcs' you can specify which vDCs
        should be queried.

        :param vdcs: None, vDC or a list of vDCs to query. If None all vDCs
                     will be queried.
        :type vdcs: :class:`Vdc`

        :rtype: ``list`` of :class:`Node`
        """
        if not vdcs:
            vdcs = self.vdcs
        if not isinstance(vdcs, (list, tuple)):
            vdcs = [vdcs]
        nodes = []
        for vdc in vdcs:
            res = self.connection.request(get_url_path(vdc.id))
            elms = res.object.findall(fixxpath(
                res.object, "ResourceEntities/ResourceEntity")
            )
            vapps = [
                (i.get('name'), i.get('href'))
                for i in elms
                if i.get('type') == 'application/vnd.vmware.vcloud.vApp+xml'
                and i.get('name')
            ]

            for vapp_name, vapp_href in vapps:
                try:
                    res = self.connection.request(
                        get_url_path(vapp_href),
                        headers={'Content-Type':
                                 'application/vnd.vmware.vcloud.vApp+xml'}
                    )
                    nodes.append(self._to_node(res.object))
                except Exception:
                    # The vApp was probably removed since the previous vDC
                    # query, ignore
                    e = sys.exc_info()[1]
                    if not (e.args[0].tag.endswith('Error') and
                            e.args[0].get('minorErrorCode') ==
                            'ACCESS_TO_RESOURCE_IS_FORBIDDEN'):
                        raise

        return nodes

    def _to_size(self, ram):
        ns = NodeSize(
            id=None,
            name="%s Ram" % ram,
            ram=ram,
            disk=None,
            bandwidth=None,
            price=None,
            driver=self.connection.driver
        )
        return ns

    def list_sizes(self, location=None):
        sizes = [self._to_size(i) for i in VIRTUAL_MEMORY_VALS]
        return sizes

    def _get_catalogitems_hrefs(self, catalog):
        """Given a catalog href returns contained catalog item hrefs"""
        res = self.connection.request(
            get_url_path(catalog),
            headers={
                'Content-Type': 'application/vnd.vmware.vcloud.catalog+xml'
            }
        ).object

        cat_items = res.findall(fixxpath(res, "CatalogItems/CatalogItem"))
        cat_item_hrefs = [i.get('href')
                          for i in cat_items
                          if i.get('type') ==
                          'application/vnd.vmware.vcloud.catalogItem+xml']

        return cat_item_hrefs

    def _get_catalogitem(self, catalog_item):
        """Given a catalog item href returns elementree"""
        res = self.connection.request(
            get_url_path(catalog_item),
            headers={
                'Content-Type': 'application/vnd.vmware.vcloud.catalogItem+xml'
            }
        ).object

        return res

    def list_images(self, location=None):
        images = []
        for vdc in self.vdcs:
            res = self.connection.request(get_url_path(vdc.id)).object
            res_ents = res.findall(fixxpath(
                res, "ResourceEntities/ResourceEntity")
            )
            images += [
                self._to_image(i)
                for i in res_ents
                if i.get('type') ==
                'application/vnd.vmware.vcloud.vAppTemplate+xml'
            ]

        for catalog in self._get_catalog_hrefs():
            for cat_item in self._get_catalogitems_hrefs(catalog):
                res = self._get_catalogitem(cat_item)
                res_ents = res.findall(fixxpath(res, 'Entity'))
                images += [
                    self._to_image(i)
                    for i in res_ents
                    if i.get('type') ==
                    'application/vnd.vmware.vcloud.vAppTemplate+xml'
                ]

        def idfun(image):
            return image.id

        return self._uniquer(images, idfun)

    def _uniquer(self, seq, idfun=None):
        if idfun is None:
            def idfun(x):
                return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            if marker in seen:
                continue
            seen[marker] = 1
            result.append(item)
        return result

    def create_node(self, **kwargs):
        """
        Creates and returns node.

        :keyword    ex_network: link to a "Network" e.g.,
                    ``https://services.vcloudexpress...``
        :type       ex_network: ``str``

        :keyword    ex_vdc: Name of organisation's virtual data
                            center where vApp VMs will be deployed.
        :type       ex_vdc: ``str``

        :keyword    ex_cpus: number of virtual cpus (limit depends on provider)
        :type       ex_cpus: ``int``

        :type       ex_row: ``str``

        :type       ex_group: ``str``
        """
        name = kwargs['name']
        image = kwargs['image']
        size = kwargs['size']

        # Some providers don't require a network link
        try:
            network = kwargs.get('ex_network', self.networks[0].get('href'))
        except IndexError:
            network = ''

        password = None
        auth = self._get_and_check_auth(kwargs.get('auth'))
        password = auth.password

        instantiate_xml = InstantiateVAppXML(
            name=name,
            template=image.id,
            net_href=network,
            cpus=str(kwargs.get('ex_cpus', 1)),
            memory=str(size.ram),
            password=password,
            row=kwargs.get('ex_row', None),
            group=kwargs.get('ex_group', None)
        )

        vdc = self._get_vdc(kwargs.get('ex_vdc', None))

        # Instantiate VM and get identifier.
        content_type = \
            'application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml'
        res = self.connection.request(
            '%s/action/instantiateVAppTemplate' % get_url_path(vdc.id),
            data=instantiate_xml.tostring(),
            method='POST',
            headers={'Content-Type': content_type}
        )
        vapp_path = get_url_path(res.object.get('href'))

        # Deploy the VM from the identifier.
        res = self.connection.request('%s/action/deploy' % vapp_path,
                                      method='POST')

        self._wait_for_task_completion(res.object.get('href'))

        # Power on the VM.
        res = self.connection.request('%s/power/action/powerOn' % vapp_path,
                                      method='POST')

        res = self.connection.request(vapp_path)
        node = self._to_node(res.object)

        if getattr(auth, "generated", False):
            node.extra['password'] = auth.password

        return node


class HostingComConnection(VCloudConnection):

    """
    vCloud connection subclass for Hosting.com
    """

    host = "vcloud.safesecureweb.com"

    def _get_auth_headers(self):
        """hosting.com doesn't follow the standard vCloud authentication API"""
        return {
            'Authentication': base64.b64encode(b('%s:%s' % (self.user_id,
                                                            self.key))),
            'Content-Length': '0'
        }


class HostingComDriver(VCloudNodeDriver):

    """
    vCloud node driver for Hosting.com
    """
    connectionCls = HostingComConnection


class TerremarkConnection(VCloudConnection):

    """
    vCloud connection subclass for Terremark
    """

    host = "services.vcloudexpress.terremark.com"


class TerremarkDriver(VCloudNodeDriver):

    """
    vCloud node driver for Terremark
    """

    connectionCls = TerremarkConnection

    def list_locations(self):
        return [NodeLocation(0, "Terremark Texas", 'US', self)]


class VCloud_1_5_Connection(VCloudConnection):

    def _get_auth_headers(self):
        """Compatibility for using v1.5 API under vCloud Director 5.1"""
        return {
            'Authorization': "Basic %s" % base64.b64encode(
                b('%s:%s' % (self.user_id, self.key))).decode('utf-8'),
            'Content-Length': '0',
            'Accept': 'application/*+xml;version=1.5'
        }

    def _get_auth_token(self):
        if not self.token:
            # Log In
            conn = self.conn_classes[self.secure](self.host,
                                                  self.port)
            conn.request(method='POST', url='/api/sessions',
                         headers=self._get_auth_headers())

            resp = conn.getresponse()
            headers = dict(resp.getheaders())

            # Set authorization token
            try:
                self.token = headers['x-vcloud-authorization']
            except KeyError:
                raise InvalidCredsError()

            # Get the URL of the Organization
            body = ET.XML(resp.read())
            self.org_name = body.get('org')
            org_list_url = get_url_path(
                next((link for link in body.findall(fixxpath(body, 'Link'))
                     if link.get('type') ==
                     'application/vnd.vmware.vcloud.orgList+xml')).get('href')
            )

            conn.request(method='GET', url=org_list_url,
                         headers=self.add_default_headers({}))
            body = ET.XML(conn.getresponse().read())
            self.driver.org = get_url_path(
                next((org for org in body.findall(fixxpath(body, 'Org'))
                     if org.get('name') == self.org_name)).get('href')
            )

    def add_default_headers(self, headers):
        headers['Accept'] = 'application/*+xml;version=1.5'
        headers['x-vcloud-authorization'] = self.token
        return headers


class Instantiate_1_5_VAppXML(object):

    def __init__(self, name, template, network, vm_network=None,
                 vm_fence=None):
        self.name = name
        self.template = template
        self.network = network
        self.vm_network = vm_network
        self.vm_fence = vm_fence
        self._build_xmltree()

    def tostring(self):
        return ET.tostring(self.root)

    def _build_xmltree(self):
        self.root = self._make_instantiation_root()

        if self.network is not None:
            instantionation_params = ET.SubElement(self.root,
                                                   'InstantiationParams')
            network_config_section = ET.SubElement(instantionation_params,
                                                   'NetworkConfigSection')
            ET.SubElement(
                network_config_section,
                'Info',
                {'xmlns': 'http://schemas.dmtf.org/ovf/envelope/1'}
            )
            network_config = ET.SubElement(network_config_section,
                                           'NetworkConfig')
            self._add_network_association(network_config)

        self._add_vapp_template(self.root)

    def _make_instantiation_root(self):
        return ET.Element(
            'InstantiateVAppTemplateParams',
            {'name': self.name,
             'deploy': 'false',
             'powerOn': 'false',
             'xml:lang': 'en',
             'xmlns': 'http://www.vmware.com/vcloud/v1.5',
             'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        )

    def _add_vapp_template(self, parent):
        return ET.SubElement(
            parent,
            'Source',
            {'href': self.template}
        )

    def _add_network_association(self, parent):
        if self.vm_network is None:
            # Don't set a custom vApp VM network name
            parent.set('networkName', self.network.get('name'))
        else:
            # Set a custom vApp VM network name
            parent.set('networkName', self.vm_network)
        configuration = ET.SubElement(parent, 'Configuration')
        ET.SubElement(configuration, 'ParentNetwork',
                      {'href': self.network.get('href')})

        if self.vm_fence is None:
            fencemode = self.network.find(fixxpath(self.network,
                                          'Configuration/FenceMode')).text
        else:
            fencemode = self.vm_fence
        ET.SubElement(configuration, 'FenceMode').text = fencemode


class VCloud_1_5_NodeDriver(VCloudNodeDriver):
    connectionCls = VCloud_1_5_Connection

    # Based on
    # http://pubs.vmware.com/vcloud-api-1-5/api_prog/
    # GUID-843BE3AD-5EF6-4442-B864-BCAE44A51867.html
    NODE_STATE_MAP = {'-1': NodeState.UNKNOWN,
                      '0': NodeState.PENDING,
                      '1': NodeState.PENDING,
                      '2': NodeState.PENDING,
                      '3': NodeState.PENDING,
                      '4': NodeState.RUNNING,
                      '5': NodeState.RUNNING,
                      '6': NodeState.UNKNOWN,
                      '7': NodeState.UNKNOWN,
                      '8': NodeState.STOPPED,
                      '9': NodeState.UNKNOWN,
                      '10': NodeState.UNKNOWN}

    def list_locations(self):
        return [NodeLocation(id=self.connection.host,
                name=self.connection.host, country="N/A", driver=self)]

    def ex_find_node(self, node_name, vdcs=None):
        """
        Searches for node across specified vDCs. This is more effective than
        querying all nodes to get a single instance.

        :param node_name: The name of the node to search for
        :type node_name: ``str``

        :param vdcs: None, vDC or a list of vDCs to search in. If None all vDCs
                     will be searched.
        :type vdcs: :class:`Vdc`

        :return: node instance or None if not found
        :rtype: :class:`Node` or ``None``
        """
        if not vdcs:
            vdcs = self.vdcs
        if not getattr(vdcs, '__iter__', False):
            vdcs = [vdcs]
        for vdc in vdcs:
            res = self.connection.request(get_url_path(vdc.id))
            xpath = fixxpath(res.object, "ResourceEntities/ResourceEntity")
            entity_elems = res.object.findall(xpath)
            for entity_elem in entity_elems:
                if entity_elem.get('type') == \
                        'application/vnd.vmware.vcloud.vApp+xml' and \
                        entity_elem.get('name') == node_name:
                    path = get_url_path(entity_elem.get('href'))
                    headers = {'Content-Type':
                               'application/vnd.vmware.vcloud.vApp+xml'}
                    res = self.connection.request(path,
                                                  headers=headers)
                    return self._to_node(res.object)
        return None

    def destroy_node(self, node):
        try:
            self.ex_undeploy_node(node)
        except Exception:
            # Some vendors don't implement undeploy at all yet,
            # so catch this and move on.
            pass

        res = self.connection.request(get_url_path(node.id), method='DELETE')
        return res.status == httplib.ACCEPTED

    def reboot_node(self, node):
        res = self.connection.request('%s/power/action/reset'
                                      % get_url_path(node.id),
                                      method='POST')
        if res.status in [httplib.ACCEPTED, httplib.NO_CONTENT]:
            self._wait_for_task_completion(res.object.get('href'))
            return True
        else:
            return False

    def ex_deploy_node(self, node):
        """
        Deploys existing node. Equal to vApp "start" operation.

        :param  node: The node to be deployed
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        data = {'powerOn': 'true',
                'xmlns': 'http://www.vmware.com/vcloud/v1.5'}
        deploy_xml = ET.Element('DeployVAppParams', data)
        path = get_url_path(node.id)
        headers = {
            'Content-Type':
            'application/vnd.vmware.vcloud.deployVAppParams+xml'
        }
        res = self.connection.request('%s/action/deploy' % path,
                                      data=ET.tostring(deploy_xml),
                                      method='POST',
                                      headers=headers)
        self._wait_for_task_completion(res.object.get('href'))
        res = self.connection.request(get_url_path(node.id))
        return self._to_node(res.object)

    def ex_undeploy_node(self, node):
        """
        Undeploys existing node. Equal to vApp "stop" operation.

        :param  node: The node to be deployed
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        data = {'xmlns': 'http://www.vmware.com/vcloud/v1.5'}
        undeploy_xml = ET.Element('UndeployVAppParams', data)
        undeploy_power_action_xml = ET.SubElement(undeploy_xml,
                                                  'UndeployPowerAction')
        undeploy_power_action_xml.text = 'shutdown'

        headers = {
            'Content-Type':
            'application/vnd.vmware.vcloud.undeployVAppParams+xml'
        }

        try:
            res = self.connection.request(
                '%s/action/undeploy' % get_url_path(node.id),
                data=ET.tostring(undeploy_xml),
                method='POST',
                headers=headers)

            self._wait_for_task_completion(res.object.get('href'))
        except Exception:
            undeploy_power_action_xml.text = 'powerOff'
            res = self.connection.request(
                '%s/action/undeploy' % get_url_path(node.id),
                data=ET.tostring(undeploy_xml),
                method='POST',
                headers=headers)
            self._wait_for_task_completion(res.object.get('href'))

        res = self.connection.request(get_url_path(node.id))
        return self._to_node(res.object)

    def ex_power_off_node(self, node):
        """
        Powers on all VMs under specified node. VMs need to be This operation
        is allowed only when the vApp/VM is powered on.

        :param  node: The node to be powered off
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        return self._perform_power_operation(node, 'powerOff')

    def ex_power_on_node(self, node):
        """
        Powers on all VMs under specified node. This operation is allowed
        only when the vApp/VM is powered off or suspended.

        :param  node: The node to be powered on
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        return self._perform_power_operation(node, 'powerOn')

    def ex_shutdown_node(self, node):
        """
        Shutdowns all VMs under specified node. This operation is allowed only
        when the vApp/VM is powered on.

        :param  node: The node to be shut down
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        return self._perform_power_operation(node, 'shutdown')

    def ex_suspend_node(self, node):
        """
        Suspends all VMs under specified node. This operation is allowed only
        when the vApp/VM is powered on.

        :param  node: The node to be suspended
        :type   node: :class:`Node`

        :rtype: :class:`Node`
        """
        return self._perform_power_operation(node, 'suspend')

    def _perform_power_operation(self, node, operation):
        res = self.connection.request(
            '%s/power/action/%s' % (get_url_path(node.id), operation),
            method='POST')
        self._wait_for_task_completion(res.object.get('href'))
        res = self.connection.request(get_url_path(node.id))
        return self._to_node(res.object)

    def ex_get_control_access(self, node):
        """
        Returns the control access settings for specified node.

        :param  node: node to get the control access for
        :type   node: :class:`Node`

        :rtype: :class:`ControlAccess`
        """
        res = self.connection.request(
            '%s/controlAccess' % get_url_path(node.id))
        everyone_access_level = None
        is_shared_elem = res.object.find(
            fixxpath(res.object, "IsSharedToEveryone"))
        if is_shared_elem is not None and is_shared_elem.text == 'true':
            everyone_access_level = res.object.find(
                fixxpath(res.object, "EveryoneAccessLevel")).text

        # Parse all subjects
        subjects = []
        xpath = fixxpath(res.object, "AccessSettings/AccessSetting")
        for elem in res.object.findall(xpath):
            access_level = elem.find(fixxpath(res.object, "AccessLevel")).text
            subject_elem = elem.find(fixxpath(res.object, "Subject"))
            if subject_elem.get('type') == \
               'application/vnd.vmware.admin.group+xml':
                subj_type = 'group'
            else:
                subj_type = 'user'

            path = get_url_path(subject_elem.get('href'))
            res = self.connection.request(path)
            name = res.object.get('name')
            subject = Subject(type=subj_type,
                              name=name,
                              access_level=access_level,
                              id=subject_elem.get('href'))
            subjects.append(subject)

        return ControlAccess(node, everyone_access_level, subjects)

    def ex_set_control_access(self, node, control_access):
        """
        Sets control access for the specified node.

        :param  node: node
        :type   node: :class:`Node`

        :param  control_access: control access settings
        :type   control_access: :class:`ControlAccess`

        :rtype: ``None``
        """
        xml = ET.Element('ControlAccessParams',
                         {'xmlns': 'http://www.vmware.com/vcloud/v1.5'})
        shared_to_everyone = ET.SubElement(xml, 'IsSharedToEveryone')
        if control_access.everyone_access_level:
            shared_to_everyone.text = 'true'
            everyone_access_level = ET.SubElement(xml, 'EveryoneAccessLevel')
            everyone_access_level.text = control_access.everyone_access_level
        else:
            shared_to_everyone.text = 'false'

        # Set subjects
        if control_access.subjects:
            access_settings_elem = ET.SubElement(xml, 'AccessSettings')
        for subject in control_access.subjects:
            setting = ET.SubElement(access_settings_elem, 'AccessSetting')
            if subject.id:
                href = subject.id
            else:
                res = self.ex_query(type=subject.type, filter='name==' +
                                    subject.name)
                if not res:
                    raise LibcloudError('Specified subject "%s %s" not found '
                                        % (subject.type, subject.name))
                href = res[0]['href']
            ET.SubElement(setting, 'Subject', {'href': href})
            ET.SubElement(setting, 'AccessLevel').text = subject.access_level

        headers = {
            'Content-Type': 'application/vnd.vmware.vcloud.controlAccess+xml'
        }
        self.connection.request(
            '%s/action/controlAccess' % get_url_path(node.id),
            data=ET.tostring(xml),
            headers=headers,
            method='POST')

    def ex_get_metadata(self, node):
        """
        :param  node: node
        :type   node: :class:`Node`

        :return: dictionary mapping metadata keys to metadata values
        :rtype: dictionary mapping ``str`` to ``str``
        """
        res = self.connection.request('%s/metadata' % (get_url_path(node.id)))
        xpath = fixxpath(res.object, 'MetadataEntry')
        metadata_entries = res.object.findall(xpath)
        res_dict = {}

        for entry in metadata_entries:
            key = entry.findtext(fixxpath(res.object, 'Key'))
            value = entry.findtext(fixxpath(res.object, 'Value'))
            res_dict[key] = value

        return res_dict

    def ex_set_metadata_entry(self, node, key, value):
        """
        :param  node: node
        :type   node: :class:`Node`

        :param key: metadata key to be set
        :type key: ``str``

        :param value: metadata value to be set
        :type value: ``str``

        :rtype: ``None``
        """
        metadata_elem = ET.Element(
            'Metadata',
            {'xmlns': "http://www.vmware.com/vcloud/v1.5",
             'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"}
        )
        entry = ET.SubElement(metadata_elem, 'MetadataEntry')
        key_elem = ET.SubElement(entry, 'Key')
        key_elem.text = key
        value_elem = ET.SubElement(entry, 'Value')
        value_elem.text = value

        # send it back to the server
        res = self.connection.request(
            '%s/metadata' % get_url_path(node.id),
            data=ET.tostring(metadata_elem),
            headers={
                'Content-Type': 'application/vnd.vmware.vcloud.metadata+xml'
            },
            method='POST')
        self._wait_for_task_completion(res.object.get('href'))

    def ex_query(self, type, filter=None, page=1, page_size=100, sort_asc=None,
                 sort_desc=None):
        """
        Queries vCloud for specified type. See
        http://www.vmware.com/pdf/vcd_15_api_guide.pdf for details. Each
        element of the returned list is a dictionary with all attributes from
        the record.

        :param type: type to query (r.g. user, group, vApp etc.)
        :type  type: ``str``

        :param filter: filter expression (see documentation for syntax)
        :type  filter: ``str``

        :param page: page number
        :type  page: ``int``

        :param page_size: page size
        :type  page_size: ``int``

        :param sort_asc: sort in ascending order by specified field
        :type  sort_asc: ``str``

        :param sort_desc: sort in descending order by specified field
        :type  sort_desc: ``str``

        :rtype: ``list`` of dict
        """
        # This is a workaround for filter parameter encoding
        # the urllib encodes (name==Developers%20Only) into
        # %28name%3D%3DDevelopers%20Only%29) which is not accepted by vCloud
        params = {
            'type': type,
            'pageSize': page_size,
            'page': page,
        }
        if sort_asc:
            params['sortAsc'] = sort_asc
        if sort_desc:
            params['sortDesc'] = sort_desc

        url = '/api/query?' + urlencode(params)
        if filter:
            if not filter.startswith('('):
                filter = '(' + filter + ')'
            url += '&filter=' + filter.replace(' ', '+')

        results = []
        res = self.connection.request(url)
        for elem in res.object:
            if not elem.tag.endswith('Link'):
                result = elem.attrib
                result['type'] = elem.tag.split('}')[1]
                results.append(result)
        return results

    def create_node(self, **kwargs):
        """
        Creates and returns node. If the source image is:
          - vApp template - a new vApp is instantiated from template
          - existing vApp - a new vApp is cloned from the source vApp. Can
                            not clone more vApps is parallel otherwise
                            resource busy error is raised.


        @inherits: :class:`NodeDriver.create_node`

        :keyword    image:  OS Image to boot on node. (required). Can be a
                            NodeImage or existing Node that will be cloned.
        :type       image:  :class:`NodeImage` or :class:`Node`

        :keyword    ex_network: Organisation's network name for attaching vApp
                                VMs to.
        :type       ex_network: ``str``

        :keyword    ex_vdc: Name of organisation's virtual data center where
                            vApp VMs will be deployed.
        :type       ex_vdc: ``str``

        :keyword    ex_vm_names: list of names to be used as a VM and computer
                                 name. The name must be max. 15 characters
                                 long and follow the host name requirements.
        :type       ex_vm_names: ``list`` of ``str``

        :keyword    ex_vm_cpu: number of virtual CPUs/cores to allocate for
                               each vApp VM.
        :type       ex_vm_cpu: ``int``

        :keyword    ex_vm_memory: amount of memory in MB to allocate for each
                                  vApp VM.
        :type       ex_vm_memory: ``int``

        :keyword    ex_vm_script: full path to file containing guest
                                  customisation script for each vApp VM.
                                  Useful for creating users & pushing out
                                  public SSH keys etc.
        :type       ex_vm_script: ``str``

        :keyword    ex_vm_network: Override default vApp VM network name.
                                   Useful for when you've imported an OVF
                                   originating from outside of the vCloud.
        :type       ex_vm_network: ``str``

        :keyword    ex_vm_fence: Fence mode for connecting the vApp VM network
                                 (ex_vm_network) to the parent
                                 organisation network (ex_network).
        :type       ex_vm_fence: ``str``

        :keyword    ex_vm_ipmode: IP address allocation mode for all vApp VM
                                  network connections.
        :type       ex_vm_ipmode: ``str``

        :keyword    ex_deploy: set to False if the node shouldn't be deployed
                               (started) after creation
        :type       ex_deploy: ``bool``

        :keyword    ex_clone_timeout: timeout in seconds for clone/instantiate
                                      VM operation.
                                      Cloning might be a time consuming
                                      operation especially when linked clones
                                      are disabled or VMs are created on
                                      different datastores.
                                      Overrides the default task completion
                                      value.
        :type       ex_clone_timeout: ``int``
        """
        name = kwargs['name']
        image = kwargs['image']
        ex_vm_names = kwargs.get('ex_vm_names')
        ex_vm_cpu = kwargs.get('ex_vm_cpu')
        ex_vm_memory = kwargs.get('ex_vm_memory')
        ex_vm_script = kwargs.get('ex_vm_script')
        ex_vm_fence = kwargs.get('ex_vm_fence', None)
        ex_network = kwargs.get('ex_network', None)
        ex_vm_network = kwargs.get('ex_vm_network', None)
        ex_vm_ipmode = kwargs.get('ex_vm_ipmode', None)
        ex_deploy = kwargs.get('ex_deploy', True)
        ex_vdc = kwargs.get('ex_vdc', None)
        ex_clone_timeout = kwargs.get('ex_clone_timeout',
                                      DEFAULT_TASK_COMPLETION_TIMEOUT)

        self._validate_vm_names(ex_vm_names)
        self._validate_vm_cpu(ex_vm_cpu)
        self._validate_vm_memory(ex_vm_memory)
        self._validate_vm_fence(ex_vm_fence)
        self._validate_vm_ipmode(ex_vm_ipmode)
        ex_vm_script = self._validate_vm_script(ex_vm_script)

        # Some providers don't require a network link
        if ex_network:
            network_href = self._get_network_href(ex_network)
            network_elem = self.connection.request(
                get_url_path(network_href)).object
        else:
            network_elem = None

        vdc = self._get_vdc(ex_vdc)

        if self._is_node(image):
            vapp_name, vapp_href = self._clone_node(name,
                                                    image,
                                                    vdc,
                                                    ex_clone_timeout)
        else:
            vapp_name, vapp_href = self._instantiate_node(name, image,
                                                          network_elem,
                                                          vdc, ex_vm_network,
                                                          ex_vm_fence,
                                                          ex_clone_timeout)

        self._change_vm_names(vapp_href, ex_vm_names)
        self._change_vm_cpu(vapp_href, ex_vm_cpu)
        self._change_vm_memory(vapp_href, ex_vm_memory)
        self._change_vm_script(vapp_href, ex_vm_script)
        self._change_vm_ipmode(vapp_href, ex_vm_ipmode)

        # Power on the VM.
        if ex_deploy:
            # Retry 3 times: when instantiating large number of VMs at the same
            # time some may fail on resource allocation
            retry = 3
            while True:
                try:
                    res = self.connection.request(
                        '%s/power/action/powerOn' % get_url_path(vapp_href),
                        method='POST')
                    self._wait_for_task_completion(res.object.get('href'))
                    break
                except Exception:
                    if retry <= 0:
                        raise
                    retry -= 1
                    time.sleep(10)

        res = self.connection.request(get_url_path(vapp_href))
        node = self._to_node(res.object)
        return node

    def _instantiate_node(self, name, image, network_elem, vdc, vm_network,
                          vm_fence, instantiate_timeout):
        instantiate_xml = Instantiate_1_5_VAppXML(
            name=name,
            template=image.id,
            network=network_elem,
            vm_network=vm_network,
            vm_fence=vm_fence
        )

        # Instantiate VM and get identifier.
        headers = {
            'Content-Type':
            'application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml'
        }
        res = self.connection.request(
            '%s/action/instantiateVAppTemplate' % get_url_path(vdc.id),
            data=instantiate_xml.tostring(),
            method='POST',
            headers=headers
        )
        vapp_name = res.object.get('name')
        vapp_href = res.object.get('href')

        task_href = res.object.find(fixxpath(res.object, "Tasks/Task")).get(
            'href')
        self._wait_for_task_completion(task_href, instantiate_timeout)
        return vapp_name, vapp_href

    def _clone_node(self, name, sourceNode, vdc, clone_timeout):
        clone_xml = ET.Element(
            "CloneVAppParams",
            {'name': name, 'deploy': 'false', 'powerOn': 'false',
             'xmlns': "http://www.vmware.com/vcloud/v1.5",
             'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"}
        )
        ET.SubElement(clone_xml,
                      'Description').text = 'Clone of ' + sourceNode.name
        ET.SubElement(clone_xml, 'Source', {'href': sourceNode.id})

        headers = {
            'Content-Type': 'application/vnd.vmware.vcloud.cloneVAppParams+xml'
        }
        res = self.connection.request(
            '%s/action/cloneVApp' % get_url_path(vdc.id),
            data=ET.tostring(clone_xml),
            method='POST',
            headers=headers
        )
        vapp_name = res.object.get('name')
        vapp_href = res.object.get('href')

        task_href = res.object.find(
            fixxpath(res.object, "Tasks/Task")).get('href')
        self._wait_for_task_completion(task_href, clone_timeout)

        res = self.connection.request(get_url_path(vapp_href))

        vms = res.object.findall(fixxpath(res.object, "Children/Vm"))

        # Fix the networking for VMs
        for i, vm in enumerate(vms):
            # Remove network
            network_xml = ET.Element("NetworkConnectionSection", {
                'ovf:required': 'false',
                'xmlns': "http://www.vmware.com/vcloud/v1.5",
                'xmlns:ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
            ET.SubElement(network_xml, "ovf:Info").text = \
                'Specifies the available VM network connections'

            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.networkConnectionSection+xml'
            }
            res = self.connection.request(
                '%s/networkConnectionSection' % get_url_path(vm.get('href')),
                data=ET.tostring(network_xml),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

            # Re-add network
            network_xml = vm.find(fixxpath(vm, 'NetworkConnectionSection'))
            network_conn_xml = network_xml.find(
                fixxpath(network_xml, 'NetworkConnection'))
            network_conn_xml.set('needsCustomization', 'true')
            network_conn_xml.remove(
                network_conn_xml.find(fixxpath(network_xml, 'IpAddress')))
            network_conn_xml.remove(
                network_conn_xml.find(fixxpath(network_xml, 'MACAddress')))

            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.networkConnectionSection+xml'
            }
            res = self.connection.request(
                '%s/networkConnectionSection' % get_url_path(vm.get('href')),
                data=ET.tostring(network_xml),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

        return vapp_name, vapp_href

    def ex_set_vm_cpu(self, vapp_or_vm_id, vm_cpu):
        """
        Sets the number of virtual CPUs for the specified VM or VMs under
        the vApp. If the vapp_or_vm_id param represents a link to an vApp
        all VMs that are attached to this vApp will be modified.

        Please ensure that hot-adding a virtual CPU is enabled for the
        powered on virtual machines. Otherwise use this method on undeployed
        vApp.

        :keyword    vapp_or_vm_id: vApp or VM ID that will be modified. If
                                   a vApp ID is used here all attached VMs
                                   will be modified
        :type       vapp_or_vm_id: ``str``

        :keyword    vm_cpu: number of virtual CPUs/cores to allocate for
                            specified VMs
        :type       vm_cpu: ``int``

        :rtype: ``None``
        """
        self._validate_vm_cpu(vm_cpu)
        self._change_vm_cpu(vapp_or_vm_id, vm_cpu)

    def ex_set_vm_memory(self, vapp_or_vm_id, vm_memory):
        """
        Sets the virtual memory in MB to allocate for the specified VM or
        VMs under the vApp. If the vapp_or_vm_id param represents a link
        to an vApp all VMs that are attached to this vApp will be modified.

        Please ensure that hot-change of virtual memory is enabled for the
        powered on virtual machines. Otherwise use this method on undeployed
        vApp.

        :keyword    vapp_or_vm_id: vApp or VM ID that will be modified. If
                                   a vApp ID is used here all attached VMs
                                   will be modified
        :type       vapp_or_vm_id: ``str``

        :keyword    vm_memory: virtual memory in MB to allocate for the
                               specified VM or VMs
        :type       vm_memory: ``int``

        :rtype: ``None``
        """
        self._validate_vm_memory(vm_memory)
        self._change_vm_memory(vapp_or_vm_id, vm_memory)

    def ex_add_vm_disk(self, vapp_or_vm_id, vm_disk_size):
        """
        Adds a virtual disk to the specified VM or VMs under the vApp. If the
        vapp_or_vm_id param represents a link to an vApp all VMs that are
        attached to this vApp will be modified.

        :keyword    vapp_or_vm_id: vApp or VM ID that will be modified. If a
                                   vApp ID is used here all attached VMs
                                   will be modified
        :type       vapp_or_vm_id: ``str``

        :keyword    vm_disk_size: the disk capacity in GB that will be added
                                  to the specified VM or VMs
        :type       vm_disk_size: ``int``

        :rtype: ``None``
        """
        self._validate_vm_disk_size(vm_disk_size)
        self._add_vm_disk(vapp_or_vm_id, vm_disk_size)

    @staticmethod
    def _validate_vm_names(names):
        if names is None:
            return
        hname_re = re.compile(
            '^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9]*)[\-])*([A-Za-z]|[A-Za-z][A-Za-z0-9]*[A-Za-z0-9])$')  # NOQA
        for name in names:
            if len(name) > 15:
                raise ValueError(
                    'The VM name "' + name + '" is too long for the computer '
                    'name (max 15 chars allowed).')
            if not hname_re.match(name):
                raise ValueError('The VM name "' + name + '" can not be '
                                 'used. "' + name + '" is not a valid '
                                 'computer name for the VM.')

    @staticmethod
    def _validate_vm_memory(vm_memory):
        if vm_memory is None:
            return
        elif vm_memory not in VIRTUAL_MEMORY_VALS:
            raise ValueError(
                '%s is not a valid vApp VM memory value' % vm_memory)

    @staticmethod
    def _validate_vm_cpu(vm_cpu):
        if vm_cpu is None:
            return
        elif vm_cpu not in VIRTUAL_CPU_VALS_1_5:
            raise ValueError('%s is not a valid vApp VM CPU value' % vm_cpu)

    @staticmethod
    def _validate_vm_disk_size(vm_disk):
        if vm_disk is None:
            return
        elif int(vm_disk) < 0:
            raise ValueError('%s is not a valid vApp VM disk space value',
                             vm_disk)

    @staticmethod
    def _validate_vm_script(vm_script):
        if vm_script is None:
            return
        # Try to locate the script file
        if not os.path.isabs(vm_script):
            vm_script = os.path.expanduser(vm_script)
            vm_script = os.path.abspath(vm_script)
        if not os.path.isfile(vm_script):
            raise LibcloudError(
                "%s the VM script file does not exist" % vm_script)
        try:
            open(vm_script).read()
        except:
            raise
        return vm_script

    @staticmethod
    def _validate_vm_fence(vm_fence):
        if vm_fence is None:
            return
        elif vm_fence not in FENCE_MODE_VALS_1_5:
            raise ValueError('%s is not a valid fencing mode value' % vm_fence)

    @staticmethod
    def _validate_vm_ipmode(vm_ipmode):
        if vm_ipmode is None:
            return
        elif vm_ipmode == 'MANUAL':
            raise NotImplementedError(
                'MANUAL IP mode: The interface for supplying '
                'IPAddress does not exist yet')
        elif vm_ipmode not in IP_MODE_VALS_1_5:
            raise ValueError(
                '%s is not a valid IP address allocation mode value'
                % vm_ipmode)

    def _change_vm_names(self, vapp_or_vm_id, vm_names):
        if vm_names is None:
            return

        vms = self._get_vm_elements(vapp_or_vm_id)
        for i, vm in enumerate(vms):
            if len(vm_names) <= i:
                return

            # Get GuestCustomizationSection
            res = self.connection.request(
                '%s/guestCustomizationSection' % get_url_path(vm.get('href')))

            # Update GuestCustomizationSection
            res.object.find(
                fixxpath(res.object, 'ComputerName')).text = vm_names[i]
            # Remove AdminPassword from customization section
            admin_pass = res.object.find(fixxpath(res.object, 'AdminPassword'))
            if admin_pass is not None:
                res.object.remove(admin_pass)

            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.guestCustomizationSection+xml'
            }
            res = self.connection.request(
                '%s/guestCustomizationSection' % get_url_path(vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

            # Update Vm name
            req_xml = ET.Element("Vm", {
                'name': vm_names[i],
                'xmlns': "http://www.vmware.com/vcloud/v1.5"})
            res = self.connection.request(
                get_url_path(vm.get('href')),
                data=ET.tostring(req_xml),
                method='PUT',
                headers={
                    'Content-Type': 'application/vnd.vmware.vcloud.vm+xml'}
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _change_vm_cpu(self, vapp_or_vm_id, vm_cpu):
        if vm_cpu is None:
            return

        vms = self._get_vm_elements(vapp_or_vm_id)
        for vm in vms:
            # Get virtualHardwareSection/cpu section
            res = self.connection.request(
                '%s/virtualHardwareSection/cpu' % get_url_path(vm.get('href')))

            # Update VirtualQuantity field
            xpath = ('{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                     'CIM_ResourceAllocationSettingData}VirtualQuantity')
            res.object.find(xpath).text = str(vm_cpu)

            headers = {
                'Content-Type': 'application/vnd.vmware.vcloud.rasdItem+xml'
            }
            res = self.connection.request(
                '%s/virtualHardwareSection/cpu' % get_url_path(vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _change_vm_memory(self, vapp_or_vm_id, vm_memory):
        if vm_memory is None:
            return

        vms = self._get_vm_elements(vapp_or_vm_id)
        for vm in vms:
            # Get virtualHardwareSection/memory section
            res = self.connection.request(
                '%s/virtualHardwareSection/memory' %
                get_url_path(vm.get('href')))

            # Update VirtualQuantity field
            xpath = ('{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                     'CIM_ResourceAllocationSettingData}VirtualQuantity')
            res.object.find(xpath).text = str(vm_memory)

            headers = {
                'Content-Type': 'application/vnd.vmware.vcloud.rasdItem+xml'
            }
            res = self.connection.request(
                '%s/virtualHardwareSection/memory' % get_url_path(
                    vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _add_vm_disk(self, vapp_or_vm_id, vm_disk):
        if vm_disk is None:
            return

        rasd_ns = ('{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'
                   'CIM_ResourceAllocationSettingData}')

        vms = self._get_vm_elements(vapp_or_vm_id)
        for vm in vms:
            # Get virtualHardwareSection/disks section
            res = self.connection.request(
                '%s/virtualHardwareSection/disks' %
                get_url_path(vm.get('href')))

            existing_ids = []
            new_disk = None
            for item in res.object.findall(fixxpath(res.object, 'Item')):
                # Clean Items from unnecessary stuff
                for elem in item:
                    if elem.tag == '%sInstanceID' % rasd_ns:
                        existing_ids.append(int(elem.text))
                    if elem.tag in ['%sAddressOnParent' % rasd_ns,
                                    '%sParent' % rasd_ns]:
                        item.remove(elem)
                if item.find('%sHostResource' % rasd_ns) is not None:
                    new_disk = item

            new_disk = copy.deepcopy(new_disk)
            disk_id = max(existing_ids) + 1
            new_disk.find('%sInstanceID' % rasd_ns).text = str(disk_id)
            new_disk.find('%sElementName' %
                          rasd_ns).text = 'Hard Disk ' + str(disk_id)
            new_disk.find('%sHostResource' % rasd_ns).set(
                fixxpath(new_disk, 'capacity'), str(int(vm_disk) * 1024))
            res.object.append(new_disk)

            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.rasditemslist+xml'
            }
            res = self.connection.request(
                '%s/virtualHardwareSection/disks' % get_url_path(
                    vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _change_vm_script(self, vapp_or_vm_id, vm_script):
        if vm_script is None:
            return

        vms = self._get_vm_elements(vapp_or_vm_id)
        try:
            script = open(vm_script).read()
        except:
            return

        # ElementTree escapes script characters automatically. Escape
        # requirements:
        # http://www.vmware.com/support/vcd/doc/rest-api-doc-1.5-html/types/
        # GuestCustomizationSectionType.html
        for vm in vms:
            # Get GuestCustomizationSection
            res = self.connection.request(
                '%s/guestCustomizationSection' % get_url_path(vm.get('href')))

            # Attempt to update any existing CustomizationScript element
            try:
                res.object.find(
                    fixxpath(res.object, 'CustomizationScript')).text = script
            except:
                # CustomizationScript section does not exist, insert it just
                # before ComputerName
                for i, e in enumerate(res.object):
                    if e.tag == \
                            '{http://www.vmware.com/vcloud/v1.5}ComputerName':
                        break
                e = ET.Element(
                    '{http://www.vmware.com/vcloud/v1.5}CustomizationScript')
                e.text = script
                res.object.insert(i, e)

            # Remove AdminPassword from customization section due to an API
            # quirk
            admin_pass = res.object.find(fixxpath(res.object, 'AdminPassword'))
            if admin_pass is not None:
                res.object.remove(admin_pass)

            # Update VM's GuestCustomizationSection
            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.guestCustomizationSection+xml'
            }
            res = self.connection.request(
                '%s/guestCustomizationSection' % get_url_path(vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _change_vm_ipmode(self, vapp_or_vm_id, vm_ipmode):
        if vm_ipmode is None:
            return

        vms = self._get_vm_elements(vapp_or_vm_id)

        for vm in vms:
            res = self.connection.request(
                '%s/networkConnectionSection' % get_url_path(vm.get('href')))
            net_conns = res.object.findall(
                fixxpath(res.object, 'NetworkConnection'))
            for c in net_conns:
                c.find(fixxpath(c, 'IpAddressAllocationMode')).text = vm_ipmode

            headers = {
                'Content-Type':
                'application/vnd.vmware.vcloud.networkConnectionSection+xml'
            }

            res = self.connection.request(
                '%s/networkConnectionSection' % get_url_path(vm.get('href')),
                data=ET.tostring(res.object),
                method='PUT',
                headers=headers
            )
            self._wait_for_task_completion(res.object.get('href'))

    def _get_network_href(self, network_name):
        network_href = None

        # Find the organisation's network href
        res = self.connection.request(self.org)
        links = res.object.findall(fixxpath(res.object, 'Link'))
        for l in links:
            if l.attrib['type'] == \
                    'application/vnd.vmware.vcloud.orgNetwork+xml' \
                    and l.attrib['name'] == network_name:
                network_href = l.attrib['href']

        if network_href is None:
            raise ValueError(
                '%s is not a valid organisation network name' % network_name)
        else:
            return network_href

    def _get_vm_elements(self, vapp_or_vm_id):
        res = self.connection.request(get_url_path(vapp_or_vm_id))
        if res.object.tag.endswith('VApp'):
            vms = res.object.findall(fixxpath(res.object, 'Children/Vm'))
        elif res.object.tag.endswith('Vm'):
            vms = [res.object]
        else:
            raise ValueError(
                'Specified ID value is not a valid VApp or Vm identifier.')
        return vms

    def _is_node(self, node_or_image):
        return isinstance(node_or_image, Node)

    def _to_node(self, node_elm):
        # Parse VMs as extra field
        vms = []
        for vm_elem in node_elm.findall(fixxpath(node_elm, 'Children/Vm')):
            public_ips = []
            private_ips = []

            xpath = fixxpath(vm_elem,
                             'NetworkConnectionSection/NetworkConnection')
            for connection in vm_elem.findall(xpath):
                ip = connection.find(fixxpath(connection, "IpAddress"))
                if ip is not None:
                    private_ips.append(ip.text)
                external_ip = connection.find(
                    fixxpath(connection, "ExternalIpAddress"))
                if external_ip is not None:
                    public_ips.append(external_ip.text)
                elif ip is not None:
                    public_ips.append(ip.text)

            xpath = ('{http://schemas.dmtf.org/ovf/envelope/1}'
                     'OperatingSystemSection')
            os_type_elem = vm_elem.find(xpath)
            if os_type_elem is not None:
                os_type = os_type_elem.get(
                    '{http://www.vmware.com/schema/ovf}osType')
            else:
                os_type = None
            vm = {
                'id': vm_elem.get('href'),
                'name': vm_elem.get('name'),
                'state': self.NODE_STATE_MAP[vm_elem.get('status')],
                'public_ips': public_ips,
                'private_ips': private_ips,
                'os_type': os_type
            }
            vms.append(vm)

        # Take the node IP addresses from all VMs
        public_ips = []
        private_ips = []
        for vm in vms:
            public_ips.extend(vm['public_ips'])
            private_ips.extend(vm['private_ips'])

        # Find vDC
        vdc_id = next(link.get('href') for link
                      in node_elm.findall(fixxpath(node_elm, 'Link'))
                      if link.get('type') ==
                      'application/vnd.vmware.vcloud.vdc+xml')
        vdc = next(vdc for vdc in self.vdcs if vdc.id == vdc_id)

        node = Node(id=node_elm.get('href'),
                    name=node_elm.get('name'),
                    state=self.NODE_STATE_MAP[node_elm.get('status')],
                    public_ips=public_ips,
                    private_ips=private_ips,
                    driver=self.connection.driver,
                    extra={'vdc': vdc.name, 'vms': vms})
        return node

    def _to_vdc(self, vdc_elm):

        def get_capacity_values(capacity_elm):
            if capacity_elm is None:
                return None
            limit = int(capacity_elm.findtext(fixxpath(capacity_elm, 'Limit')))
            used = int(capacity_elm.findtext(fixxpath(capacity_elm, 'Used')))
            units = capacity_elm.findtext(fixxpath(capacity_elm, 'Units'))
            return Capacity(limit, used, units)

        cpu = get_capacity_values(
            vdc_elm.find(fixxpath(vdc_elm, 'ComputeCapacity/Cpu')))
        memory = get_capacity_values(
            vdc_elm.find(fixxpath(vdc_elm, 'ComputeCapacity/Memory')))
        storage = get_capacity_values(
            vdc_elm.find(fixxpath(vdc_elm, 'StorageCapacity')))

        return Vdc(id=vdc_elm.get('href'),
                   name=vdc_elm.get('name'),
                   driver=self,
                   allocation_model=vdc_elm.findtext(
                       fixxpath(vdc_elm, 'AllocationModel')),
                   cpu=cpu,
                   memory=memory,
                   storage=storage)


class VCloud_5_1_NodeDriver(VCloud_1_5_NodeDriver):

    @staticmethod
    def _validate_vm_memory(vm_memory):
        if vm_memory is None:
            return None
        elif (vm_memory % 4) != 0:
            # The vcd 5.1 virtual machine memory size must be a multiple of 4
            # MB
            raise ValueError(
                '%s is not a valid vApp VM memory value' % (vm_memory))
