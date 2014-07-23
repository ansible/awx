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
Base types used by other parts of libcloud
"""

from libcloud.common.types import LibcloudError, MalformedResponseError
from libcloud.common.types import InvalidCredsError, InvalidCredsException

__all__ = [
    "Provider",
    "NodeState",
    "DeploymentError",
    "DeploymentException",

    # @@TR: should the unused imports below be exported?
    "LibcloudError",
    "MalformedResponseError",
    "InvalidCredsError",
    "InvalidCredsException",
    "DEPRECATED_RACKSPACE_PROVIDERS",
    "OLD_CONSTANT_TO_NEW_MAPPING"
]


class Provider(object):
    """
    Defines for each of the supported providers

    :cvar DUMMY: Example provider
    :cvar EC2_US_EAST: Amazon AWS US N. Virgina
    :cvar EC2_US_WEST: Amazon AWS US N. California
    :cvar EC2_EU_WEST: Amazon AWS EU Ireland
    :cvar RACKSPACE: Rackspace next-gen OpenStack based Cloud Servers
    :cvar RACKSPACE_FIRST_GEN: Rackspace First Gen Cloud Servers
    :cvar GCE: Google Compute Engine
    :cvar GOGRID: GoGrid
    :cvar VPSNET: VPS.net
    :cvar LINODE: Linode.com
    :cvar VCLOUD: vmware vCloud
    :cvar RIMUHOSTING: RimuHosting.com
    :cvar ECP: Enomaly
    :cvar IBM: IBM Developer Cloud
    :cvar OPENNEBULA: OpenNebula.org
    :cvar DREAMHOST: DreamHost Private Server
    :cvar ELASTICHOSTS: ElasticHosts.com
    :cvar CLOUDSIGMA: CloudSigma
    :cvar NIMBUS: Nimbus
    :cvar BLUEBOX: Bluebox
    :cvar OPSOURCE: Opsource Cloud
    :cvar NINEFOLD: Ninefold
    :cvar TERREMARK: Terremark
    :cvar EC2_US_WEST_OREGON: Amazon AWS US West 2 (Oregon)
    :cvar CLOUDSTACK: CloudStack
    :cvar CLOUDSIGMA_US: CloudSigma US Las Vegas
    :cvar LIBVIRT: Libvirt driver
    :cvar JOYENT: Joyent driver
    :cvar VCL: VCL driver
    :cvar KTUCLOUD: kt ucloud driver
    :cvar GRIDSPOT: Gridspot driver
    :cvar ABIQUO: Abiquo driver
    :cvar NEPHOSCALE: NephoScale driver
    :cvar EXOSCALE: Exoscale driver.
    :cvar IKOULA: Ikoula driver.
    :cvar OUTSCALE_SAS: Outscale SAS driver.
    :cvar OUTSCALE_INC: Outscale INC driver.
    """
    DUMMY = 'dummy'
    EC2 = 'ec2_us_east'
    RACKSPACE = 'rackspace'
    GCE = 'gce'
    GOGRID = 'gogrid'
    VPSNET = 'vpsnet'
    LINODE = 'linode'
    VCLOUD = 'vcloud'
    RIMUHOSTING = 'rimuhosting'
    VOXEL = 'voxel'
    SOFTLAYER = 'softlayer'
    EUCALYPTUS = 'eucalyptus'
    ECP = 'ecp'
    IBM = 'ibm'
    OPENNEBULA = 'opennebula'
    DREAMHOST = 'dreamhost'
    ELASTICHOSTS = 'elastichosts'
    BRIGHTBOX = 'brightbox'
    CLOUDSIGMA = 'cloudsigma'
    NIMBUS = 'nimbus'
    BLUEBOX = 'bluebox'
    GANDI = 'gandi'
    OPSOURCE = 'opsource'
    OPENSTACK = 'openstack'
    SKALICLOUD = 'skalicloud'
    SERVERLOVE = 'serverlove'
    NINEFOLD = 'ninefold'
    TERREMARK = 'terremark'
    CLOUDSTACK = 'cloudstack'
    LIBVIRT = 'libvirt'
    JOYENT = 'joyent'
    VCL = 'vcl'
    KTUCLOUD = 'ktucloud'
    GRIDSPOT = 'gridspot'
    RACKSPACE_FIRST_GEN = 'rackspace_first_gen'
    HOSTVIRTUAL = 'hostvirtual'
    ABIQUO = 'abiquo'
    DIGITAL_OCEAN = 'digitalocean'
    NEPHOSCALE = 'nephoscale'
    CLOUDFRAMES = 'cloudframes'
    EXOSCALE = 'exoscale'
    IKOULA = 'ikoula'
    OUTSCALE_SAS = 'outscale_sas'
    OUTSCALE_INC = 'outscale_inc'

    # OpenStack based providers
    HPCLOUD = 'hpcloud'
    KILI = 'kili'

    # Deprecated constants which are still supported
    EC2_US_EAST = 'ec2_us_east'
    EC2_EU = 'ec2_eu_west'  # deprecated name
    EC2_EU_WEST = 'ec2_eu_west'
    EC2_US_WEST = 'ec2_us_west'
    EC2_AP_SOUTHEAST = 'ec2_ap_southeast'
    EC2_AP_NORTHEAST = 'ec2_ap_northeast'
    EC2_US_WEST_OREGON = 'ec2_us_west_oregon'
    EC2_SA_EAST = 'ec2_sa_east'
    EC2_AP_SOUTHEAST2 = 'ec2_ap_southeast_2'

    ELASTICHOSTS_UK1 = 'elastichosts_uk1'
    ELASTICHOSTS_UK2 = 'elastichosts_uk2'
    ELASTICHOSTS_US1 = 'elastichosts_us1'
    ELASTICHOSTS_US2 = 'elastichosts_us2'
    ELASTICHOSTS_US3 = 'elastichosts_us3'
    ELASTICHOSTS_CA1 = 'elastichosts_ca1'
    ELASTICHOSTS_AU1 = 'elastichosts_au1'
    ELASTICHOSTS_CN1 = 'elastichosts_cn1'

    CLOUDSIGMA_US = 'cloudsigma_us'

    # Deprecated constants which aren't supported anymore
    RACKSPACE_UK = 'rackspace_uk'
    RACKSPACE_NOVA_BETA = 'rackspace_nova_beta'
    RACKSPACE_NOVA_DFW = 'rackspace_nova_dfw'
    RACKSPACE_NOVA_LON = 'rackspace_nova_lon'
    RACKSPACE_NOVA_ORD = 'rackspace_nova_ord'

    # Removed
    # SLICEHOST = 'slicehost'


DEPRECATED_RACKSPACE_PROVIDERS = [Provider.RACKSPACE_UK,
                                  Provider.RACKSPACE_NOVA_BETA,
                                  Provider.RACKSPACE_NOVA_DFW,
                                  Provider.RACKSPACE_NOVA_LON,
                                  Provider.RACKSPACE_NOVA_ORD]
OLD_CONSTANT_TO_NEW_MAPPING = {
    Provider.RACKSPACE: Provider.RACKSPACE_FIRST_GEN,
    Provider.RACKSPACE_UK: Provider.RACKSPACE_FIRST_GEN,

    Provider.RACKSPACE_NOVA_BETA: Provider.RACKSPACE,
    Provider.RACKSPACE_NOVA_DFW: Provider.RACKSPACE,
    Provider.RACKSPACE_NOVA_LON: Provider.RACKSPACE,
    Provider.RACKSPACE_NOVA_ORD: Provider.RACKSPACE
}


class NodeState(object):
    """
    Standard states for a node

    :cvar RUNNING: Node is running.
    :cvar REBOOTING: Node is rebooting.
    :cvar TERMINATED: Node is terminated. This node can't be started later on.
    :cvar STOPPED: Node is stopped. This node can be started later on.
    :cvar PENDING: Node is pending.
    :cvar UNKNOWN: Node state is unknown.
    """
    RUNNING = 0
    REBOOTING = 1
    TERMINATED = 2
    PENDING = 3
    UNKNOWN = 4
    STOPPED = 5


class Architecture(object):
    """
    Image and size architectures.

    :cvar I386: i386 (32 bt)
    :cvar X86_64: x86_64 (64 bit)
    """
    I386 = 0
    X86_X64 = 1


class DeploymentError(LibcloudError):
    """
    Exception used when a Deployment Task failed.

    :ivar node: :class:`Node` on which this exception happened, you might want
                to call :func:`Node.destroy`
    """
    def __init__(self, node, original_exception=None, driver=None):
        self.node = node
        self.value = original_exception
        self.driver = driver

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (('<DeploymentError: node=%s, error=%s, driver=%s>'
                % (self.node.id, str(self.value), str(self.driver))))


class KeyPairError(LibcloudError):
    error_type = 'KeyPairError'

    def __init__(self, name, driver):
        self.name = name
        self.value = 'Key pair with name %s does not exist' % (name)
        super(KeyPairError, self).__init__(value=self.value, driver=driver)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('<%s name=%s, value=%s, driver=%s>' %
                (self.error_type, self.name, self.value, self.driver.name))


class KeyPairDoesNotExistError(KeyPairError):
    error_type = 'KeyPairDoesNotExistError'


"""Deprecated alias of :class:`DeploymentException`"""
DeploymentException = DeploymentError
