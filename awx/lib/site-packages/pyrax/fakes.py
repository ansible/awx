#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import random
import time
import uuid

import pyrax
from pyrax.autoscale import AutoScaleClient
from pyrax.autoscale import AutoScalePolicy
from pyrax.autoscale import AutoScaleWebhook
from pyrax.autoscale import ScalingGroup
from pyrax.autoscale import ScalingGroupManager
from pyrax.cf_wrapper.client import BulkDeleter
from pyrax.cf_wrapper.client import FolderUploader
from pyrax.cf_wrapper.container import Container
from pyrax.cf_wrapper.storage_object import StorageObject
from pyrax.client import BaseClient
from pyrax.clouddatabases import CloudDatabaseClient
from pyrax.clouddatabases import CloudDatabaseDatabaseManager
from pyrax.clouddatabases import CloudDatabaseInstance
from pyrax.clouddatabases import CloudDatabaseManager
from pyrax.clouddatabases import CloudDatabaseUser
from pyrax.clouddatabases import CloudDatabaseUserManager
from pyrax.clouddatabases import CloudDatabaseVolume
from pyrax.cloudblockstorage import CloudBlockStorageClient
from pyrax.cloudblockstorage import CloudBlockStorageManager
from pyrax.cloudblockstorage import CloudBlockStorageSnapshot
from pyrax.cloudblockstorage import CloudBlockStorageVolume
from pyrax.cloudloadbalancers import CloudLoadBalancer
from pyrax.cloudloadbalancers import CloudLoadBalancerManager
from pyrax.cloudloadbalancers import CloudLoadBalancerClient
from pyrax.cloudloadbalancers import Node
from pyrax.cloudloadbalancers import VirtualIP
from pyrax.clouddns import CloudDNSClient
from pyrax.clouddns import CloudDNSDomain
from pyrax.clouddns import CloudDNSManager
from pyrax.clouddns import CloudDNSRecord
from pyrax.clouddns import CloudDNSPTRRecord
from pyrax.cloudnetworks import CloudNetwork
from pyrax.cloudnetworks import CloudNetworkClient
from pyrax.cloudmonitoring import CloudMonitorClient
from pyrax.cloudmonitoring import CloudMonitorEntity
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorNotification
from pyrax.image import Image
from pyrax.image import ImageClient
from pyrax.image import ImageManager
from pyrax.image import ImageMemberManager
from pyrax.image import ImageTagManager
from pyrax.queueing import Queue
from pyrax.queueing import QueueClaim
from pyrax.queueing import QueueMessage
from pyrax.queueing import QueueClient
from pyrax.queueing import QueueManager

import pyrax.exceptions as exc
from pyrax.identity.rax_identity import RaxIdentity
from pyrax.identity.keystone_identity import KeystoneIdentity
import pyrax.utils as utils


example_uri = "http://example.com"


class FakeResponse(object):
    headers = {}
    body = ""
    status_code = 200
    reason = "Oops"
    content = "Oops"

    @property
    def status(self):
        # TEMPORARY - until the cf_wrapper code is removed.
        return self.status_code

    @status.setter
    def status(self, val):
        # TEMPORARY - until the cf_wrapper code is removed.
        self.status_code = val

    def getheaders(self):
        return self.headers

    def read(self):
        return "Line1\nLine2"

    def get(self, arg):
        pass

    def json(self):
        return self.content


class FakeClient(object):
    user_agent = "Fake"
    USER_AGENT = "Fake"


class FakeContainer(Container):
    def _fetch_cdn_data(self):
        self._cdn_uri = None
        self._cdn_ttl = self.client.default_cdn_ttl
        self._cdn_ssl_uri = None
        self._cdn_streaming_uri = None
        self._cdn_ios_uri = None
        self._cdn_log_retention = False


class FakeStorageObject(StorageObject):
    def __init__(self, client, container, name=None, total_bytes=None,
            content_type=None, last_modified=None, etag=None, attdict=None):
        """
        The object can either be initialized with individual params, or by
        passing the dict that is returned by swiftclient.
        """
        self.client = client
        self.container = container
        self.name = name
        self.total_bytes = total_bytes
        self.content_type = content_type
        self.last_modified = last_modified
        self.etag = etag
        if attdict:
            self._read_attdict(attdict)


fake_attdict = {"name": "fake",
        "content-length": 42,
        "content-type": "text/html",
        "etag": "ABC",
        "last-modified": "Tue, 01 Jan 2013 01:02:03 GMT",
        }


