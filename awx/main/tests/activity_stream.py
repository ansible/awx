# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Python
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseTest

class ActivityStreamTest(BaseTest):

    def collection(self):
        return reverse('api:activity_stream_list')

    def item(self, item_id):
        return reverse('api:activity_stream_detail', args=(item_id,))

    def setUp(self):
        super(ActivityStreamTest, self).setUp()
        self.setup_instances()
        self.create_test_license_file()
        # TODO: Test non-enterprise license
        self.setup_users()
        self.org_created = self.post(reverse('api:organization_list'), dict(name='test org', description='test descr'), expect=201, auth=self.get_super_credentials())

    def test_get_activity_stream_list(self):
        url = self.collection()

        with self.current_user(self.super_django_user):
            self.options(url, expect=200)
            self.head(url, expect=200)
            response = self.get(url, expect=200)
            self.check_pagination_and_size(response, 1, previous=None, next=None)

    def test_basic_fields(self):
        item_id = ActivityStream.objects.order_by('pk')[0].pk
        org_item = self.item(item_id)

        with self.current_user(self.super_django_user):
            response = self.get(org_item, expect=200)

            self.assertTrue("related" in response)
            self.assertTrue("organization" in response['related'])
            self.assertTrue("summary_fields" in response)
            self.assertTrue("organization" in response['summary_fields'])
            self.assertTrue(response['summary_fields']['organization'][0]['name'] == self.org_created['name'])

    def test_changeby_user(self):
        item_id = ActivityStream.objects.order_by('pk')[0].pk
        org_item = self.item(item_id)

        with self.current_user(self.super_django_user):
            response = self.get(org_item, expect=200)
            self.assertEqual(response['summary_fields']['actor']['username'], self.super_django_user.username)
