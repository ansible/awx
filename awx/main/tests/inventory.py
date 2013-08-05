# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import datetime
import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from awx.main.models import *
from awx.main.tests.base import BaseTest

class InventoryTest(BaseTest):

    def setUp(self):

        super(InventoryTest, self).setUp()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 3)
        self.organizations[0].admins.add(self.normal_django_user)
        self.organizations[0].users.add(self.other_django_user)
        self.organizations[0].users.add(self.normal_django_user)

        self.inventory_a = Inventory.objects.create(name='inventory-a', description='foo', organization=self.organizations[0])
        self.inventory_b = Inventory.objects.create(name='inventory-b', description='bar', organization=self.organizations[1])
 
        # the normal user is an org admin of org 0

        # create a permission here on the 'other' user so they have edit access on the org
        # we may add another permission type later.
        self.perm_read = Permission.objects.create(
             inventory       = self.inventory_b,
             user            = self.other_django_user,
             permission_type = 'read'
        )

    def test_get_inventory_list(self):
        url = reverse('main:inventory_list')
        qs = Inventory.objects.filter(active=True).distinct()

        # Check list view with invalid authentication.
        self.check_invalid_auth(url)

        # a super user can list all inventories
        self.check_get_list(url, self.super_django_user, qs)

        # an org admin can list inventories but is filtered to what he adminsters
        normal_qs = qs.filter(organization__admins__in=[self.normal_django_user])
        self.check_get_list(url, self.normal_django_user, normal_qs)

        # a user who is on a team who has a read permissions on an inventory can see filtered inventories
        other_qs = qs.filter(permissions__user__in=[self.other_django_user])
        self.check_get_list(url, self.other_django_user, other_qs)

        # a regular user not part of anything cannot see any inventories
        nobody_qs = qs.none()
        self.check_get_list(url, self.nobody_django_user, nobody_qs)

    def test_post_inventory_list(self):
        url = reverse('main:inventory_list')

        # Check post to list view with invalid authentication.
        new_inv_0 = dict(name='inventory-c', description='baz', organization=self.organizations[0].pk)
        self.check_invalid_auth(url, new_inv_0, methods=('post',))

        # a super user can create inventory
        new_inv_1 = dict(name='inventory-c', description='baz', organization=self.organizations[0].pk)
        new_id = max(Inventory.objects.values_list('pk', flat=True)) + 1
        with self.current_user(self.super_django_user):
            data = self.post(url, data=new_inv_1, expect=201)
            self.assertEquals(data['id'], new_id)

        # an org admin of any org can create inventory, if it is one of his organizations
        # the organization parameter is required!
        new_inv_incomplete = dict(name='inventory-d', description='baz')
        new_inv_not_my_org = dict(name='inventory-d', description='baz', organization=self.organizations[2].pk)
        new_inv_my_org = dict(name='inventory-d', description='baz', organization=self.organizations[0].pk)
        with self.current_user(self.normal_django_user):
            data = self.post(url, data=new_inv_incomplete, expect=400)
            data = self.post(url, data=new_inv_not_my_org, expect=403)
            data = self.post(url, data=new_inv_my_org, expect=201)

        # a regular user cannot create inventory
        new_inv_denied = dict(name='inventory-e', description='glorp', organization=self.organizations[0].pk)
        with self.current_user(self.other_django_user):
            data = self.post(url, data=new_inv_denied, expect=403)

    def test_get_inventory_detail(self):
        url_a = reverse('main:inventory_detail', args=(self.inventory_a.pk,))
        url_b = reverse('main:inventory_detail', args=(self.inventory_b.pk,))

        # Check detail view with invalid authentication.
        self.check_invalid_auth(url_a)
        self.check_invalid_auth(url_b)

        # a super user can get inventory records
        with self.current_user(self.super_django_user):
            data = self.get(url_a, expect=200)
            self.assertEquals(data['name'], 'inventory-a')

        # an org admin can get inventory records for his orgs only
        with self.current_user(self.normal_django_user):
            data = self.get(url_a, expect=200)
            self.assertEquals(data['name'], 'inventory-a')
            data = self.get(url_b, expect=403)

        # a user who is on a team who has read permissions on an inventory can see inventory records
        with self.current_user(self.other_django_user):
            data = self.get(url_a, expect=403)
            data = self.get(url_b, expect=200)
            self.assertEquals(data['name'], 'inventory-b')

        # a regular user cannot read any inventory records
        with self.current_user(self.nobody_django_user):
            data = self.get(url_a, expect=403)
            data = self.get(url_b, expect=403)

    def test_put_inventory_detail(self):
        url_a = reverse('main:inventory_detail', args=(self.inventory_a.pk,))
        url_b = reverse('main:inventory_detail', args=(self.inventory_b.pk,))
        
        # Check put to detail view with invalid authentication.
        self.check_invalid_auth(url_a, methods=('put',))
        self.check_invalid_auth(url_b, methods=('put',))
        
        # a super user can update inventory records
        with self.current_user(self.super_django_user):
            data = self.get(url_a, expect=200)
            data['name'] = 'inventory-a-update1'
            self.put(url_a, data, expect=200)
            data = self.get(url_b, expect=200)
            data['name'] = 'inventory-b-update1'
            self.put(url_b, data, expect=200)

        # an org admin can update inventory records for his orgs only.
        with self.current_user(self.normal_django_user):
            data = self.get(url_a, expect=200)
            data['name'] = 'inventory-a-update2'
            self.put(url_a, data, expect=200)
            self.put(url_b, data, expect=403)

        # a user who is on a team who has read permissions on an inventory can
        # see inventory records, but not update.
        with self.current_user(self.other_django_user):
            data = self.get(url_b, expect=200)
            data['name'] = 'inventory-b-update3'
            self.put(url_b, data, expect=403)

        # a regular user cannot update any inventory records
        with self.current_user(self.nobody_django_user):
            self.put(url_a, {}, expect=403)
            self.put(url_b, {}, expect=403)

        # a superuser can reassign an inventory to another organization.
        with self.current_user(self.super_django_user):
            data = self.get(url_b, expect=200)
            self.assertEqual(data['organization'], self.organizations[1].pk)
            data['organization'] = self.organizations[0].pk
            self.put(url_b, data, expect=200)

        # a normal user can't reassign an inventory to an organization where
        # he isn't an admin.
        with self.current_user(self.normal_django_user):
            data = self.get(url_a, expect=200)
            self.assertEqual(data['organization'], self.organizations[0].pk)
            data['organization'] = self.organizations[1].pk
            self.put(url_a, data, expect=403)

    def test_delete_inventory_detail(self):
        pass # FIXME

    def test_main_line(self):
       
        # some basic URLs... 
        inventories   = reverse('main:inventory_list')
        inventories_1 = reverse('main:inventory_detail', args=(self.inventory_a.pk,))
        inventories_2 = reverse('main:inventory_detail', args=(self.inventory_b.pk,))
        hosts         = reverse('main:host_list')
        groups        = reverse('main:group_list')


        # a super user can add hosts (but inventory ID is required)
        inv = Inventory.objects.create(
            name = 'test inventory',
            organization = self.organizations[0]
        )
        invalid      = dict(name='asdf0.example.com')
        new_host_a   = dict(name='asdf0.example.com', inventory=inv.pk)
        new_host_b   = dict(name='asdf1.example.com', inventory=inv.pk)
        new_host_c   = dict(name='asdf2.example.com', inventory=inv.pk)
        new_host_d   = dict(name='asdf3.example.com', inventory=inv.pk)
        new_host_e   = dict(name='asdf4.example.com', inventory=inv.pk)
        host_data0 = self.post(hosts, data=invalid, expect=400, auth=self.get_super_credentials())
        host_data0 = self.post(hosts, data=new_host_a, expect=201, auth=self.get_super_credentials())
 
        # an org admin can add hosts
        host_data1 = self.post(hosts, data=new_host_e, expect=201, auth=self.get_normal_credentials())

        # a normal user cannot add hosts
        host_data2 = self.post(hosts, data=new_host_b, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions (on any inventory) can create hosts
        edit_perm = Permission.objects.create(
             user            = self.other_django_user,
             inventory       = Inventory.objects.get(pk=inv.pk),
             permission_type = PERM_INVENTORY_WRITE
        )
        host_data3 = self.post(hosts, data=new_host_c, expect=201, auth=self.get_other_credentials())

        # hostnames must be unique inside an organization
        host_data4 = self.post(hosts, data=new_host_c, expect=400, auth=self.get_other_credentials())

        # Verify we can update host via PUT.
        host_url3 = host_data3['url']
        host_data3['variables'] = ''
        host_data3 = self.put(host_url3, data=host_data3, expect=200, auth=self.get_other_credentials())
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables, '')
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables_dict, {})
        
        # Should reject invalid data.
        host_data3['variables'] = 'foo: [bar'
        self.put(host_url3, data=host_data3, expect=400, auth=self.get_other_credentials())

        # Should accept valid JSON or YAML.
        host_data3['variables'] = 'bad: monkey'
        self.put(host_url3, data=host_data3, expect=200, auth=self.get_other_credentials())
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables, host_data3['variables'])
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables_dict, {'bad': 'monkey'})
        
        host_data3['variables'] = '{"angry": "penguin"}'
        self.put(host_url3, data=host_data3, expect=200, auth=self.get_other_credentials())
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables, host_data3['variables'])
        self.assertEqual(Host.objects.get(id=host_data3['id']).variables_dict, {'angry': 'penguin'})

        ###########################################
        # GROUPS

        invalid       = dict(name='web1')
        new_group_a   = dict(name='web2', inventory=inv.pk)
        new_group_b   = dict(name='web3', inventory=inv.pk)
        new_group_c   = dict(name='web4', inventory=inv.pk)
        new_group_d   = dict(name='web5', inventory=inv.pk)
        new_group_e   = dict(name='web6', inventory=inv.pk)
        groups = reverse('main:group_list')

        data0 = self.post(groups, data=invalid, expect=400, auth=self.get_super_credentials())
        data0 = self.post(groups, data=new_group_a, expect=201, auth=self.get_super_credentials())

        # an org admin can add groups
        group_data1 = self.post(groups, data=new_group_e, expect=201, auth=self.get_normal_credentials())

        # a normal user cannot add groups
        group_data2 = self.post(groups, data=new_group_b, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions (on any inventory) can create groups
        # already done!
        #edit_perm = Permission.objects.create(
        #     user            = self.other_django_user,
        #     inventory       = Inventory.objects.get(pk=inv.pk),
        #     permission_type = PERM_INVENTORY_WRITE
        #)       
        group_data3 = self.post(groups, data=new_group_c, expect=201, auth=self.get_other_credentials())
 
        # hostnames must be unique inside an organization
        group_data4 = self.post(groups, data=new_group_c, expect=400, auth=self.get_other_credentials())

        #################################################
        # HOSTS->inventories POST via subcollection
       
        url = reverse('main:inventory_hosts_list', args=(self.inventory_a.pk,))
        new_host_a = dict(name='web100.example.com')
        new_host_b = dict(name='web101.example.com')
        new_host_c = dict(name='web102.example.com')
        new_host_d = dict(name='web103.example.com')
        new_host_e = dict(name='web104.example.com')

        # a super user can associate hosts with inventories
        added_by_collection_a = self.post(url, data=new_host_a, expect=201, auth=self.get_super_credentials())

        # an org admin can associate hosts with inventories
        added_by_collection_b = self.post(url, data=new_host_b, expect=201, auth=self.get_normal_credentials())

        # a normal user cannot associate hosts with inventories
        added_by_collection_c = self.post(url, data=new_host_c, expect=403, auth=self.get_nobody_credentials())

        # a normal user with edit permission on the inventory can associate hosts with inventories
        url5 = reverse('main:inventory_hosts_list', args=(inv.pk,))
        added_by_collection_d = self.post(url5, data=new_host_d, expect=201, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 4)

        # now remove the host from inventory (still keeps the record) 
        added_by_collection_d['disassociate'] = 1
        self.post(url5, data=added_by_collection_d, expect=204, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 3)


        ##################################################
        # GROUPS->inventories POST via subcollection
        
        root_groups = reverse('main:inventory_root_groups_list', args=(self.inventory_a.pk,))

        url = reverse('main:inventory_groups_list', args=(self.inventory_a.pk,))
        new_group_a = dict(name='web100')
        new_group_b = dict(name='web101')
        new_group_c = dict(name='web102')
        new_group_d = dict(name='web103')
        new_group_e = dict(name='web104')

        # a super user can associate groups with inventories
        added_by_collection = self.post(url, data=new_group_a, expect=201, auth=self.get_super_credentials())

        # an org admin can associate groups with inventories
        added_by_collection = self.post(url, data=new_group_b, expect=201, auth=self.get_normal_credentials())

        # a normal user cannot associate groups with inventories
        added_by_collection = self.post(url, data=new_group_c, expect=403, auth=self.get_nobody_credentials())

        # a normal user with edit permissions on the inventory can associate groups with inventories
        url5 = reverse('main:inventory_groups_list', args=(inv.pk,))
        added_by_collection = self.post(url5, data=new_group_d, expect=201, auth=self.get_other_credentials())
        # make sure duplicates give 400s
        self.post(url5, data=new_group_d, expect=400, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 4)
        
        # side check: see if root groups URL is operational.  These are groups without parents.
        root_groups = self.get(root_groups, expect=200, auth=self.get_super_credentials())
        self.assertEquals(root_groups['count'], 2)

        remove_me = added_by_collection
        remove_me['disassociate'] = 1
        self.post(url5, data=remove_me, expect=204, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 3)
        
        ###################################################
        # VARIABLES

        vars_a = dict(asdf=1234, dog='fido',  cat='fluffy', unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_b = dict(asdf=4321, dog='barky', cat='snarf',  unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_c = dict(asdf=5555, dog='mouse', cat='mogwai', unstructured=dict(a=[3,0,3],b=dict(z=2600)))

        # attempting to get a variable object creates it, even though it does not already exist
        vdata_url = reverse('main:host_variable_data', args=(added_by_collection_a['id'],))
        
        got = self.get(vdata_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, {})

        # super user can create variable objects
        # an org admin can create variable objects (defers to inventory permissions)
        got = self.put(vdata_url, data=vars_a, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, vars_a) 

        # verify that we can update things and get them back    
        got = self.put(vdata_url, data=vars_c, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, vars_c)    
        got = self.get(vdata_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, vars_c)    

        # a normal user cannot edit variable objects
        self.put(vdata_url, data=vars_a, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory write permissions can edit variable objects...
        got = self.put(vdata_url, data=vars_b, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(got, vars_b)        

        ###################################################
        # VARIABLES -> GROUPS
        
        vars_a = dict(asdf=7777, dog='droopy',   cat='battlecat', unstructured=dict(a=[1,1,1],b=dict(x=1,y=2)))
        vars_b = dict(asdf=8888, dog='snoopy',   cat='cheshire',  unstructured=dict(a=[2,2,2],b=dict(x=3,y=4)))
        vars_c = dict(asdf=9999, dog='pluto',    cat='five',      unstructured=dict(a=[3,3,3],b=dict(z=5)))
        groups = Group.objects.all()

        vdata1_url = reverse('main:group_variable_data', args=(groups[0].pk,))
        vdata2_url = reverse('main:group_variable_data', args=(groups[1].pk,))

        # a super user can associate variable objects with groups
        got = self.get(vdata1_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, {})
        put = self.put(vdata1_url, data=vars_a, expect=200, auth=self.get_super_credentials())
        self.assertEquals(put, vars_a)

        # an org admin can associate variable objects with groups
        put = self.put(vdata1_url, data=vars_b, expect=200, auth=self.get_normal_credentials())
 
        # a normal user cannot associate variable objects with groups
        put = self.put(vdata1_url, data=vars_b, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions can associate variable objects with groups
        put = self.put(vdata1_url, data=vars_c, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(put, vars_c)

        ###################################################
        # VARIABLES -> INVENTORY
        
        vars_a = dict(asdf=9873, dog='lassie',  cat='heathcliff', unstructured=dict(a=[1,1,1],b=dict(x=1,y=2)))
        vars_b = dict(asdf=2736, dog='benji',   cat='garfield',   unstructured=dict(a=[2,2,2],b=dict(x=3,y=4)))
        vars_c = dict(asdf=7692, dog='buck',    cat='sylvester',  unstructured=dict(a=[3,3,3],b=dict(z=5)))
         
        vdata_url = reverse('main:inventory_variable_data', args=(self.inventory_a.pk,))

        # a super user can associate variable objects with inventory
        got = self.get(vdata_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, {})
        put = self.put(vdata_url, data=vars_a, expect=200, auth=self.get_super_credentials())
        self.assertEquals(put, vars_a)

        # an org admin can associate variable objects with inventory
        put = self.put(vdata_url, data=vars_b, expect=200, auth=self.get_normal_credentials())
 
        # a normal user cannot associate variable objects with inventory
        put = self.put(vdata_url, data=vars_b, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions can associate variable objects with inventory
        put = self.put(vdata_url, data=vars_c, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(put, vars_c)
        
        # repeat but request variables in yaml
        got = self.get(vdata_url, expect=200,
                       auth=self.get_normal_credentials(),
                       accept='application/yaml')
        self.assertEquals(got, vars_c)

        # repeat but updates variables in yaml
        put = self.put(vdata_url, data=vars_c, expect=200,
                       auth=self.get_normal_credentials(), data_type='yaml',
                       accept='application/yaml')
        self.assertEquals(put, vars_c)

        ####################################################
        # ADDING HOSTS TO GROUPS

        groups = Group.objects.order_by('pk')
        hosts = Host.objects.order_by('pk')
        host1 = hosts[0]
        host2 = hosts[1]
        host3 = hosts[2]
        groups[0].hosts.add(host1)
        groups[0].hosts.add(host3) 
        groups[0].save()

        # access        
        url1 = reverse('main:group_hosts_list', args=(groups[0].pk,))
        data = self.get(url1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 2)
        self.assertTrue(host1.pk in [x['id'] for x in data['results']])
        self.assertTrue(host3.pk in [x['id'] for x in data['results']])

        # addition
        url = reverse('main:host_detail', args=(host2.pk,))
        got = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(got['id'], host2.pk)
        posted = self.post(url1, data=got, expect=204, auth=self.get_normal_credentials())
        data = self.get(url1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 3)
        self.assertTrue(host2.pk in [x['id'] for x in data['results']])

        # now add one new completely new host, to test creation+association in one go
        new_host = dict(inventory=got['inventory'], name='completelynewhost.example.com', description='...')
        posted = self.post(url1, data=new_host, expect=201, auth=self.get_normal_credentials())
        
        data = self.get(url1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 4)

        # removal
        got['disassociate'] = 1
        posted = self.post(url1, data=got, expect=204, auth=self.get_normal_credentials())
        data = self.get(url1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 3)
        self.assertFalse(host2.pk in [x['id'] for x in data['results']])

        ####################################################
        # SUBGROUPS

        groups = Group.objects.all()

        # just some more groups for kicks
        inva  = Inventory.objects.get(pk=self.inventory_a.pk)
        Group.objects.create(name='group-X1', inventory=inva)
        Group.objects.create(name='group-X2', inventory=inva)
        Group.objects.create(name='group-X3', inventory=inva)
        Group.objects.create(name='group-X4', inventory=inva)
        Group.objects.create(name='group-X5', inventory=inva)

        Permission.objects.create(
            inventory       = inva,
            user            = self.other_django_user,
            permission_type = PERM_INVENTORY_WRITE
        )

        # data used for testing listing all hosts that are transitive members of a group
        g2 = Group.objects.get(name='web4')
        nh = Host.objects.create(name='newhost.example.com', inventory=inva,
                                 created_by=self.super_django_user)
        g2.hosts.add(nh)
        g2.save()

        # a super user can set subgroups
        subgroups_url     = reverse('main:group_children_list',
                                     args=(Group.objects.get(name='web2').pk,))
        child_url         = reverse('main:group_detail',
                                    args=(Group.objects.get(name='web4').pk,))
        subgroups_url2    = reverse('main:group_children_list',
                                    args=(Group.objects.get(name='web6').pk,))
        subgroups_url3    = reverse('main:group_children_list',
                                    args=(Group.objects.get(name='web100').pk,))
        subgroups_url4    = reverse('main:group_children_list',
                                    args=(Group.objects.get(name='web101').pk,))
        got = self.get(child_url, expect=200, auth=self.get_super_credentials())
        self.post(subgroups_url, data=got, expect=204, auth=self.get_super_credentials())
        kids = Group.objects.get(name='web2').children.all()
        self.assertEqual(len(kids), 1)
        checked = self.get(subgroups_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(checked['count'], 1)

        # an org admin can set subgroups
        posted = self.post(subgroups_url2, data=got, expect=204, auth=self.get_normal_credentials())

        # see if we can post a completely new subgroup
        new_data = dict(inventory=inv.pk, name='completely new', description='blarg?')
        kids = self.get(subgroups_url2, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(kids['count'], 1)
        posted2 = self.post(subgroups_url2, data=new_data, expect=201, auth=self.get_normal_credentials()) 

        # a group can't be it's own grandparent
        subsub = posted2['related']['children']
        # this is the grandparent
        original_url = reverse('main:group_detail', args=(Group.objects.get(name='web6').pk,))
        parent_data = self.get(original_url, expect=200, auth=self.get_super_credentials())
        # now posting to kid's children collection...
        self.post(subsub, data=parent_data, expect=403, auth=self.get_super_credentials())

        with_one_more_kid = self.get(subgroups_url2, expect=200, auth=self.get_normal_credentials())
        self.assertEqual(with_one_more_kid['count'], 2)

        # double post causes conflict error (actually, should it? -- just got a 204, already associated)
        # self.post(subgroups_url2, data=got, expect=409, auth=self.get_normal_credentials())
        checked = self.get(subgroups_url2, expect=200, auth=self.get_normal_credentials()) 

        # a normal user cannot set subgroups
        self.post(subgroups_url3, data=got, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions can associate subgroups (but not when they belong to different inventories!)
        #self.post(subgroups_url3, data=got, expect=204, auth=self.get_other_credentials())
        #checked = self.get(subgroups_url3, expect=200, auth=self.get_normal_credentials()) 
        #self.assertEqual(checked['count'], 1)
        
        # slight detour
        # can see all hosts under a group, even if it has subgroups
        # this URL is NOT postable
        all_hosts = reverse('main:group_all_hosts_list',
                            args=(Group.objects.get(name='web2').pk,))
        self.assertEqual(Group.objects.get(name='web2').hosts.count(), 3)
        data = self.get(all_hosts, expect=200, auth=self.get_normal_credentials())
        self.post(all_hosts, data=dict(id=123456, msg='spam'), expect=405, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 4)

        # now post it back to remove it, by adding the disassociate bit
        result = checked['results'][0]
        result['disassociate'] = 1
        self.post(subgroups_url3, data=result, expect=204, auth=self.get_other_credentials())
        checked = self.get(subgroups_url3, expect=200, auth=self.get_normal_credentials()) 
        self.assertEqual(checked['count'], 0)
        # try to double disassociate to see what happens (should no-op)
        self.post(subgroups_url3, data=result, expect=204, auth=self.get_other_credentials())

        # removed group should be automatically marked inactive once it no longer has any parents.
        removed_group = Group.objects.get(pk=result['id'])
        self.assertTrue(removed_group.parents.count())
        self.assertTrue(removed_group.active)
        for parent in removed_group.parents.all():
            parent_children_url = reverse('main:group_children_list', args=(parent.pk,))
            data = {'id': removed_group.pk, 'disassociate': 1}
            self.post(parent_children_url, data, expect=204, auth=self.get_super_credentials())
        removed_group = Group.objects.get(pk=result['id'])
        self.assertFalse(removed_group.active)

        #########################################################
        # FIXME: TAGS

        # the following objects can be tagged and the tags can be read
        #    inventory
        #    host records
        #    group records
        #    variable records
        # this may just be in a seperate test file called 'tags'

        #########################################################
        # FIXME: RELATED FIELDS

        #  on an inventory resource, I can see related resources for hosts and groups and permissions
        #  and these work 
        #  on a host resource, I can see related resources variables and inventories
        #  and these work
        #  on a group resource, I can see related resources for variables, inventories, and children
        #  and these work

    def test_migrate_children_when_group_removed(self):
        # Group A is parent of B, B is parent of C, C is parent of D.
        g_a = self.inventory_a.groups.create(name='A')
        g_b = self.inventory_a.groups.create(name='B')
        g_b.parents.add(g_a)
        g_c = self.inventory_a.groups.create(name='C')
        g_c.parents.add(g_b)
        g_d = self.inventory_a.groups.create(name='D')
        g_d.parents.add(g_c)
        # Each group "X" contains one host "x".
        h_a = self.inventory_a.hosts.create(name='a')
        h_a.groups.add(g_a)
        h_b = self.inventory_a.hosts.create(name='b')
        h_b.groups.add(g_b)
        h_c = self.inventory_a.hosts.create(name='c')
        h_c.groups.add(g_c)
        h_d = self.inventory_a.hosts.create(name='d')
        h_d.groups.add(g_d)

        # Verify that grand-child groups/hosts are not direct children of the
        # parent groups.
        self.assertFalse(g_c in g_a.children.all())
        self.assertFalse(g_d in g_a.children.all())
        self.assertFalse(g_d in g_b.children.all())
        self.assertFalse(h_b in g_a.hosts.all())
        self.assertFalse(h_c in g_a.hosts.all())
        self.assertFalse(h_c in g_b.hosts.all())
        self.assertFalse(h_d in g_a.hosts.all())
        self.assertFalse(h_d in g_b.hosts.all())
        self.assertFalse(h_d in g_c.hosts.all())

        # Delete group B. Its child groups and hosts should now be attached to
        # group A. Group C and D hosts and child groups should be unchanged.
        g_b.delete()
        self.assertTrue(g_c in g_a.children.all())
        self.assertTrue(h_b in g_a.hosts.all())
        self.assertFalse(g_d in g_a.children.all())
        self.assertFalse(h_c in g_a.hosts.all())
        self.assertFalse(h_d in g_a.hosts.all())
        self.assertFalse(h_d in g_c.hosts.all())

        # Mark group C inactive. Its child groups and hosts should now also be
        # attached to group A. Group D hosts should be unchanged.  Group C
        # should also no longer have any group or host relationships.
        g_c.mark_inactive()
        self.assertTrue(g_d in g_a.children.all())
        self.assertTrue(h_c in g_a.hosts.all())
        self.assertFalse(h_d in g_a.hosts.all())
        self.assertFalse(g_c.parents.all())
        self.assertFalse(g_c.children.all())
        self.assertFalse(g_c.hosts.all())

    def test_group_parents_and_children(self):
        # Test for various levels of group parent/child relations, with hosts,
        # to verify that helper properties return the correct querysets.

        # Group A is parent of B, B is parent of C, C is parent of D. Group E
        # is part of the inventory, but outside of the ABCD tree.
        g_a = self.inventory_a.groups.create(name='A')
        g_b = self.inventory_a.groups.create(name='B')
        g_b.parents.add(g_a)
        g_c = self.inventory_a.groups.create(name='C')
        g_c.parents.add(g_b)
        g_d = self.inventory_a.groups.create(name='D')
        g_d.parents.add(g_c)
        g_e = self.inventory_a.groups.create(name='E')
        # Each group "X" contains one host "x".
        h_a = self.inventory_a.hosts.create(name='a')
        h_a.groups.add(g_a)
        h_b = self.inventory_a.hosts.create(name='b')
        h_b.groups.add(g_b)
        h_c = self.inventory_a.hosts.create(name='c')
        h_c.groups.add(g_c)
        h_d = self.inventory_a.hosts.create(name='d')
        h_d.groups.add(g_d)
        h_e = self.inventory_a.hosts.create(name='e')
        h_e.groups.add(g_e)
        # Test all_children property on groups.
        self.assertEqual(set(g_a.all_children.values_list('pk', flat=True)),
                         set([g_b.pk, g_c.pk, g_d.pk]))
        self.assertEqual(set(g_b.all_children.values_list('pk', flat=True)),
                         set([g_c.pk, g_d.pk]))
        self.assertEqual(set(g_c.all_children.values_list('pk', flat=True)),
                         set([g_d.pk]))
        self.assertEqual(set(g_d.all_children.values_list('pk', flat=True)),
                         set([]))
        self.assertEqual(set(g_e.all_children.values_list('pk', flat=True)),
                         set([]))
        # Test all_parents property on groups.
        self.assertEqual(set(g_a.all_parents.values_list('pk', flat=True)),
                         set([]))
        self.assertEqual(set(g_b.all_parents.values_list('pk', flat=True)),
                         set([g_a.pk]))
        self.assertEqual(set(g_c.all_parents.values_list('pk', flat=True)),
                         set([g_a.pk, g_b.pk]))
        self.assertEqual(set(g_d.all_parents.values_list('pk', flat=True)),
                         set([g_a.pk, g_b.pk, g_c.pk]))
        self.assertEqual(set(g_e.all_parents.values_list('pk', flat=True)),
                         set([]))
        # Test all_hosts property on groups.
        self.assertEqual(set(g_a.all_hosts.values_list('pk', flat=True)),
                         set([h_a.pk, h_b.pk, h_c.pk, h_d.pk]))
        self.assertEqual(set(g_b.all_hosts.values_list('pk', flat=True)),
                         set([h_b.pk, h_c.pk, h_d.pk]))
        self.assertEqual(set(g_c.all_hosts.values_list('pk', flat=True)),
                         set([h_c.pk, h_d.pk]))
        self.assertEqual(set(g_d.all_hosts.values_list('pk', flat=True)),
                         set([h_d.pk]))
        self.assertEqual(set(g_e.all_hosts.values_list('pk', flat=True)),
                         set([h_e.pk]))
        # Test all_groups property on hosts.
        self.assertEqual(set(h_a.all_groups.values_list('pk', flat=True)),
                         set([g_a.pk]))
        self.assertEqual(set(h_b.all_groups.values_list('pk', flat=True)),
                         set([g_a.pk, g_b.pk]))
        self.assertEqual(set(h_c.all_groups.values_list('pk', flat=True)),
                         set([g_a.pk, g_b.pk, g_c.pk]))
        self.assertEqual(set(h_d.all_groups.values_list('pk', flat=True)),
                         set([g_a.pk, g_b.pk, g_c.pk, g_d.pk]))
        self.assertEqual(set(h_e.all_groups.values_list('pk', flat=True)),
                         set([g_e.pk]))
        # Now create a circular relationship from D back to A.
        g_a.parents.add(g_d)
        # All groups "ABCD" should be parents of each other, and children of
        # each other, and contain all hosts "abcd".
        for g in [g_a, g_b, g_c, g_d]:
            self.assertEqual(set(g.all_children.values_list('pk', flat=True)),
                             set([g_a.pk, g_b.pk, g_c.pk, g_d.pk]))
            self.assertEqual(set(g.all_parents.values_list('pk', flat=True)),
                             set([g_a.pk, g_b.pk, g_c.pk, g_d.pk]))
            self.assertEqual(set(g.all_hosts.values_list('pk', flat=True)),
                             set([h_a.pk, h_b.pk, h_c.pk, h_d.pk]))
        # All hosts "abcd" should be members of all groups "ABCD".
        for h in [h_a, h_b, h_c, h_d]:
            self.assertEqual(set(h.all_groups.values_list('pk', flat=True)),
                             set([g_a.pk, g_b.pk, g_c.pk, g_d.pk]))
        # Group E and host e should not be affected.
        self.assertEqual(set(g_e.all_children.values_list('pk', flat=True)),
                         set([]))
        self.assertEqual(set(g_e.all_parents.values_list('pk', flat=True)),
                         set([]))
        self.assertEqual(set(g_e.all_hosts.values_list('pk', flat=True)),
                         set([h_e.pk]))
        self.assertEqual(set(h_e.all_groups.values_list('pk', flat=True)),
                         set([g_e.pk]))
