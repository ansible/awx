# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import datetime
import json

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from django.core.urlresolvers import reverse
from awx.main.models import Host, Inventory, Organization
from awx.main.tests.base import BaseTest
from awx.main.licenses import *

class LicenseTests(BaseTest):

    def setUp(self):
        super(LicenseTests, self).setUp()
        self.setup_users()
        u = self.super_django_user
        org = Organization.objects.create(name='o1', created_by=u)
        inventory = Inventory.objects.create(name='hi', organization=org, created_by=u)
        host = Host.objects.create(name='a1', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a2', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a3', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a4', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a5', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a6', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a7', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a8', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a9', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a10', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a11', inventory=inventory, created_by=u)
        host = Host.objects.create(name='a12', inventory=inventory, created_by=u)

    def test_license_writer(self):

        writer = LicenseWriter( 
           company_name='acmecorp',
           contact_name='Michael DeHaan',
           contact_email='michael@ansibleworks.com',
           license_date=25000, # seconds since epoch
           instance_count=500
        )

        data = writer.get_data()

        assert data['instance_count'] == 500
        assert data['contact_name'] == 'Michael DeHaan'
        assert data['contact_email'] == 'michael@ansibleworks.com'
        assert data['license_date'] == 25000 
        assert data['license_key'] == "11bae31f31c6a6cdcb483a278cdbe98bd8ac5761acd7163a50090b0f098b3a13"

        strdata = writer.get_string()
        strdata_loaded = json.loads(strdata)
        assert strdata_loaded == data

        reader = LicenseReader()
        
        vdata = reader.from_string(strdata)

        assert vdata['available_instances'] == 500
        assert vdata['current_instances'] == 12
        assert vdata['free_instances'] == 488
        assert vdata['date_warning'] == True
        assert vdata['date_expired'] == True
        assert vdata['license_date'] == 25000
        assert vdata['time_remaining'] < 0
        assert vdata['valid_key'] == True
        assert vdata['compliant'] == False


