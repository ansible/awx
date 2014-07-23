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
Provider related utilities
"""

from libcloud.utils.misc import get_driver as _get_provider_driver
from libcloud.utils.misc import set_driver as _set_provider_driver
from libcloud.compute.types import Provider, DEPRECATED_RACKSPACE_PROVIDERS
from libcloud.compute.types import OLD_CONSTANT_TO_NEW_MAPPING

__all__ = [
    "Provider",
    "DRIVERS",
    "get_driver"]

DRIVERS = {
    Provider.DUMMY:
    ('libcloud.compute.drivers.dummy', 'DummyNodeDriver'),
    Provider.EC2_US_EAST:
    ('libcloud.compute.drivers.ec2', 'EC2NodeDriver'),
    Provider.EC2_EU_WEST:
    ('libcloud.compute.drivers.ec2', 'EC2EUNodeDriver'),
    Provider.EC2_US_WEST:
    ('libcloud.compute.drivers.ec2', 'EC2USWestNodeDriver'),
    Provider.EC2_US_WEST_OREGON:
    ('libcloud.compute.drivers.ec2', 'EC2USWestOregonNodeDriver'),
    Provider.EC2_AP_SOUTHEAST:
    ('libcloud.compute.drivers.ec2', 'EC2APSENodeDriver'),
    Provider.EC2_AP_NORTHEAST:
    ('libcloud.compute.drivers.ec2', 'EC2APNENodeDriver'),
    Provider.EC2_SA_EAST:
    ('libcloud.compute.drivers.ec2', 'EC2SAEastNodeDriver'),
    Provider.EC2_AP_SOUTHEAST2:
    ('libcloud.compute.drivers.ec2', 'EC2APSESydneyNodeDriver'),
    Provider.ECP:
    ('libcloud.compute.drivers.ecp', 'ECPNodeDriver'),
    Provider.ELASTICHOSTS:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsNodeDriver'),
    Provider.ELASTICHOSTS_UK1:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsUK1NodeDriver'),
    Provider.ELASTICHOSTS_UK2:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsUK2NodeDriver'),
    Provider.ELASTICHOSTS_US1:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsUS1NodeDriver'),
    Provider.ELASTICHOSTS_US2:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsUS2NodeDriver'),
    Provider.ELASTICHOSTS_US3:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsUS3NodeDriver'),
    Provider.ELASTICHOSTS_CA1:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsCA1NodeDriver'),
    Provider.ELASTICHOSTS_AU1:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsAU1NodeDriver'),
    Provider.ELASTICHOSTS_CN1:
    ('libcloud.compute.drivers.elastichosts', 'ElasticHostsCN1NodeDriver'),
    Provider.SKALICLOUD:
    ('libcloud.compute.drivers.skalicloud', 'SkaliCloudNodeDriver'),
    Provider.SERVERLOVE:
    ('libcloud.compute.drivers.serverlove', 'ServerLoveNodeDriver'),
    Provider.CLOUDSIGMA:
    ('libcloud.compute.drivers.cloudsigma', 'CloudSigmaNodeDriver'),
    Provider.GCE:
    ('libcloud.compute.drivers.gce', 'GCENodeDriver'),
    Provider.GOGRID:
    ('libcloud.compute.drivers.gogrid', 'GoGridNodeDriver'),
    Provider.RACKSPACE:
    ('libcloud.compute.drivers.rackspace', 'RackspaceNodeDriver'),
    Provider.RACKSPACE_FIRST_GEN:
    ('libcloud.compute.drivers.rackspace', 'RackspaceFirstGenNodeDriver'),
    Provider.HPCLOUD:
    ('libcloud.compute.drivers.hpcloud', 'HPCloudNodeDriver'),
    Provider.KILI:
    ('libcloud.compute.drivers.kili', 'KiliCloudNodeDriver'),
    Provider.VPSNET:
    ('libcloud.compute.drivers.vpsnet', 'VPSNetNodeDriver'),
    Provider.LINODE:
    ('libcloud.compute.drivers.linode', 'LinodeNodeDriver'),
    Provider.RIMUHOSTING:
    ('libcloud.compute.drivers.rimuhosting', 'RimuHostingNodeDriver'),
    Provider.VOXEL:
    ('libcloud.compute.drivers.voxel', 'VoxelNodeDriver'),
    Provider.SOFTLAYER:
    ('libcloud.compute.drivers.softlayer', 'SoftLayerNodeDriver'),
    Provider.EUCALYPTUS:
    ('libcloud.compute.drivers.ec2', 'EucNodeDriver'),
    Provider.IBM:
    ('libcloud.compute.drivers.ibm_sce', 'IBMNodeDriver'),
    Provider.OPENNEBULA:
    ('libcloud.compute.drivers.opennebula', 'OpenNebulaNodeDriver'),
    Provider.DREAMHOST:
    ('libcloud.compute.drivers.dreamhost', 'DreamhostNodeDriver'),
    Provider.BRIGHTBOX:
    ('libcloud.compute.drivers.brightbox', 'BrightboxNodeDriver'),
    Provider.NIMBUS:
    ('libcloud.compute.drivers.ec2', 'NimbusNodeDriver'),
    Provider.BLUEBOX:
    ('libcloud.compute.drivers.bluebox', 'BlueboxNodeDriver'),
    Provider.GANDI:
    ('libcloud.compute.drivers.gandi', 'GandiNodeDriver'),
    Provider.OPSOURCE:
    ('libcloud.compute.drivers.opsource', 'OpsourceNodeDriver'),
    Provider.OPENSTACK:
    ('libcloud.compute.drivers.openstack', 'OpenStackNodeDriver'),
    Provider.NINEFOLD:
    ('libcloud.compute.drivers.ninefold', 'NinefoldNodeDriver'),
    Provider.VCLOUD:
    ('libcloud.compute.drivers.vcloud', 'VCloudNodeDriver'),
    Provider.TERREMARK:
    ('libcloud.compute.drivers.vcloud', 'TerremarkDriver'),
    Provider.CLOUDSTACK:
    ('libcloud.compute.drivers.cloudstack', 'CloudStackNodeDriver'),
    Provider.LIBVIRT:
    ('libcloud.compute.drivers.libvirt_driver', 'LibvirtNodeDriver'),
    Provider.JOYENT:
    ('libcloud.compute.drivers.joyent', 'JoyentNodeDriver'),
    Provider.VCL:
    ('libcloud.compute.drivers.vcl', 'VCLNodeDriver'),
    Provider.KTUCLOUD:
    ('libcloud.compute.drivers.ktucloud', 'KTUCloudNodeDriver'),
    Provider.HOSTVIRTUAL:
    ('libcloud.compute.drivers.hostvirtual', 'HostVirtualNodeDriver'),
    Provider.ABIQUO:
    ('libcloud.compute.drivers.abiquo', 'AbiquoNodeDriver'),
    Provider.DIGITAL_OCEAN:
    ('libcloud.compute.drivers.digitalocean', 'DigitalOceanNodeDriver'),
    Provider.NEPHOSCALE:
    ('libcloud.compute.drivers.nephoscale', 'NephoscaleNodeDriver'),
    Provider.CLOUDFRAMES:
    ('libcloud.compute.drivers.cloudframes', 'CloudFramesNodeDriver'),
    Provider.EXOSCALE:
    ('libcloud.compute.drivers.exoscale', 'ExoscaleNodeDriver'),
    Provider.IKOULA:
    ('libcloud.compute.drivers.ikoula', 'IkoulaNodeDriver'),
    Provider.OUTSCALE_SAS:
    ('libcloud.compute.drivers.ec2', 'OutscaleSASNodeDriver'),
    Provider.OUTSCALE_INC:
    ('libcloud.compute.drivers.ec2', 'OutscaleINCNodeDriver'),

    # Deprecated
    Provider.CLOUDSIGMA_US:
    ('libcloud.compute.drivers.cloudsigma', 'CloudSigmaLvsNodeDriver'),
}


def get_driver(provider):
    if provider in DEPRECATED_RACKSPACE_PROVIDERS:
        id_to_name_map = dict([(v, k) for k, v in Provider.__dict__.items()])
        old_name = id_to_name_map[provider]
        new_name = id_to_name_map[OLD_CONSTANT_TO_NEW_MAPPING[provider]]

        url = 'http://s.apache.org/lc0140un'
        msg = ('Provider constant %s has been removed. New constant '
               'is now called %s.\n'
               'For more information on this change and how to modify your '
               'code to work with it, please visit: %s' %
               (old_name, new_name, url))
        raise Exception(msg)

    return _get_provider_driver(DRIVERS, provider)


def set_driver(provider, module, klass):
    return _set_provider_driver(DRIVERS, provider, module, klass)