class FakeServer(object):
    id = utils.random_unicode()


class FakeService(object):
    user_agent = "FakeService"
    USER_AGENT = "FakeService"

    def __init__(self, *args, **kwargs):
        self.client = FakeClient()
        self.Node = FakeNode
        self.VirtualIP = FakeVirtualIP
        self.loadbalancers = FakeLoadBalancer()
        self.id = utils.random_unicode()

    def authenticate(self):
        pass

    def get_protocols(self):
        return ["HTTP"]

    def get_algorithms(self):
        return ["RANDOM"]

    def get_usage(self):
        pass


class FakeCSClient(FakeService):
    def __init__(self, *args, **kwargs):
        super(FakeCSClient, self).__init__(*args, **kwargs)

        def dummy(self):
            pass

        self.servers = FakeService()
        utils.add_method(self.servers, dummy, "list")
        self.images = FakeService()
        utils.add_method(self.images, dummy, "list")
        self.flavors = FakeService()
        utils.add_method(self.flavors, dummy, "list")


class FakeFolderUploader(FolderUploader):
    def __init__(self, *args, **kwargs):
        super(FakeFolderUploader, self).__init__(*args, **kwargs)
        # Useful for when we mock out the run() method.
        self.actual_run = self.run
        self.run = self.fake_run

    def fake_run(self):
        pass


class FakeBulkDeleter(BulkDeleter):
    def __init__(self, *args, **kwargs):
        super(FakeBulkDeleter, self).__init__(*args, **kwargs)
        # Useful for when we mock out the run() method.
        self.actual_run = self.run
        self.run = self.fake_run

    def fake_run(self):
        time.sleep(0.0001)
        self.results = {}
        self.completed = True


class FakeEntryPoint(object):
    def __init__(self, name):
        self.name = name

    def load(self):
        def dummy(*args, **kwargs):
            return self.name
        return dummy

fakeEntryPoints = [FakeEntryPoint("a"), FakeEntryPoint("b"),
        FakeEntryPoint("c")]


