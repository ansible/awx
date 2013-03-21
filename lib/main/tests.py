# FIXME: do not use ResourceTestCase

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""


import datetime
import json

from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client

from lib.main.models import User, Organization, Project 

class BaseTest(django.test.TestCase):

    def make_user(self, username, password, super_user=False):
        django_user = None
        if super_user:
            django_user = DjangoUser.objects.create_superuser(username, "%s@example.com", password)
        else:
            django_user = DjangoUser.objects.create_user(username, "%s@example.com", password)
        acom_user   = User.objects.create(name=username, auth_user=django_user)
        return (django_user, acom_user)

    def make_organizations(self, count=1):
        results = []
        for x in range(0, count):
            results.append(Organization.objects.create(name="org%s" % x, description="org%s" % x))
        return results

    def check_pagination_and_size(self, data, desired_count, previous=None, next=None):
        self.assertEquals(data['count'], desired_count)
        self.assertEquals(data['previous'], previous)
        self.assertEquals(data['next'], next)

    def setup_users(self):
        # Create a user.
        self.super_username  = 'admin'
        self.super_password  = 'admin'
        self.normal_username = 'normal'
        self.normal_password = 'normal'
        self.other_username  = 'other'
        self.other_password  = 'other'

        (self.super_django_user,  self.super_acom_user)  = self.make_user(self.super_username,  self.super_password, super_user=True)
        (self.normal_django_user, self.normal_acom_user) = self.make_user(self.normal_username, self.normal_password, super_user=False)
        (self.other_django_user,  self.other_acom_user)  = self.make_user(self.other_username,  self.other_password, super_user=False)

    def get_super_credentials(self):
        return (self.super_username, self.super_password)

    def get_normal_credentials(self):
        return (self.normal_username, self.normal_password)

    def get_other_credentials(self):
        return (self.other_username, self.other_password)

    def get_invalid_credentials(self):
        return ('random', 'combination')
        
    def _generic_rest(self, url, data=None, expect=204, auth=None, method=None):
        assert method is not None
        if method != 'get':
            assert data is not None
        client = Client()
        if auth:
           client.login(username=auth[0], password=auth[1])
        method = getattr(client,method)
        response = None
        if data is not None:
            response = method(url, data=json.dumps(data))
        else:
            response = method(url)
        if response.status_code == 500 and expect != 500:
            assert False, "Failed: %s" % response.content
        if expect is not None:
            assert response.status_code == expect, "expected status %s, got %s for url=%s as auth=%s" % (expect, response.status_code, url, auth)
        data = json.loads(response.content)
        return data
 
    def get(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='get')

    def post(self, url, expect=204, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='post')

    def put(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='put')

    def delete(self, url, expect=201, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='delete')

class OrganizationsTest(BaseTest):

    def collection(self):
        return '/api/v1/organizations/'

    def setUp(self):
        self.setup_users()
        self.organizations = self.make_organizations(10)
        self.a_detail_url  = "%s%s" % (self.collection(), self.organizations[0].pk)
        self.b_detail_url  = "%s%s" % (self.collection(), self.organizations[1].pk)
        self.c_detail_url  = "%s%s" % (self.collection(), self.organizations[2].pk)

        # configuration:
        #   admin_user is an admin and regular user in all organizations
        #   other_user is all organizations
        #   normal_user is a user in organization 0, and an admin of organization 1

        for x in self.organizations:
            # NOTE: superuser does not have to be explicitly added to admin group
            # x.admins.add(self.super_acom_user)
            x.users.add(self.super_acom_user)
            x.users.add(self.other_acom_user)
 
        self.organizations[0].users.add(self.normal_acom_user)
        self.organizations[0].users.add(self.normal_acom_user)
        self.organizations[1].admins.add(self.normal_acom_user)

    def test_get_list_unauthorzied(self):

        # no credentials == 401
        self.get(self.collection(), expect=401)

        # wrong credentials == 401
        self.get(self.collection(), expect=401, auth=self.get_invalid_credentials())

        # superuser credentials == 200, full list
        data = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        self.check_pagination_and_size(data, 10, previous=None, next=None)
        [self.assertTrue(key in data['results'][0]) for key in ['name', 'description', 'url' ]]

        # normal credentials == 200, get only organizations that I am actually added to (there are 2)
        data = self.get(self.collection(), expect=200, auth=self.get_normal_credentials())
        self.check_pagination_and_size(data, 2, previous=None, next=None)

        # no admin rights? get empty list
        #resp = self.api_client.get(self.collection(), format='json', authentication=self.get_other_credentials())
        #self.assertValidJSONResponse(resp)
        #self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_get_item(self):
        return
      
        # no credentials == 401
        #self.assertHttpUnauthorized(self.api_client.get(self.a_detail_url, format='json'))
        
        # wrong crendentials == 401
        #self.assertHttpUnauthorized(self.api_client.get(self.c_detail_url, format='json', authentication=self.get_invalid_credentials())
 
        # superuser credentials == 
        pass


    def test_get_item_subobjects_projects(self):
        pass

    def test_get_item_subobjects_users(self):
        pass

    def test_get_item_subobjects_admins(self):
        pass

    def test_post_item(self):
        pass

    def test_post_item_subobjects_projects(self):
        pass

    def test_post_item_subobjects_users(self):
        pass

    def test_post_item_subobjects_admins(self):
        pass

    def test_put_item(self):
        pass

    def test_put_item_subobjects_projects(self):
        pass

    def test_put_item_subobjects_users(self):
        pass

    def test_put_item_subobjects_admins(self):
        pass

    def test_delete_item(self):
        pass

    def test_delete_item_subobjects_projects(self):
        pass

    def test_delete_item_subobjects_users(self):
        pass

    def test_delete_item_subobjects_admins(self):
        pass

