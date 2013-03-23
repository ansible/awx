"""
Test code for ansible commander.

(C) 2013 AnsibleWorks <michael@ansibleworks.com>
"""


import datetime
import json

from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from lib.main.models import *


class BaseTest(django.test.TestCase):

    def make_user(self, username, password, super_user=False):
        django_user = None
        if super_user:
            django_user = DjangoUser.objects.create_superuser(username, "%s@example.com", password)
        else:
            django_user = DjangoUser.objects.create_user(username, "%s@example.com", password)
        return django_user

    def make_organizations(self, created_by, count=1):
        results = []
        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            results.append(Organization.objects.create(
                name="org%s-%s" % (x, self.object_ctr), description="org%s" % x, created_by=created_by
            ))
        return results

    def make_projects(self, created_by, count=1):
        results = []
        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            results.append(Project.objects.create(
                name="proj%s-%s" % (x, self.object_ctr), description="proj%s" % x, scm_type='git', 
                default_playbook='foo.yml', local_repository='/checkout', created_by=created_by
            ))
        return results

    def check_pagination_and_size(self, data, desired_count, previous=None, next=None):
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

        self.super_django_user  = self.make_user(self.super_username,  self.super_password, super_user=True)
        self.normal_django_user = self.make_user(self.normal_username, self.normal_password, super_user=False)
        self.other_django_user  = self.make_user(self.other_username,  self.other_password, super_user=False)

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
        method = method.lower()
        if method not in [ 'get', 'delete' ]:
            assert data is not None
        client = Client()
        if auth:
           client.login(username=auth[0], password=auth[1])
        method = getattr(client,method)
        response = None
        if data is not None:
            response = method(url, json.dumps(data), 'application/json')
        else:
            response = method(url)

        if response.status_code == 500 and expect != 500:
            assert False, "Failed: %s" % response.content
        if expect is not None:
            assert response.status_code == expect, "expected status %s, got %s for url=%s as auth=%s: %s" % (expect, response.status_code, url, auth, response.content)
        if response.status_code not in [ 202, 204, 400, 405, 409 ]:
            # no JSON responses in these at least for now, 400/409 should probably return some (FIXME)
            return json.loads(response.content)
        else:
            return None
 
    def get(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='get')

    def post(self, url, data, expect=204, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='post')

    def put(self, url, data, expect=200, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='put')

    def delete(self, url, expect=201, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='delete')

    def get_urls(self, collection_url, auth=None):
        # TODO: this test helper function doesn't support pagination
        data = self.get(collection_url, expect=200, auth=auth)
        return [item['url'] for item in data['results']]
    

