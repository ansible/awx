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
Abiquo Compute Driver

The driver implements the compute Abiquo functionality for the Abiquo API.
This version is compatible with the following versions of Abiquo:

    * Abiquo 2.0 (http://wiki.abiquo.com/display/ABI20/The+Abiquo+API)
    * Abiquo 2.2 (http://wiki.abiquo.com/display/ABI22/The+Abiquo+API)
"""
import xml.etree.ElementTree as ET

from libcloud.compute.base import NodeDriver, NodeSize
from libcloud.compute.types import Provider, LibcloudError
from libcloud.common.abiquo import (AbiquoConnection, get_href,
                                    AbiquoResponse)
from libcloud.compute.base import NodeLocation, NodeImage, Node
from libcloud.utils.py3 import tostring


class AbiquoNodeDriver(NodeDriver):
    """
    Implements the :class:`NodeDriver`'s for the Abiquo Compute Provider
    """

    type = Provider.ABIQUO
    name = 'Abiquo'
    website = 'http://www.abiquo.com/'
    connectionCls = AbiquoConnection
    timeout = 2000  # some images take a lot of time!

    # Media Types
    NODES_MIME_TYPE = 'application/vnd.abiquo.virtualmachineswithnode+xml'
    NODE_MIME_TYPE = 'application/vnd.abiquo.virtualmachinewithnode+xml'
    VAPP_MIME_TYPE = 'application/vnd.abiquo.virtualappliance+xml'
    VM_TASK_MIME_TYPE = 'application/vnd.abiquo.virtualmachinetask+xml'

    # Others constants
    GIGABYTE = 1073741824

    def __init__(self, user_id, secret, endpoint, **kwargs):
        """
        Initializes Abiquo Driver

        Initializes the :class:`NodeDriver` object and populate the cache.

        :param       user_id: identifier of Abiquo user (required)
        :type        user_id: ``str``
        :param       secret: password of the Abiquo user (required)
        :type        secret: ``str``
        :param       endpoint: Abiquo API endpoint (required)
        :type        endpoint: ``str`` that can be parsed as URL
        """
        self.endpoint = endpoint
        super(AbiquoNodeDriver, self).__init__(key=user_id, secret=secret,
                                               secure=False, host=None,
                                               port=None, **kwargs)
        self.ex_populate_cache()

    def create_node(self, **kwargs):
        """
        Create a new node instance in Abiquo

        All the :class:`Node`s need to be defined inside a VirtualAppliance
        (called :class:`NodeGroup` here). If there is no group name defined,
        'libcloud' name will be used instead.

        This method wraps these Abiquo actions:

            1. Create a group if it does not exist.
            2. Register a new node in the group.
            3. Deploy the node and boot it.
            4. Retrieves it again to get schedule-time attributes (such as ips
               and vnc ports).

        The rest of the driver methods has been created in a way that, if any
        of these actions fail, the user can not reach an inconsistent state

        :keyword    name:   The name for this new node (required)
        :type       name:   ``str``

        :keyword    size:   The size of resources allocated to this node.
        :type       size:   :class:`NodeSize`

        :keyword    image:  OS Image to boot on node. (required)
        :type       image:  :class:`NodeImage`

        :keyword    location: Which data center to create a node in. If empty,
                              undefined behavior will be selected. (optional)
        :type       location: :class:`NodeLocation`

        :keyword   group_name:  Which group this node belongs to. If empty,
                                 it will be created into 'libcloud' group. If
                                 it does not found any group in the target
                                 location (random location if you have not set
                                 the parameter), then it will create a new
                                 group with this name.
        :type     group_name:  c{str}

        :return:               The newly created node.
        :rtype:                :class:`Node`
        """
        # Define the location
        # To be clear:
        #     'xml_loc' is the xml element we navigate into (we need links)
        #     'loc' is the :class:`NodeLocation` entity
        xml_loc, loc = self._define_create_node_location(**kwargs)

        # Define the Group
        group = self._define_create_node_group(xml_loc, loc, **kwargs)

        # Register the Node
        vm = self._define_create_node_node(group, **kwargs)

        # Execute the 'create' in hypervisor action
        self._deploy_remote(vm)

        # Retrieve it again, to get some schedule-time defined values
        edit_vm = get_href(vm, 'edit')
        headers = {'Accept': self.NODE_MIME_TYPE}
        vm = self.connection.request(edit_vm, headers=headers).object
        return self._to_node(vm, self)

    def destroy_node(self, node):
        """
        Destroy a node

        Depending on the provider, this may destroy all data associated with
        the node, including backups.

        :param node: The node to be destroyed
        :type node: :class:`Node`

        :return: True if the destroy was successful, otherwise False
        :rtype: ``bool``
        """

        # Refresh node state
        e_vm = self.connection.request(node.extra['uri_id']).object
        state = e_vm.findtext('state')

        if state in ['ALLOCATED', 'CONFIGURED', 'LOCKED', 'UNKNOWN']:
            raise LibcloudError('Invalid Node state', self)

        if state != 'NOT_ALLOCATED':
            # prepare the element that forces the undeploy
            vm_task = ET.Element('virtualmachinetask')
            force_undeploy = ET.SubElement(vm_task, 'forceUndeploy')
            force_undeploy.text = 'True'
            # Set the URI
            destroy_uri = node.extra['uri_id'] + '/action/undeploy'
            # Prepare the headers
            headers = {'Content-type': self.VM_TASK_MIME_TYPE}
            res = self.connection.async_request(action=destroy_uri,
                                                method='POST',
                                                data=tostring(vm_task),
                                                headers=headers)

        if state == 'NOT_ALLOCATED' or res.async_success():
            self.connection.request(action=node.extra['uri_id'],
                                    method='DELETE')
            return True
        else:
            return False

    def ex_run_node(self, node):
        """
        Runs a node

        Here there is a bit difference between Abiquo states and libcloud
        states, so this method is created to have better compatibility. In
        libcloud, if the node is not running, then it does not exist (avoiding
        UNKNOWN and temporal states). In Abiquo, you can define a node, and
        then deploy it.

        If the node is in :class:`NodeState.TERMINATED` libcloud's state and in
        'NOT_DEPLOYED' Abiquo state, there is a way to run and recover it
        for libcloud using this method. There is no way to reach this state
        if you are using only libcloud, but you may have used another Abiquo
        client and now you want to recover your node to be used by libcloud.

        :param node: The node to run
        :type node: :class:`Node`

        :return: The node itself, but with the new state
        :rtype: :class:`Node`
        """
        # Refresh node state
        e_vm = self.connection.request(node.extra['uri_id']).object
        state = e_vm.findtext('state')

        if state != 'NOT_ALLOCATED':
            raise LibcloudError('Invalid Node state', self)

        # --------------------------------------------------------
        #     Deploy the Node
        # --------------------------------------------------------
        self._deploy_remote(e_vm)

        # --------------------------------------------------------
        #     Retrieve it again, to get some schedule-defined
        #     values.
        # --------------------------------------------------------
        edit_vm = get_href(e_vm, 'edit')
        headers = {'Accept': self.NODE_MIME_TYPE}
        e_vm = self.connection.request(edit_vm, headers=headers).object
        return self._to_node(e_vm, self)

    def ex_populate_cache(self):
        """
        Populate the cache.

        For each connection, it is good to store some objects that will be
        useful for further requests, such as the 'user' and the 'enterprise'
        objects.

        Executes the 'login' resource after setting the connection parameters
        and, if the execution is successful, it sets the 'user' object into
        cache. After that, it also requests for the 'enterprise' and
        'locations' data.

        List of locations should remain the same for a single libcloud
        connection. However, this method is public and you are able to
        refresh the list of locations any time.
        """
        user = self.connection.request('/login').object
        self.connection.cache['user'] = user
        e_ent = get_href(self.connection.cache['user'],
                         'enterprise')
        ent = self.connection.request(e_ent).object
        self.connection.cache['enterprise'] = ent

        uri_vdcs = '/cloud/virtualdatacenters'
        e_vdcs = self.connection.request(uri_vdcs).object

        # Set a dict for the datacenter and its href for a further search
        params = {"idEnterprise": self._get_enterprise_id()}
        e_dcs = self.connection.request('/admin/datacenters',
                                        params=params).object
        dc_dict = {}
        for dc in e_dcs.findall('datacenter'):
            key = get_href(dc, 'edit')
            dc_dict[key] = dc

        # Populate locations cache
        self.connection.cache['locations'] = {}
        for e_vdc in e_vdcs.findall('virtualDatacenter'):
            dc_link = get_href(e_vdc, 'datacenter')
            loc = self._to_location(e_vdc, dc_dict[dc_link], self)

            # Save into cache the link to the itself because we will need
            # it in the future, but we save here to don't extend the class
            # :class:`NodeLocation`.
            # So here we have the dict: :class:`NodeLocation` ->
            # link_datacenter
            self.connection.cache['locations'][loc] = get_href(e_vdc, 'edit')

    def ex_create_group(self, name, location=None):
        """
        Create an empty group.

        You can specify the location as well.

        :param     group:     name of the group (required)
        :type      group:     ``str``

        :param     location: location were to create the group
        :type      location: :class:`NodeLocation`

        :returns:            the created group
        :rtype:              :class:`NodeGroup`
        """
        # prepare the element
        vapp = ET.Element('virtualAppliance')
        vapp_name = ET.SubElement(vapp, 'name')
        vapp_name.text = name

        if location is None:
            location = self.list_locations()[0]
        elif location not in self.list_locations():
            raise LibcloudError('Location does not exist')

        link_vdc = self.connection.cache['locations'][location]
        e_vdc = self.connection.request(link_vdc).object

        creation_link = get_href(e_vdc, 'virtualappliances')
        headers = {'Content-type': self.VAPP_MIME_TYPE}
        vapp = self.connection.request(creation_link, data=tostring(vapp),
                                       headers=headers, method='POST').object

        uri_vapp = get_href(vapp, 'edit')

        return NodeGroup(self, vapp.findtext('name'),
                         uri=uri_vapp)

    def ex_destroy_group(self, group):
        """
        Destroy a group.

        Be careful! Destroying a group means destroying all the :class:`Node`s
        there and the group itself!

        If there is currently any action over any :class:`Node` of the
        :class:`NodeGroup`, then the method will raise an exception.

        :param     name: The group (required)
        :type      name: :class:`NodeGroup`

        :return:         If the group was destroyed successfully
        :rtype:          ``bool``
        """
        # Refresh group state
        e_group = self.connection.request(group.uri).object
        state = e_group.findtext('state')

        if state not in ['NOT_DEPLOYED', 'DEPLOYED']:
            error = 'Can not destroy group because of current state'
            raise LibcloudError(error, self)

        if state == 'DEPLOYED':
            # prepare the element that forces the undeploy
            vm_task = ET.Element('virtualmachinetask')
            force_undeploy = ET.SubElement(vm_task, 'forceUndeploy')
            force_undeploy.text = 'True'

            # Set the URI
            undeploy_uri = group.uri + '/action/undeploy'

            # Prepare the headers
            headers = {'Content-type': self.VM_TASK_MIME_TYPE}
            res = self.connection.async_request(action=undeploy_uri,
                                                method='POST',
                                                data=tostring(vm_task),
                                                headers=headers)

        if state == 'NOT_DEPLOYED' or res.async_success():
            # The node is no longer deployed. Unregister it.
            self.connection.request(action=group.uri,
                                    method='DELETE')
            return True
        else:
            return False

    def ex_list_groups(self, location=None):
        """
        List all groups.

        :param location: filter the groups by location (optional)
        :type  location: a :class:`NodeLocation` instance.

        :return:         the list of :class:`NodeGroup`
        """
        groups = []
        for vdc in self._get_locations(location):
            link_vdc = self.connection.cache['locations'][vdc]
            e_vdc = self.connection.request(link_vdc).object
            apps_link = get_href(e_vdc, 'virtualappliances')
            vapps = self.connection.request(apps_link).object
            for vapp in vapps.findall('virtualAppliance'):
                nodes = []
                vms_link = get_href(vapp, 'virtualmachines')
                headers = {'Accept': self.NODES_MIME_TYPE}
                vms = self.connection.request(vms_link, headers=headers).object
                for vm in vms.findall('virtualmachinewithnode'):
                    nodes.append(self._to_node(vm, self))

                group = NodeGroup(self, vapp.findtext('name'),
                                  nodes, get_href(vapp, 'edit'))
                groups.append(group)

        return groups

    def list_images(self, location=None):
        """
        List images on Abiquo Repositories

        :keyword location: The location to list images for.
        :type    location: :class:`NodeLocation`

        :return:           list of node image objects
        :rtype:            ``list`` of :class:`NodeImage`
        """
        enterprise_id = self._get_enterprise_id()
        uri = '/admin/enterprises/%s/datacenterrepositories/' % (enterprise_id)
        repos = self.connection.request(uri).object

        images = []
        for repo in repos.findall('datacenterRepository'):
            # filter by location. Skips when the name of the location
            # is different from the 'datacenterRepository' element
            for vdc in self._get_locations(location):
                # Check if the virtual datacenter belongs to this repo
                link_vdc = self.connection.cache['locations'][vdc]
                e_vdc = self.connection.request(link_vdc).object
                dc_link_vdc = get_href(e_vdc, 'datacenter')
                dc_link_repo = get_href(repo, 'datacenter')

                if dc_link_vdc == dc_link_repo:
                    # Filter the template in case we don't have it yet
                    url_templates = get_href(repo, 'virtualmachinetemplates')
                    hypervisor_type = e_vdc.findtext('hypervisorType')
                    params = {'hypervisorTypeName': hypervisor_type}
                    templates = self.connection.request(url_templates,
                                                        params).object
                    for templ in templates.findall('virtualMachineTemplate'):
                        # Avoid duplicated templates
                        id_template = templ.findtext('id')
                        ids = [image.id for image in images]
                        if id_template not in ids:
                            images.append(self._to_nodeimage(templ, self,
                                                             get_href(repo,
                                                                      'edit')))

        return images

    def list_locations(self):
        """
        Return list of locations where the user has access to.

        :return: the list of :class:`NodeLocation` available for the current
                 user
        :rtype:  ``list`` of :class:`NodeLocation`
        """
        return list(self.connection.cache['locations'].keys())

    def list_nodes(self, location=None):
        """
        List all nodes.

        :param location: Filter the groups by location (optional)
        :type  location: a :class:`NodeLocation` instance.

        :return:  List of node objects
        :rtype: ``list`` of :class:`Node`
        """
        nodes = []

        for group in self.ex_list_groups(location):
            nodes.extend(group.nodes)

        return nodes

    def list_sizes(self, location=None):
        """
        List sizes on a provider.

        Abiquo does not work with sizes. However, this method
        returns a list of predefined ones (copied from :class:`DummyNodeDriver`
        but without price neither bandwidth) to help the users to create their
        own.

        If you call the method :class:`AbiquoNodeDriver.create_node` with the
        size informed, it will just override the 'ram' value of the 'image'
        template. So it is no too much usefull work with sizes...

        :return: The list of sizes
        :rtype:  ``list`` of :class:`NodeSizes`
        """
        return [
            NodeSize(id=1,
                     name='Small',
                     ram=128,
                     disk=4,
                     bandwidth=None,
                     price=None,
                     driver=self),
            NodeSize(id=2,
                     name='Medium',
                     ram=512,
                     disk=16,
                     bandwidth=None,
                     price=None,
                     driver=self),
            NodeSize(id=3,
                     name='Big',
                     ram=4096,
                     disk=32,
                     bandwidth=None,
                     price=None,
                     driver=self),
            NodeSize(id=4,
                     name="XXL Big",
                     ram=4096 * 2,
                     disk=32 * 4,
                     bandwidth=None,
                     price=None,
                     driver=self)
        ]

    def reboot_node(self, node):
        """
        Reboot a node.

        :param node: The node to be rebooted
        :type node: :class:`Node`

        :return: True if the reboot was successful, otherwise False
        :rtype: ``bool``
        """
        reboot_uri = node.extra['uri_id'] + '/action/reset'
        res = self.connection.async_request(action=reboot_uri, method='POST')
        return res.async_success()

    # -------------------------
    # Extenstion methods
    # -------------------------

    def _ex_connection_class_kwargs(self):
        """
        Set the endpoint as an extra :class:`AbiquoConnection` argument.

        According to Connection code, the "url" argument should be
        parsed properly to connection.

        :return: ``dict`` of :class:`AbiquoConnection` input arguments
        """

        return {'url': self.endpoint}

    def _deploy_remote(self, e_vm):
        """
        Asynchronous call to create the node.
        """
        # --------------------------------------------------------
        #     Deploy the Node
        # --------------------------------------------------------
        # prepare the element that forces the deploy
        vm_task = ET.Element('virtualmachinetask')
        force_deploy = ET.SubElement(vm_task, 'forceEnterpriseSoftLimits')
        force_deploy.text = 'True'

        # Prepare the headers
        headers = {'Content-type': self.VM_TASK_MIME_TYPE}
        link_deploy = get_href(e_vm, 'deploy')
        res = self.connection.async_request(action=link_deploy, method='POST',
                                            data=tostring(vm_task),
                                            headers=headers)
        if not res.async_success():
            raise LibcloudError('Could not run the node', self)

    def _to_location(self, vdc, dc, driver):
        """
        Generates the :class:`NodeLocation` class.
        """
        identifier = vdc.findtext('id')
        name = vdc.findtext('name')
        country = dc.findtext('name')
        return NodeLocation(identifier, name, country, driver)

    def _to_node(self, vm, driver):
        """
        Generates the :class:`Node` class.
        """
        identifier = vm.findtext('id')
        name = vm.findtext('nodeName')
        state = AbiquoResponse.NODE_STATE_MAP[vm.findtext('state')]

        link_image = get_href(vm, 'virtualmachinetemplate')
        image_element = self.connection.request(link_image).object
        repo_link = get_href(image_element, 'datacenterrepository')
        image = self._to_nodeimage(image_element, self, repo_link)

        # Fill the 'ips' data
        private_ips = []
        public_ips = []
        nics_element = self.connection.request(get_href(vm, 'nics')).object
        for nic in nics_element.findall('nic'):
            ip = nic.findtext('ip')
            for link in nic.findall('link'):
                rel = link.attrib['rel']
                if rel == 'privatenetwork':
                    private_ips.append(ip)
                elif rel in ['publicnetwork', 'externalnetwork',
                             'unmanagednetwork']:
                    public_ips.append(ip)

        extra = {'uri_id': get_href(vm, 'edit')}

        if vm.find('vdrpIp') is not None:
            extra['vdrp_ip'] = vm.findtext('vdrpIP')
            extra['vdrp_port'] = vm.findtext('vdrpPort')

        return Node(identifier, name, state, public_ips, private_ips,
                    driver, image=image, extra=extra)

    def _to_nodeimage(self, template, driver, repo):
        """
        Generates the :class:`NodeImage` class.
        """
        identifier = template.findtext('id')
        name = template.findtext('name')
        url = get_href(template, 'edit')
        extra = {'repo': repo, 'url': url}
        return NodeImage(identifier, name, driver, extra)

    def _get_locations(self, location=None):
        """
        Returns the locations as a generator.
        """
        if location is not None:
            yield location
        else:
            for loc in self.list_locations():
                yield loc

    def _get_enterprise_id(self):
        """
        Returns the identifier of the logged user's enterprise.
        """
        return self.connection.cache['enterprise'].findtext('id')

    def _define_create_node_location(self, **kwargs):
        """
        Search for a location where to create the node.

        Based on 'create_node' **kwargs argument, decide in which
        location will be created.
        """
        # First, get image location
        if 'image' not in kwargs:
            error = "'image' parameter is mandatory"
            raise LibcloudError(error, self)

        image = kwargs['image']

        # Get the location argument
        location = None
        if 'location' in kwargs:
            location = kwargs['location']
            if location not in self.list_locations():
                raise LibcloudError('Location does not exist')

        # Check if the image is compatible with any of the locations or
        # the input location
        loc = None
        target_loc = None
        for candidate_loc in self._get_locations(location):
            link_vdc = self.connection.cache['locations'][candidate_loc]
            e_vdc = self.connection.request(link_vdc).object
            # url_location = get_href(e_vdc, 'datacenter')
            for img in self.list_images(candidate_loc):
                if img.id == image.id:
                    loc = e_vdc
                    target_loc = candidate_loc
                    break

        if loc is None:
            error = 'The image can not be used in any location'
            raise LibcloudError(error, self)

        return loc, target_loc

    def _define_create_node_group(self, xml_loc, loc, **kwargs):
        """
        Search for a group where to create the node.

        If we can not find any group, create it into argument 'location'
        """
        if 'group_name' not in kwargs:
            group_name = NodeGroup.DEFAULT_GROUP_NAME
        else:
            group_name = kwargs['group_name']

        # We search if the group is already defined into the location
        groups_link = get_href(xml_loc, 'virtualappliances')
        vapps_element = self.connection.request(groups_link).object
        target_group = None
        for vapp in vapps_element.findall('virtualAppliance'):
            if vapp.findtext('name') == group_name:
                uri_vapp = get_href(vapp, 'edit')
                return NodeGroup(self, vapp.findtext('name'), uri=uri_vapp)

        # target group not found: create it. Since it is an extension of
        # the basic 'libcloud' functionality, we try to be as flexible as
        # possible.
        if target_group is None:
            return self.ex_create_group(group_name, loc)

    def _define_create_node_node(self, group, **kwargs):
        """
        Defines the node before to create.

        In Abiquo, you first need to 'register' or 'define' the node in
        the API before to create it into the target hypervisor.
        """
        vm = ET.Element('virtualmachinewithnode')
        if 'name' in kwargs:
            vmname = ET.SubElement(vm, 'nodeName')
            vmname.text = kwargs['name']
        attrib = {'type': 'application/vnd.abiquo/virtualmachinetemplate+xml',
                  'rel': 'virtualmachinetemplate',
                  'href': kwargs['image'].extra['url']}
        ET.SubElement(vm, 'link', attrib=attrib)
        headers = {'Content-type': self.NODE_MIME_TYPE}

        if 'size' in kwargs:
            # Override the 'NodeSize' data
            ram = ET.SubElement(vm, 'ram')
            ram.text = str(kwargs['size'].ram)
            hd = ET.SubElement(vm, 'hdInBytes')
            hd.text = str(int(kwargs['size'].disk) * self.GIGABYTE)

        # Create the virtual machine
        nodes_link = group.uri + '/virtualmachines'
        vm = self.connection.request(nodes_link, data=tostring(vm),
                                     headers=headers, method='POST').object
        edit_vm = get_href(vm, 'edit')
        headers = {'Accept': self.NODE_MIME_TYPE}

        return self.connection.request(edit_vm, headers=headers).object


class NodeGroup(object):
    """
    Group of virtual machines that can be managed together

    All :class:`Node`s in Abiquo must be defined inside a Virtual Appliance.
    We offer a way to handle virtual appliances (called NodeGroup to
    maintain some kind of name conventions here) inside the
    :class:`AbiquoNodeDriver` without breaking compatibility of the rest of
    libcloud API.

    If the user does not want to handle groups, all the virtual machines
    will be created inside a group named 'libcloud'
    """
    DEFAULT_GROUP_NAME = 'libcloud'

    def __init__(self, driver, name=DEFAULT_GROUP_NAME, nodes=[], uri=''):
        """
        Initialize a new group object.
        """
        self.driver = driver
        self.name = name
        self.nodes = nodes
        self.uri = uri

    def __repr__(self):
        return (('<NodeGroup: name=%s, nodes=[%s] >')
                % (self.name, ",".join(map(str, self.nodes))))

    def destroy(self):
        """
        Destroys the group delegating the execution to
        :class:`AbiquoNodeDriver`.
        """
        return self.driver.ex_destroy_group(self)