#   def test_get_list_xml(self):
#       self.assertValidXMLResponse(self.api_client.get(self.collection(), format='xml', authentication=self.get_normal_credentials()))
#
#   def test_get_detail_unauthenticated(self):
#
#    def test_get_detail_json(self):
#        resp = self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials())
#        self.assertValidJSONResponse(resp)
#
#        # We use ``assertKeys`` here to just verify the keys, not all the data.
#        self.assertKeys(self.deserialize(resp), ['created', 'slug', 'title', 'user'])
#        self.assertEqual(self.deserialize(resp)['name'], 'First post')
#
#    def test_get_detail_xml(self):
#        self.assertValidXMLResponse(self.api_client.get(self.detail_url, format='xml', authentication=self.get_credentials()))
#
#   def test_post_list_unauthenticated(self):
#       self.assertHttpUnauthorized(self.api_client.post('/api/v1/entries/', format='json', data=self.post_data))
#
#    def test_post_list(self):
#        # Check how many are there first.
#        self.assertEqual(Entry.objects.count(), 5)
#        self.assertHttpCreated(self.api_client.post('/api/v1/entries/', format='json', data=self.post_data, authentication=self.get_credentials()))
#        # Verify a new one has been added.
#        self.assertEqual(Entry.objects.count(), 6)
#
#    def test_put_detail_unauthenticated(self):
#        self.assertHttpUnauthorized(self.api_client.put(self.detail_url, format='json', data={}))
#
#    def test_put_detail(self):
#        # Grab the current data & modify it slightly.
#        original_data = self.deserialize(self.api_client.get(self.detail_url, format='json', authentication=self.get_credentials()))
#        new_data = original_data.copy()
#        new_data['title'] = 'Updated: First Post'
#        new_data['created'] = '2012-05-01T20:06:12'
#
#        self.assertEqual(Entry.objects.count(), 5)
#        self.assertHttpAccepted(self.api_client.put(self.detail_url, format='json', data=new_data, authentication=self.get_credentials()))
#        # Make sure the count hasn't changed & we did an update.
#        self.assertEqual(Entry.objects.count(), 5)
#        # Check for updated data.
#        self.assertEqual(Entry.objects.get(pk=25).title, 'Updated: First Post')
#        self.assertEqual(Entry.objects.get(pk=25).slug, 'first-post')
#        self.assertEqual(Entry.objects.get(pk=25).created, datetime.datetime(2012, 3, 1, 13, 6, 12))
#
#    def test_delete_detail_unauthenticated(self):
#        self.assertHttpUnauthorized(self.api_client.delete(self.detail_url, format='json'))
#
#    def test_delete_detail(self):
#        self.assertEqual(Entry.objects.count(), 5)
#        self.assertHttpAccepted(self.api_client.delete(self.detail_url, format='json', authentication=self.get_credentials()))
#        self.assertEqual(Entry.objects.count(), 4)