class OrganizationsTest(BaseTest):

    def collection(self):
        return '/api/v1/organizations/'

    def setUp(self):
        self.object_ctr = 0
        self.setup_users()
 
        self.organizations = self.make_organizations(self.super_django_user, 10)
        self.projects      = self.make_projects(self.normal_django_user, 10)

        # add projects to organizations in a more or less arbitrary way
        for project in self.projects[0:2]:
            self.organizations[0].projects.add(project)
        for project in self.projects[3:8]:
            self.organizations[1].projects.add(project)
        for project in self.projects[9:10]: 
            self.organizations[2].projects.add(project)
        self.organizations[0].projects.add(self.projects[-1])
        self.organizations[9].projects.add(self.projects[-2])

        # get the URL for various organization records
        self.a_detail_url  = "%s%s" % (self.collection(), self.organizations[0].pk)
        self.b_detail_url  = "%s%s" % (self.collection(), self.organizations[1].pk)
        self.c_detail_url  = "%s%s" % (self.collection(), self.organizations[2].pk)

        # configuration:
        #   admin_user is an admin and regular user in all organizations
        #   other_user is all organizations
        #   normal_user is a user in organization 0, and an admin of organization 1

        for x in self.organizations:
            # NOTE: superuser does not have to be explicitly added to admin group
            # x.admins.add(self.super_django_user)
            x.users.add(self.super_django_user)
 
        self.organizations[0].users.add(self.normal_django_user)
        self.organizations[1].admins.add(self.normal_django_user)

    def test_get_list(self):

        # no credentials == 401
        self.get(self.collection(), expect=401)

        # wrong credentials == 401
        self.get(self.collection(), expect=401, auth=self.get_invalid_credentials())

        # superuser credentials == 200, full list
        data = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        self.check_pagination_and_size(data, 10, previous=None, next=None)
        [self.assertTrue(key in data['results'][0]) for key in ['name', 'description', 'url', 'creation_date', 'id' ]]

        # check that the related URL functionality works
        related = data['results'][0]['related']
        for x in [ 'audit_trail', 'projects', 'users', 'admins', 'tags' ]:
            self.assertTrue(x in related and related[x].endswith("/%s/" % x), "looking for %s in related" % x)

        # normal credentials == 200, get only organizations that I am actually added to (there are 2)
        data = self.get(self.collection(), expect=200, auth=self.get_normal_credentials())
        self.check_pagination_and_size(data, 2, previous=None, next=None)

        # no admin rights? get empty list
        data = self.get(self.collection(), expect=200, auth=self.get_other_credentials())
        self.check_pagination_and_size(data, 0, previous=None, next=None)

    def test_get_item(self):

        # first get all the URLs
        data = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        urls = [item['url'] for item in data['results']]

        # make sure super user can fetch records
        data = self.get(urls[0], expect=200, auth=self.get_super_credentials())
        [self.assertTrue(key in data) for key in ['name', 'description', 'url' ]]

        # make sure invalid user cannot
        data = self.get(urls[0], expect=401, auth=self.get_invalid_credentials())

        # normal user should be able to get org 0 and org 1 but not org 9 (as he's not a user or admin of it)
        data = self.get(urls[0], expect=200, auth=self.get_normal_credentials())
        data = self.get(urls[1], expect=200, auth=self.get_normal_credentials())
        data = self.get(urls[9], expect=403, auth=self.get_normal_credentials())

        # other user isn't a user or admin of anything, and similarly can't get in
        data = self.get(urls[0], expect=403, auth=self.get_other_credentials())

    def test_get_item_subobjects_projects(self):

        # first get all the orgs
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        
        # find projects attached to the first org
        projects0_url = orgs['results'][0]['related']['projects']
        projects1_url = orgs['results'][1]['related']['projects']
        projects9_url = orgs['results'][9]['related']['projects']
       
        self.get(projects0_url, expect=401, auth=None)
        self.get(projects0_url, expect=401, auth=self.get_invalid_credentials())
   
        # normal user is just a member of the first org, but can't see any projects under the org
        projects0a = self.get(projects0_url, expect=403, auth=self.get_normal_credentials())

        # however in the second org, he's an admin and should see all of them
        projects1a = self.get(projects1_url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(projects1a['count'], 5)

        # but the non-admin cannot access the list of projects in the org.  He should use /projects/ instead!
        projects1b = self.get(projects1_url, expect=403, auth=self.get_other_credentials())
 
        # superuser should be able to read anything
        projects9a = self.get(projects9_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(projects9a['count'], 1)


    def test_get_item_subobjects_users(self):

        # see if we can list the users added to the organization
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        org1_users_url = orgs['results'][1]['related']['users']
        org1_users = self.get(org1_users_url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(org1_users['count'], 1)
        org1_users = self.get(org1_users_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(org1_users['count'], 1)

    def test_get_item_subobjects_admins(self):

        # see if we can list the users added to the organization
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        org1_users_url = orgs['results'][1]['related']['admins']
        org1_users = self.get(org1_users_url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(org1_users['count'], 1)
        org1_users = self.get(org1_users_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(org1_users['count'], 1)

    def test_get_item_subobjects_tags(self):

        # put some tags on the org
        org1 = Organization.objects.get(pk=2)
        tag1 = Tag.objects.create(name='atag')
        tag2 = Tag.objects.create(name='btag')
        org1.tags.add(tag1)
        org1.tags.add(tag2)

        # see if we can list the users added to the organization
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        org1_tags_url = orgs['results'][1]['related']['tags']
        org1_tags = self.get(org1_tags_url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(org1_tags['count'], 2)
        org1_tags = self.get(org1_tags_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(org1_tags['count'], 2)
        org1_tags = self.get(org1_tags_url, expect=403, auth=self.get_other_credentials())

    def test_get_item_subobjects_audit_trail(self):
        # FIXME
        pass

    def test_post_item(self):

        new_org = dict(name='magic test org', description='8675309')
        
        # need to be a valid user
        self.post(self.collection(), new_org, expect=401, auth=None)
        self.post(self.collection(), new_org, expect=401, auth=self.get_invalid_credentials())
        
        # only super users can create organizations
        self.post(self.collection(), new_org, expect=403, auth=self.get_normal_credentials())
        self.post(self.collection(), new_org, expect=403, auth=self.get_other_credentials())
        data1 = self.post(self.collection(), new_org, expect=201, auth=self.get_super_credentials())

        # duplicate post results in 400
        data2 = self.post(self.collection(), new_org, expect=400, auth=self.get_super_credentials())

        # look at what we got back from the post, make sure we added an org
        self.assertTrue(data1['url'].endswith("/11/"))

    def test_post_item_subobjects_projects(self):
        
        # first get all the orgs
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        
        # find projects attached to the first org
        projects0_url = orgs['results'][0]['related']['projects']
        projects1_url = orgs['results'][1]['related']['projects']
        projects2_url = orgs['results'][2]['related']['projects']
        
        # get all the projects on the first org
        projects0 = self.get(projects0_url, expect=200, auth=self.get_super_credentials())
        a_project = projects0['results'][-1]

        # attempt to add the project to the 7th org and see what happens
        self.post(projects1_url, a_project, expect=204, auth=self.get_super_credentials())
        projects1 = self.get(projects0_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(projects1['count'], 3)

        # make sure we can't add the project again (should generate a conflict error)
        self.post(projects1_url, a_project, expect=409, auth=self.get_super_credentials())
        projects1 = self.get(projects1_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(projects1['count'], 6)       

        # make sure adding a project that does not exist, or a missing pk field, results in a 400
        self.post(projects1_url, dict(id=99999), expect=400, auth=self.get_super_credentials())
        self.post(projects1_url, dict(asdf=1234), expect=400, auth=self.get_super_credentials())

        # test that by posting a pk + disassociate: True we can remove a relationship
        a_project['disassociate'] = True
        self.post(projects1_url, a_project, expect=204, auth=self.get_super_credentials())
        projects1 = self.get(projects1_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(projects1['count'], 5)
       
        a_project = projects1['results'][-1]
        a_project['disassociate'] = 1
        projects1 = self.get(projects1_url, expect=200, auth=self.get_super_credentials())
        self.post(projects1_url, a_project, expect=204, auth=self.get_normal_credentials())
        projects1 = self.get(projects1_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(projects1['count'], 4)

        new_project_a = self.make_projects(self.normal_django_user, 1)[0]
        new_project_b = self.make_projects(self.other_django_user, 1)[0]

        # admin of org can add projects that he can read
        self.post(projects1_url, dict(id=new_project_a.pk), expect=204, auth=self.get_normal_credentials())
        # but not those he cannot
        self.post(projects1_url, dict(id=new_project_b.pk), expect=403, auth=self.get_normal_credentials())

        # and can't post a project he can read to an org he cannot
        # self.post(projects2_url, dict(id=new_project_a.pk), expect=403, auth=self.get_normal_credentials())

        # and can't do post a project he can read to an organization he cannot
        self.post(projects2_url, dict(id=new_project_a.pk), expect=403, auth=self.get_normal_credentials())
          

    def test_post_item_subobjects_users(self):

        url = '/api/v1/organizations/2/users/'
        users = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(users['count'], 1)
        self.post(url, dict(id=2), expect=204, auth=self.get_normal_credentials())
        users = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(users['count'], 2)
        self.post(url, dict(id=2, disassociate=True), expect=204, auth=self.get_normal_credentials())
        users = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(users['count'], 1)

    def test_post_item_subobjects_admins(self):

        url = '/api/v1/organizations/2/admins/'
        admins = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(admins['count'], 1)
        self.post(url, dict(id=1), expect=204, auth=self.get_normal_credentials())
        admins = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(admins['count'], 2)
        self.post(url, dict(id=1, disassociate=1), expect=204, auth=self.get_normal_credentials())
        admins = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(admins['count'], 1)

    def test_post_item_subobjects_tags(self):

        tag = Tag.objects.create(name='blippy')
        url = '/api/v1/organizations/2/tags/'
        tags = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(tags['count'], 0)
        self.post(url, dict(id=tag.pk), expect=204, auth=self.get_normal_credentials())
        tags = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(tags['count'], 1)
        self.assertEqual(tags['results'][0]['id'], tag.pk)
        self.post(url, dict(id=tag.pk, disassociate=1), expect=204, auth=self.get_normal_credentials())
        tags = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(tags['count'], 0)

    def test_post_item_subobjects_audit_trail(self):
        # audit trails are system things, and no user can post to them.
        url = '/api/v1/organizations/2/audit_trail/'
        self.post(url, dict(id=1), expect=405, auth=self.get_super_credentials())

    def test_put_item(self):

        # first get some urls and data to put back to them
        urls = self.get_urls(self.collection(), auth=self.get_super_credentials())
        data0 = self.get(urls[0], expect=200, auth=self.get_super_credentials())
        data1 = self.get(urls[1], expect=200, auth=self.get_super_credentials())

        # test that an unauthenticated user cannot do a put
        new_data1 = data1.copy()
        new_data1['description'] = 'updated description'
        self.put(urls[0], new_data1, expect=401, auth=None)
        self.put(urls[0], new_data1, expect=401, auth=self.get_invalid_credentials())

        # user normal is an admin of org 0 and a member of org 1 so should be able to put only org 1        
        self.put(urls[0], new_data1, expect=403, auth=self.get_normal_credentials())
        put_result = self.put(urls[1], new_data1, expect=200, auth=self.get_normal_credentials())

        # get back org 1 and see if it changed
        get_result = self.get(urls[1], expect=200, auth=self.get_normal_credentials())
        self.assertEquals(get_result['description'], 'updated description')

        # super user can also put even though they aren't added to the org users or admins list
        self.put(urls[1], new_data1, expect=200, auth=self.get_super_credentials())

        # make sure posting to this URL is not supported
        self.post(urls[1], new_data1, expect=405, auth=self.get_super_credentials())

    def test_put_item_subobjects_projects(self):

        # any attempt to put a subobject should be a 405, edit the actual resource or POST with 'disassociate' to delete
        # this is against a collection URL anyway, so we really need not repeat this test for other object types
        # as a PUT against a collection doesn't make much sense.  
 
        orgs = self.get(self.collection(), expect=200, auth=self.get_super_credentials())
        projects0_url = orgs['results'][0]['related']['projects']
        sub_projects = self.get(projects0_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(sub_projects['count'], 3)
        first_sub_project = sub_projects['results'][0]
        self.put(projects0_url, first_sub_project, expect=405, auth=self.get_super_credentials())

    def test_delete_item(self):

        # first get some urls
        urls = self.get_urls(self.collection(), auth=self.get_super_credentials())
        urldata1 = self.get(urls[1], auth=self.get_super_credentials())
        
        # check authentication -- admins of the org and superusers can delete objects only
        self.delete(urls[0], expect=401, auth=None)
        self.delete(urls[0], expect=401, auth=self.get_invalid_credentials())
        self.delete(urls[8], expect=403, auth=self.get_normal_credentials())
        self.delete(urls[1], expect=204, auth=self.get_normal_credentials())
        self.delete(urls[0], expect=204, auth=self.get_super_credentials())
      
        # check that when we have deleted an object it comes back 404 via GET
        # but that it's still in the database as inactive
        self.get(urls[1], expect=404, auth=self.get_normal_credentials())
        org1 = Organization.objects.get(pk=urldata1['id'])
        self.assertEquals(org1.active, False)

        # also check that DELETE on the collection doesn't work
        self.delete(self.collection(), expect=405, auth=self.get_super_credentials())