class FakeManager(object):
    api = FakeClient()

    def list(self):
        pass

    def get(self, item):
        pass

    def delete(self, item):
        pass

    def create(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass

    def action(self, item, action_type, body={}):
        pass


class FakeException(BaseException):
    pass


class FakeServiceCatalog(object):
    def __init__(self, *args, **kwargs):
        pass

    def get_token(self):
        return "fake_token"

    def url_for(self, attr=None, filter_value=None,
            service_type=None, endpoint_type="publicURL",
            service_name=None, volume_service_name=None):
        if filter_value == "ALL":
            raise exc.AmbiguousEndpoints
        elif filter_value == "KEY":
            raise KeyError
        elif filter_value == "EP":
            raise exc.EndpointNotFound
        return "http://example.com"


class FakeKeyring(object):
    password_set = False

    def get_password(self, *args, **kwargs):
        return "FAKE_TOKEN|FAKE_URL"

    def set_password(self, *args, **kwargs):
        self.password_set = True


class FakeEntity(object):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_unicode()

    def get(self, *args, **kwargs):
        pass

    def list(self, *args, **kwargs):
        pass


class FakeDatabaseUser(CloudDatabaseUser):
    pass


class FakeDatabaseVolume(CloudDatabaseVolume):
    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        self.size = 1
        self.used = 0.2


class FakeDatabaseInstance(CloudDatabaseInstance):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_unicode()
        self.manager = FakeDatabaseManager()
        self.manager.api = FakeDatabaseClient()
        self._database_manager = CloudDatabaseDatabaseManager(
                FakeDatabaseClient())
        self._user_manager = CloudDatabaseUserManager(FakeDatabaseClient())
        self.volume = FakeDatabaseVolume(self)


class FakeDatabaseManager(CloudDatabaseManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeDatabaseClient()
        super(FakeDatabaseManager, self).__init__(api, *args, **kwargs)
        self.uri_base = "instances"


class FakeDatabaseClient(CloudDatabaseClient):
    def __init__(self, *args, **kwargs):
        self._manager = FakeDatabaseManager(self)
        self._flavor_manager = FakeManager()
        super(FakeDatabaseClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeNovaVolumeClient(BaseClient):
    def __init__(self, *args, **kwargs):
        pass


class FakeBlockStorageManager(CloudBlockStorageManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeBlockStorageClient()
        super(FakeBlockStorageManager, self).__init__(api, *args, **kwargs)


class FakeBlockStorageVolume(CloudBlockStorageVolume):
    def __init__(self, *args, **kwargs):
        volname = utils.random_unicode(8)
        self.id = utils.random_unicode()
        self.manager = FakeBlockStorageManager()
        self._nova_volumes = FakeNovaVolumeClient()


class FakeBlockStorageSnapshot(CloudBlockStorageSnapshot):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_unicode()
        self.manager = FakeManager()
        self.status = "available"


class FakeBlockStorageClient(CloudBlockStorageClient):
    def __init__(self, *args, **kwargs):
        self._types_manager = FakeManager()
        self._snapshot_manager = FakeManager()
        super(FakeBlockStorageClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeLoadBalancerClient(CloudLoadBalancerClient):
    def __init__(self, *args, **kwargs):
        super(FakeLoadBalancerClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeLoadBalancerManager(CloudLoadBalancerManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeLoadBalancerClient()
        super(FakeLoadBalancerManager, self).__init__(api, *args, **kwargs)


class FakeLoadBalancer(CloudLoadBalancer):
    def __init__(self, name=None, info=None, *args, **kwargs):
        name = name or utils.random_ascii()
        info = info or {"fake": "fake"}
        super(FakeLoadBalancer, self).__init__(name, info, *args, **kwargs)
        self.id = utils.random_ascii()
        self.port = random.randint(1, 256)
        self.manager = FakeLoadBalancerManager()


class FakeNode(Node):
    def __init__(self, address=None, port=None, condition=None, weight=None,
            status=None, parent=None, type=None, id=None):
        if address is None:
            address = "0.0.0.0"
        if port is None:
            port = 80
        if id is None:
            id = utils.random_unicode()
        super(FakeNode, self).__init__(address=address, port=port,
                condition=condition, weight=weight, status=status,
                parent=parent, type=type, id=id)


class FakeVirtualIP(VirtualIP):
    pass


class FakeStatusChanger(object):
    check_count = 0
    id = utils.random_unicode()

    @property
    def status(self):
        if self.check_count < 2:
            self.check_count += 1
            return "changing"
        return "ready"


class FakeDNSClient(CloudDNSClient):
    def __init__(self, *args, **kwargs):
        super(FakeDNSClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeDNSManager(CloudDNSManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeDNSClient()
        super(FakeDNSManager, self).__init__(api, *args, **kwargs)
        self.resource_class = FakeDNSDomain
        self.response_key = "domain"
        self.plural_response_key = "domains"
        self.uri_base = "domains"


class FakeDNSDomain(CloudDNSDomain):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_ascii()
        self.name = utils.random_unicode()
        self.manager = FakeDNSManager()


class FakeDNSRecord(CloudDNSRecord):
    def __init__(self, mgr, info, *args, **kwargs):
        super(FakeDNSRecord, self).__init__(mgr, info, *args, **kwargs)


class FakeDNSPTRRecord(CloudDNSPTRRecord):
    pass


class FakeDNSDevice(FakeLoadBalancer):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_unicode()


class FakeCloudNetworkClient(CloudNetworkClient):
    def __init__(self, *args, **kwargs):
        super(FakeCloudNetworkClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeCloudNetwork(CloudNetwork):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        label = kwargs.pop("label", kwargs.pop("name", utils.random_unicode()))
        info["label"] = label
        super(FakeCloudNetwork, self).__init__(manager=None, info=info, *args,
                **kwargs)
        self.id = uuid.uuid4()


class FakeAutoScaleClient(AutoScaleClient):
    def __init__(self, *args, **kwargs):
        self._manager = FakeManager()
        super(FakeAutoScaleClient, self).__init__(*args, **kwargs)


class FakeAutoScalePolicy(AutoScalePolicy):
    def __init__(self, *args, **kwargs):
        super(FakeAutoScalePolicy, self).__init__(*args, **kwargs)
        self.id = utils.random_ascii()


class FakeAutoScaleWebhook(AutoScaleWebhook):
    def __init__(self, *args, **kwargs):
        super(FakeAutoScaleWebhook, self).__init__(*args, **kwargs)
        self.id = utils.random_ascii()


class FakeScalingGroupManager(ScalingGroupManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeAutoScaleClient()
        super(FakeScalingGroupManager, self).__init__(api, *args, **kwargs)
        self.id = utils.random_ascii()


class FakeScalingGroup(ScalingGroup):
    def __init__(self, name=None, info=None, *args, **kwargs):
        name = name or utils.random_ascii()
        info = info or {"fake": "fake", "scalingPolicies": []}
        self.groupConfiguration = {}
        super(FakeScalingGroup, self).__init__(name, info, *args, **kwargs)
        self.id = utils.random_ascii()
        self.name = name
        self.manager = FakeScalingGroupManager()


class FakeCloudMonitorClient(CloudMonitorClient):
    def __init__(self, *args, **kwargs):
        super(FakeCloudMonitorClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeCloudMonitorEntity(CloudMonitorEntity):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        super(FakeCloudMonitorEntity, self).__init__(FakeManager(), info=info,
                *args, **kwargs)
        self.manager.api = FakeCloudMonitorClient()
        self.id = utils.random_unicode()


class FakeCloudMonitorCheck(CloudMonitorCheck):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        entity = kwargs.pop("entity", FakeCloudMonitorEntity())
        super(FakeCloudMonitorCheck, self).__init__(None, info, entity,
                *args, **kwargs)
        self.id = uuid.uuid4()


class FakeCloudMonitorNotification(CloudMonitorNotification):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        super(FakeCloudMonitorNotification, self).__init__(manager=None,
                info=info, *args, **kwargs)
        self.id = uuid.uuid4()


class FakeQueue(Queue):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        info["name"] = utils.random_unicode()
        mgr = kwargs.pop("manager", FakeQueueManager())
        super(FakeQueue, self).__init__(manager=mgr, info=info, *args, **kwargs)


class FakeQueueClaim(QueueClaim):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        info["name"] = utils.random_unicode()
        mgr = kwargs.pop("manager", FakeQueueManager())
        super(FakeQueueClaim, self).__init__(manager=mgr, info=info, *args,
                **kwargs)


class FakeQueueMessage(QueueMessage):
    def __init__(self, *args, **kwargs):
        id_ = utils.random_unicode()
        href = "http://example.com/%s" % id_
        info = kwargs.pop("info", {"href": href})
        info["name"] = utils.random_unicode()
        mgr = kwargs.pop("manager", FakeQueueManager())
        super(FakeQueueMessage, self).__init__(manager=mgr, info=info, *args,
                **kwargs)


class FakeQueueClient(QueueClient):
    def __init__(self, *args, **kwargs):
        super(FakeQueueClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeQueueManager(QueueManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeQueueClient()
        super(FakeQueueManager, self).__init__(api, *args, **kwargs)
        self.id = utils.random_ascii()


class FakeImage(Image):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        info["name"] = utils.random_unicode()
        info["id"] = utils.random_unicode()
        mgr = kwargs.pop("manager", FakeImageManager())
        kwargs["member_manager_class"] = FakeImageMemberManager
        kwargs["tag_manager_class"] = FakeImageTagManager
        super(FakeImage, self).__init__(mgr, info, *args, **kwargs)


class FakeImageClient(ImageClient):
    def __init__(self, *args, **kwargs):
        super(FakeImageClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeImageMemberManager(ImageMemberManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeImageClient()
        super(FakeImageMemberManager, self).__init__(api, *args, **kwargs)
        self.id = utils.random_ascii()


class FakeImageTagManager(ImageTagManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeImageClient()
        super(FakeImageTagManager, self).__init__(api, *args, **kwargs)
        self.id = utils.random_ascii()


class FakeImageManager(ImageManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeImageClient()
        super(FakeImageManager, self).__init__(api, *args, **kwargs)
        self.plural_response_key = "images"
        self.resource_class = FakeImage
        self.id = utils.random_ascii()


class FakeIdentity(RaxIdentity):
    """Class that returns canned authentication responses."""
    def __init__(self, *args, **kwargs):
        super(FakeIdentity, self).__init__(*args, **kwargs)
        self._good_username = "fakeuser"
        self._good_password = "fakeapikey"
        self._default_region = random.choice(("DFW", "ORD"))

    def authenticate(self):
        if ((self.username == self._good_username) and
                (self.password == self._good_password)):
            self._parse_response(self.fake_response())
            self.authenticated = True
        else:
            self.authenticated = False
            raise exc.AuthenticationFailed("No match for '%s'/'%s' "
                    "username/password" % (self.username, self.password))

    def auth_with_token(self, token, tenant_id=None, tenant_name=None):
        self.token = token
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.authenticated = True

    def get_token(self, force=False):
        return self.token

    def fake_response(self):
        return fake_identity_response


fake_config_file = """[settings]
identity_type = rackspace
keyring_username =
region = FAKE
custom_user_agent = FAKE
http_debug =
"""

# This will handle both singular and plural responses.
fake_identity_user_response = {
        "users": [{"name": "fake", "id": "fake"},
            {"name": "faker", "id": "faker"}],
        "user": {"name": "fake", "id": "fake"},
        "roles": [{u'description': 'User Admin Role.',
                'id': '3',
                'name': 'identity:user-admin'}],
        }

fake_identity_tenant_response = {"name": "fake", "id": "fake",
        "description": "fake", "enabled": True}

fake_identity_tenants_response = {
    "tenants": [
        {"name": "fake", "id": "fake", "description": "fake",
        "enabled": True},
        {"name": "faker", "id": "faker", "description": "faker",
        "enabled": True},
        ]}

fake_identity_tokens_response = {"access":
        {'metadata': {u'is_admin': 0,
            'roles': [u'asdfgh',
                'sdfghj',
                'dfghjk']},
        'serviceCatalog': [{u'endpoints': [
            {u'adminURL': 'http://10.0.0.0:8774/v2/qweqweqwe',
            'id': 'dddddddddd',
            'publicURL': 'http://10.0.0.0:8774/v2/qweqweqwe',
            'internalURL': 'http://10.0.0.0:8774/v2/qweqweqwe',
            'region': 'some_region'}],
            'endpoints_links': [],
            'name': 'nova',
            'type': 'compute'},
            {u'endpoints': [{u'adminURL': 'http://10.0.0.0:35357/v2.0',
            'id': 'qweqweqwe',
            'internalURL': 'http://10.0.0.0:5000/v2.0',
            'publicURL': 'http://10.0.0.0:5000/v2.0',
            'region': 'some_region'}],
            'endpoints_links': [],
            'name': 'keystone',
            'type': 'identity'}],
        'token': {u'expires': '1999-05-04T16:45:05Z',
            'id': 'qweqweqwe',
            'tenant': {u'description': 'admin Tenant',
                'enabled': True,
                'id': 'qweqweqwe',
                'name': 'admin'}},
        'user': {u'id': 'qweqweqwe',
            'name': 'admin',
            'roles': [{u'id': 'qweqweqwe', 'name': 'admin'},
                {u'id': 'qweqweqwe', 'name': 'KeystoneAdmin'},
                {u'id': 'qweqweqwe',
                'name': 'KeystoneServiceAdmin'}],
            'roles_links': [],
            'username': 'admin'}}}

fake_identity_endpoints_response = {"access": {
        "endpoints": ["fake", "faker", "fakest"]}}

fake_identity_response = {u'access':
    {u'serviceCatalog': [
        {u'endpoints': [{u'publicURL':
            'https://ord.loadbalancers.api.rackspacecloud.com/v1.0/000000',
            'region': 'ORD',
            'tenantId': '000000'},
            {u'publicURL':
            'https://dfw.loadbalancers.api.rackspacecloud.com/v1.0/000000',
            'region': 'DFW',
            'tenantId': '000000'},
            {u'publicURL':
            'https://syd.loadbalancers.api.rackspacecloud.com/v1.0/000000',
            'region': 'SYD',
            'tenantId': '000000'}],
        'name': 'cloudLoadBalancers',
        'type': 'rax:load-balancer'},
        {u'endpoints': [{u'internalURL':
            'https://snet-aa.fake1.clouddrive.com/v1/MossoCloudFS_abc',
            'publicURL': 'https://aa.fake1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'FAKE',
            'tenantId': 'MossoCloudFS_abc'},
            {u'internalURL':
            'https://snet-aa.dfw1.clouddrive.com/v1/MossoCloudFS_abc',
            'publicURL': 'https://aa.dfw1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'DFW',
            'tenantId': 'MossoCloudFS_abc'},
            {u'internalURL':
            'https://snet-aa.ord1.clouddrive.com/v1/MossoCloudFS_abc',
            'publicURL': 'https://aa.ord1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'ORD',
            'tenantId': 'MossoCloudFS_abc'},
            {u'internalURL':
            'https://snet-aa.syd1.clouddrive.com/v1/MossoCloudFS_abc',
            'publicURL': 'https://aa.ord1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'SYD',
            'tenantId': 'MossoCloudFS_abc'}],
        'name': 'cloudFiles',
        'type': 'object-store'},
        {u'endpoints': [{u'publicURL':
            'https://dfw.servers.api.rackspacecloud.com/v2/000000',
            'region': 'DFW',
            'tenantId': '000000',
            'versionId': '2',
            'versionInfo': 'https://dfw.servers.api.rackspacecloud.com/v2',
            'versionList': 'https://dfw.servers.api.rackspacecloud.com/'},
            {u'publicURL':
            'https://ord.servers.api.rackspacecloud.com/v2/000000',
            'region': 'ORD',
            'tenantId': '000000',
            'versionId': '2',
            'versionInfo': 'https://ord.servers.api.rackspacecloud.com/v2',
            'versionList': 'https://ord.servers.api.rackspacecloud.com/'},
            {u'publicURL':
            'https://syd.servers.api.rackspacecloud.com/v2/000000',
            'region': 'SYD',
            'tenantId': '000000',
            'versionId': '2',
            'versionInfo': 'https://syd.servers.api.rackspacecloud.com/v2',
            'versionList': 'https://syd.servers.api.rackspacecloud.com/'}],
        'name': 'cloudServersOpenStack',
        'type': 'compute'},
        {u'endpoints': [{u'publicURL':
        'https://dns.api.rackspacecloud.com/v1.0/000000',
        'tenantId': '000000'}],
        'name': 'cloudDNS',
        'type': 'rax:dns'},
        {u'endpoints': [{u'publicURL':
            'https://dfw.databases.api.rackspacecloud.com/v1.0/000000',
            'region': 'DFW',
            'tenantId': '000000'},
            {u'publicURL':
            'https://syd.databases.api.rackspacecloud.com/v1.0/000000',
            'region': 'SYD',
            'tenantId': '000000'},
            {u'publicURL':
            'https://ord.databases.api.rackspacecloud.com/v1.0/000000',
            'region': 'ORD',
            'tenantId': '000000'}],
        'name': 'cloudDatabases',
        'type': 'rax:database'},
        {u'endpoints': [{u'publicURL':
        'https://servers.api.rackspacecloud.com/v1.0/000000',
        'tenantId': '000000',
        'versionId': '1.0',
        'versionInfo': 'https://servers.api.rackspacecloud.com/v1.0',
        'versionList': 'https://servers.api.rackspacecloud.com/'}],
        'name': 'cloudServers',
        'type': 'compute'},
        {u'endpoints': [{u'publicURL':
            'https://cdn1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'DFW',
            'tenantId': 'MossoCloudFS_abc'},
            {u'publicURL': 'https://cdn1.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'SYD',
            'tenantId': 'MossoCloudFS_abc'},
            {u'publicURL': 'https://cdn2.clouddrive.com/v1/MossoCloudFS_abc',
            'region': 'ORD',
            'tenantId': 'MossoCloudFS_abc'}],
        'name': 'cloudFilesCDN',
        'type': 'rax:object-cdn'},
        {u'endpoints': [{u'publicURL':
            'https://monitoring.api.rackspacecloud.com/v1.0/000000',
            'tenantId': '000000'}],
        'name': 'cloudMonitoring',
        'type': 'rax:monitor'}],
    u'token': {u'expires': '2222-02-22T22:22:22.000-02:00',
    'id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'tenant': {u'id': '000000', 'name': '000000'}},
    u'user': {u'id': '123456',
    'name': 'fakeuser',
    'RAX-AUTH:defaultRegion': 'DFW',
    'roles': [{u'description': 'User Admin Role.',
    'id': '3',
    'name': 'identity:user-admin'}],
    }}}



class FakeIdentityResponse(FakeResponse):
    status_code = 200
    response_type = "auth"
    responses = {"auth": fake_identity_response,
            "users": fake_identity_user_response,
            "tenant": fake_identity_tenant_response,
            "tenants": fake_identity_tenants_response,
            "tokens": fake_identity_tokens_response,
            "endpoints": fake_identity_endpoints_response,
            }

    @property
    def content(self):
        return self.responses.get(self.response_type)

    def json(self):
        return self.content

    def read(self):
        return json.dumps(self.content)


def get_png_content():
    _module_pth = os.path.dirname(pyrax.__file__)
    _img_path = os.path.join(_module_pth, "..", "tests", "unit",
            "python-logo.png")
    png_content = None
    with open(_img_path, "rb") as pfile:
        png_content = pfile.read()
    return png_content
