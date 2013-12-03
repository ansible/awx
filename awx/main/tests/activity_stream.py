# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import contextlib
import datetime
import json
import os
import shutil
import tempfile


from django.contrib.auth.models import User
import django.test
from django.test.client import Client
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTest

class ActivityStreamTest(BaseTest):

    def collection(self):
        return reverse('api:activity_stream_list')

    def item(self, item_id):
        return reverse('api:activity_stream_detail', args=(item_id,))

    def setUp(self):
        super(ActivityStreamTest, self).setUp()
        self.setup_users()
        self.org_created = self.post(reverse('api:organization_list'), dict(name='test org', description='test descr'), expect=201, auth=self.get_super_credentials())

    # def test_get_activity_stream_list(self):
    #      url = self.collection()

    #      with self.current_user(self.super_django_user):
    #          self.options(url, expect=200)
    #          self.head(url, expect=200)
    #          response = self.get(url, expect=200)
    #          self.check_pagination_and_size(response, 1, previous=None, next=None)

    def test_basic_fields(self):
        org_item = self.item(1)

        with self.current_user(self.super_django_user):
            response = self.get(org_item, expect=200)
            self.assertEqual(response['object1_id'], self.org_created['id'])
            self.assertEqual(response['object1_type'], "awx.main.models.organization.Organization")
            self.assertEqual(response['object2_id'], None)
            self.assertEqual(response['object2_type'], None)

            self.assertTrue("related" in response)
            self.assertTrue("object1" in response['related'])
            self.assertTrue("summary_fields" in response)
            self.assertTrue("object1" in response['summary_fields'])
            self.assertEquals(response['summary_fields']['object1']['base'], "organization")

    def test_changeby_user(self):
        org_item = self.item(1)

        with self.current_user(self.super_django_user):
            response = self.get(org_item, expect=200)
            self.assertEqual(response['summary_fields']['user']['username'], self.super_django_user.username)
