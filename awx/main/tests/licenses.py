# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import json
import os
import tempfile

from awx.main.models import Host, Inventory, Organization
from awx.main.tests.base import BaseTest
import awx.main.task_engine
from awx.main.task_engine import * # noqa

class LicenseTests(BaseTest):

    def setUp(self):
        self.start_redis()
        self.setup_instances()
        super(LicenseTests, self).setUp()
        self.setup_users()
        u = self.super_django_user
        org = Organization.objects.create(name='o1', created_by=u)
        org.admins.add(self.normal_django_user)
        self.inventory = Inventory.objects.create(name='hi', organization=org, created_by=u)
        Host.objects.create(name='a1', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a2', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a3', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a4', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a5', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a6', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a7', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a8', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a9', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a10', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a11', inventory=self.inventory, created_by=u)
        Host.objects.create(name='a12', inventory=self.inventory, created_by=u)
        self._temp_task_file = awx.main.task_engine.TEMPORARY_TASK_FILE
        self._temp_task_fetch_ami = awx.main.task_engine.TemporaryTaskEngine.fetch_ami
        self._temp_task_fetch_instance = awx.main.task_engine.TemporaryTaskEngine.fetch_instance

    def tearDown(self):
        awx.main.task_engine.TEMPORARY_TASK_FILE = self._temp_task_file
        awx.main.task_engine.TemporaryTaskEngine.fetch_ami = self._temp_task_fetch_ami
        awx.main.task_engine.TemporaryTaskEngine.fetch_instance = self._temp_task_fetch_instance
        super(LicenseTests, self).tearDown()
        self.stop_redis()

    def test_license_writer(self):

        writer = TaskEngager( 
            company_name='acmecorp',
            contact_name='Michael DeHaan',
            contact_email='michael@ansibleworks.com',
            license_date=25000, # seconds since epoch
            instance_count=500)

        data = writer.get_data()

        assert data['instance_count'] == 500
        assert data['contact_name'] == 'Michael DeHaan'
        assert data['contact_email'] == 'michael@ansibleworks.com'
        assert data['license_date'] == 25000 
        assert data['license_key'] == "11bae31f31c6a6cdcb483a278cdbe98bd8ac5761acd7163a50090b0f098b3a13"

        strdata = writer.get_string()
        strdata_loaded = json.loads(strdata)
        assert strdata_loaded == data

        reader = TaskSerializer()

        vdata = reader.from_string(strdata)

        assert vdata['available_instances'] == 500
        assert vdata['current_instances'] == 12
        assert vdata['free_instances'] == 488
        assert vdata['date_warning'] is True
        assert vdata['date_expired'] is True
        assert vdata['license_date'] == 25000
        assert vdata['time_remaining'] < 0
        assert vdata['valid_key'] is True
        assert vdata['compliant'] is False
        assert vdata['subscription_name']

    def test_expired_licenses(self):
        reader = TaskSerializer()
        writer = TaskEngager(
            company_name='Tower',
            contact_name='Tower Admin',
            contact_email='tower@ansible.com',
            license_date=int(time.time() - 3600),
            instance_count=100,
            trial=True)
        strdata = writer.get_string()
        vdata = reader.from_string(strdata)

        assert vdata['compliant'] is False
        assert vdata['grace_period_remaining'] < 0

        writer = TaskEngager(
            company_name='Tower',
            contact_name='Tower Admin',
            contact_email='tower@ansible.com',
            license_date=int(time.time() - 2592001),
            instance_count=100,
            trial=False)
        strdata = writer.get_string()
        vdata = reader.from_string(strdata)

        assert vdata['compliant'] is False
        assert vdata['grace_period_remaining'] < 0

        writer = TaskEngager(
            company_name='Tower',
            contact_name='Tower Admin',
            contact_email='tower@ansible.com',
            license_date=int(time.time() - 3600),
            instance_count=100,
            trial=False)
        strdata = writer.get_string()
        vdata = reader.from_string(strdata)

        assert vdata['compliant'] is False
        assert vdata['grace_period_remaining'] > 0

    def test_aws_license(self):
        os.environ['AWX_LICENSE_FILE'] = 'non-existent-license-file.json'
        h, path = tempfile.mkstemp()
        self._temp_paths.append(path)
        with os.fdopen(h, 'w') as f:
            json.dump({'instance_count': 100}, f)
        awx.main.task_engine.TEMPORARY_TASK_FILE = path

        def fetch_ami(_self):
            _self.attributes['ami-id'] = 'ami-00000000'
            return True

        def fetch_instance(_self):
            _self.attributes['instance-id'] = 'i-00000000'
            return True

        awx.main.task_engine.TemporaryTaskEngine.fetch_ami = fetch_ami
        awx.main.task_engine.TemporaryTaskEngine.fetch_instance = fetch_instance
        reader = TaskSerializer()
        license = reader.from_file()
        self.assertTrue(license['is_aws'])
        self.assertTrue(license['time_remaining'])
        self.assertTrue(license['free_instances'] > 0)
        self.assertTrue(license['grace_period_remaining'] > 0)
