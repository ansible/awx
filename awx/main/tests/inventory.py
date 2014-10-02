# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import glob
import json
import os
import re
import tempfile

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTest, BaseTransactionTest

__all__ = ['InventoryTest', 'InventoryUpdatesTest']

TEST_SIMPLE_INVENTORY_SCRIPT = "#!/usr/bin/env python\nimport json\nprint json.dumps({'hosts': ['ahost-01', 'ahost-02', 'ahost-03', 'ahost-04']})"

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
        url = reverse('api:inventory_list')
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
        url = reverse('api:inventory_list')

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
        url_a = reverse('api:inventory_detail', args=(self.inventory_a.pk,))
        url_b = reverse('api:inventory_detail', args=(self.inventory_b.pk,))

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
        url_a = reverse('api:inventory_detail', args=(self.inventory_a.pk,))
        url_b = reverse('api:inventory_detail', args=(self.inventory_b.pk,))
        
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

        # Via AC-376:
        # Create an inventory. Leave the description empty. 
        # Edit the new inventory, change the Name, click Save.
        list_url = reverse('api:inventory_list')
        new_data = dict(name='inventory-c', description='',
                        organization=self.organizations[0].pk)
        new_id = max(Inventory.objects.values_list('pk', flat=True)) + 1
        with self.current_user(self.super_django_user):
            data = self.post(list_url, data=new_data, expect=201)
            self.assertEqual(data['id'], new_id)
            self.assertEqual(data['description'], '')
            url_c = reverse('api:inventory_detail', args=(new_id,))
            data = self.get(url_c, expect=200)
            self.assertEqual(data['description'], '')
            data['description'] = None
            #data['name'] = 'inventory-a-update2'
            self.put(url_c, data, expect=200)

    def test_delete_inventory_detail(self):
        url_a = reverse('api:inventory_detail', args=(self.inventory_a.pk,))
        url_b = reverse('api:inventory_detail', args=(self.inventory_b.pk,))
        
        # Create test hosts and groups within each inventory.
        self.inventory_a.hosts.create(name='host-a')
        self.inventory_a.groups.create(name='group-a')
        self.inventory_b.hosts.create(name='host-b')
        self.inventory_b.groups.create(name='group-b')
        
        # Check put to detail view with invalid authentication.
        self.check_invalid_auth(url_a, methods=('delete',))
        self.check_invalid_auth(url_b, methods=('delete',))

        # a regular user cannot delete any inventory records
        with self.current_user(self.nobody_django_user):
            self.delete(url_a, expect=403)
            self.delete(url_b, expect=403)

        # a user who is on a team who has read permissions on an inventory can
        # see inventory records, but not delete.
        with self.current_user(self.other_django_user):
            data = self.get(url_b, expect=200)
            self.delete(url_b, expect=403)

        # an org admin can delete inventory records for his orgs only.
        with self.current_user(self.normal_django_user):
            data = self.get(url_a, expect=200)
            self.delete(url_a, expect=204)
            self.delete(url_b, expect=403)

        # Verify that the inventory is marked inactive, along with all its
        # hosts and groups.
        self.inventory_a = Inventory.objects.get(pk=self.inventory_a.pk)
        self.assertFalse(self.inventory_a.active)
        self.assertFalse(self.inventory_a.hosts.filter(active=True).count())
        self.assertFalse(self.inventory_a.groups.filter(active=True).count())

        # a super user can delete inventory records
        with self.current_user(self.super_django_user):
            self.delete(url_a, expect=404)
            self.delete(url_b, expect=204)

        # Verify that the inventory is marked inactive, along with all its
        # hosts and groups.
        self.inventory_b = Inventory.objects.get(pk=self.inventory_b.pk)
        self.assertFalse(self.inventory_b.active)
        self.assertFalse(self.inventory_b.hosts.filter(active=True).count())
        self.assertFalse(self.inventory_b.groups.filter(active=True).count())

    def test_inventory_access_deleted_permissions(self):
        temp_org = self.make_organizations(self.super_django_user, 1)[0]
        temp_org.admins.add(self.normal_django_user)
        temp_org.users.add(self.other_django_user)
        temp_org.users.add(self.normal_django_user)
        temp_inv = temp_org.inventories.create(name='Delete Org Inventory')
        temp_group1 = temp_inv.groups.create(name='Delete Org Inventory Group')

        temp_perm_read = Permission.objects.create(
            inventory       = temp_inv,
            user            = self.other_django_user,
            permission_type = 'read'
        )

        org_detail = reverse('api:organization_detail', args=(temp_org.pk,))
        inventory_detail = reverse('api:inventory_detail', args=(temp_inv.pk,))
        permission_detail = reverse('api:permission_detail', args=(temp_perm_read.pk,))

        self.get(inventory_detail, expect=200, auth=self.get_other_credentials())
        self.delete(permission_detail, expect=204, auth=self.get_super_credentials())
        self.get(inventory_detail, expect=403, auth=self.get_other_credentials())

    def test_create_inventory_script(self):
        inventory_scripts = reverse('api:inventory_script_list')
        new_script = dict(name="Test", description="Test Script", script=TEST_SIMPLE_INVENTORY_SCRIPT)
        script_data = self.post(inventory_scripts, data=new_script, expect=201, auth=self.get_super_credentials())

        got = self.get(inventory_scripts, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got['count'], 1)

        new_failed_script = dict(name="Shouldfail", description="This test should fail", script=TEST_SIMPLE_INVENTORY_SCRIPT)
        self.post(inventory_scripts, data=new_failed_script, expect=403, auth=self.get_normal_credentials())

    def test_main_line(self):
       
        # some basic URLs... 
        inventories   = reverse('api:inventory_list')
        inventories_1 = reverse('api:inventory_detail', args=(self.inventory_a.pk,))
        inventories_2 = reverse('api:inventory_detail', args=(self.inventory_b.pk,))
        hosts         = reverse('api:host_list')
        groups        = reverse('api:group_list')
        self.create_test_license_file()

        # a super user can add hosts (but inventory ID is required)
        inv = Inventory.objects.create(
            name = 'test inventory',
            organization = self.organizations[0]
        )
        invalid      = dict(name='asdf0.example.com')
        new_host_a   = dict(name=u'asdf\u0162.example.com:1022', inventory=inv.pk)
        new_host_b   = dict(name='asdf1.example.com', inventory=inv.pk)
        new_host_c   = dict(name='127.1.2.3:2022', inventory=inv.pk,
                            variables=json.dumps({'who': 'what?'}))
        new_host_d   = dict(name='asdf3.example.com', inventory=inv.pk)
        new_host_e   = dict(name=u'asdf4.example.com:\u0162', inventory=inv.pk)
        host_data0 = self.post(hosts, data=invalid, expect=400, auth=self.get_super_credentials())
        host_data0 = self.post(hosts, data=new_host_a, expect=201, auth=self.get_super_credentials())
    
        # Port should be split out into host variables.
        host_a = Host.objects.get(pk=host_data0['id'])
        self.assertEqual(host_a.name, u'asdf\u0162.example.com')
        self.assertEqual(host_a.variables_dict, {'ansible_ssh_port': 1022})
 
        # an org admin can add hosts (try first with invalid port #).
        host_data1 = self.post(hosts, data=new_host_e, expect=400, auth=self.get_normal_credentials())
        new_host_e['name'] = u'asdf4.example.com'
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

        # Port should be split out into host variables, other variables kept intact.
        host_c = Host.objects.get(pk=host_data3['id'])
        self.assertEqual(host_c.name, '127.1.2.3')
        self.assertEqual(host_c.variables_dict, {'ansible_ssh_port': 2022, 'who': 'what?'})

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
        groups = reverse('api:group_list')

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

        # Check that we don't allow creating reserved group names.
        data = dict(name='all', inventory=inv.pk)
        with self.current_user(self.super_django_user):
            response = self.post(groups, data=data, expect=400)
        data = dict(name='_meta', inventory=inv.pk)
        with self.current_user(self.super_django_user):
            response = self.post(groups, data=data, expect=400)

        # A new group should not be able to be added a removed group
        del_group = inv.groups.create(name='del')
        undel_group = inv.groups.create(name='nondel')
        del_children_url = reverse('api:group_children_list', args=(del_group.pk,))
        nondel_url         = reverse('api:group_detail',
                                  args=(Group.objects.get(name='nondel').pk,))
        del_group.mark_inactive()
        nondel_detail = self.get(nondel_url, expect=200, auth=self.get_normal_credentials())
        self.post(del_children_url, data=nondel_detail, expect=403, auth=self.get_normal_credentials())


        #################################################
        # HOSTS->inventories POST via subcollection
       
        url = reverse('api:inventory_hosts_list', args=(self.inventory_a.pk,))
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
        url5 = reverse('api:inventory_hosts_list', args=(inv.pk,))
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
        
        root_groups = reverse('api:inventory_root_groups_list', args=(self.inventory_a.pk,))

        url = reverse('api:inventory_groups_list', args=(self.inventory_a.pk,))
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
        url5 = reverse('api:inventory_groups_list', args=(inv.pk,))
        added_by_collection = self.post(url5, data=new_group_d, expect=201, auth=self.get_other_credentials())
        # make sure duplicates give 400s
        self.post(url5, data=new_group_d, expect=400, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 5)
        
        # side check: see if root groups URL is operational.  These are groups without parents.
        root_groups = self.get(root_groups, expect=200, auth=self.get_super_credentials())
        self.assertEquals(root_groups['count'], 2)

        remove_me = added_by_collection
        remove_me['disassociate'] = 1
        self.post(url5, data=remove_me, expect=204, auth=self.get_other_credentials())
        got = self.get(url5, expect=200, auth=self.get_other_credentials())
        self.assertEquals(got['count'], 4)
        
        ###################################################
        # VARIABLES

        vars_a = dict(asdf=1234, dog='fido',  cat='fluffy', unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_b = dict(asdf=4321, dog='barky', cat='snarf',  unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_c = dict(asdf=5555, dog='mouse', cat='mogwai', unstructured=dict(a=[3,0,3],b=dict(z=2600)))

        # attempting to get a variable object creates it, even though it does not already exist
        vdata_url = reverse('api:host_variable_data', args=(added_by_collection_a['id'],))
        
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
        group = Group.objects.get(id=1)

        vdata1_url = reverse('api:group_variable_data', args=(group.pk,))

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
         
        vdata_url = reverse('api:inventory_variable_data', args=(self.inventory_a.pk,))

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
        url1 = reverse('api:group_hosts_list', args=(groups[0].pk,))
        alt_group_hosts = reverse('api:group_hosts_list', args=(groups[1].pk,))
        other_alt_group_hosts = reverse('api:group_hosts_list', args=(groups[2].pk,))

        data = self.get(url1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 2)
        self.assertTrue(host1.pk in [x['id'] for x in data['results']])
        self.assertTrue(host3.pk in [x['id'] for x in data['results']])

        # addition
        url = reverse('api:host_detail', args=(host2.pk,))
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

        # You should be able to add an existing host to a group as a new host and have it be copied
        existing_host = new_host
        self.post(alt_group_hosts, data=existing_host, expect=204, auth=self.get_normal_credentials())

        # Not if the variables are different though
        existing_host['variables'] = '{"booh": "bah"}'
        self.post(other_alt_group_hosts, data=existing_host, expect=400, auth=self.get_normal_credentials())

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
        gx1 = Group.objects.create(name='group-X1', inventory=inva)
        gx2 = Group.objects.create(name='group-X2', inventory=inva)
        gx2.parents.add(gx1)
        gx3 = Group.objects.create(name='group-X3', inventory=inva)
        gx3.parents.add(gx2)
        gx4 = Group.objects.create(name='group-X4', inventory=inva)
        gx4.parents.add(gx3)
        gx5 = Group.objects.create(name='group-X5', inventory=inva)
        gx5.parents.add(gx4)

        Permission.objects.create(
            inventory       = inva,
            user            = self.other_django_user,
            permission_type = PERM_INVENTORY_WRITE
        )

        # data used for testing listing all hosts that are transitive members of a group
        g2 = Group.objects.get(name='web4')
        nh = Host.objects.create(name='newhost.example.com', inventory=g2.inventory,
                                 created_by=self.super_django_user)
        g2.hosts.add(nh)
        g2.save()

        # a super user can set subgroups
        subgroups_url     = reverse('api:group_children_list',
                                     args=(Group.objects.get(name='web2').pk,))
        child_url         = reverse('api:group_detail',
                                    args=(Group.objects.get(name='web4').pk,))
        subgroups_url2    = reverse('api:group_children_list',
                                    args=(Group.objects.get(name='web6').pk,))
        subgroups_url3    = reverse('api:group_children_list',
                                    args=(Group.objects.get(name='web100').pk,))
        subgroups_url4    = reverse('api:group_children_list',
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
        original_url = reverse('api:group_detail', args=(Group.objects.get(name='web6').pk,))
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
        all_hosts = reverse('api:group_all_hosts_list',
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
            parent_children_url = reverse('api:group_children_list', args=(parent.pk,))
            data = {'id': removed_group.pk, 'disassociate': 1}
            self.post(parent_children_url, data, expect=204, auth=self.get_super_credentials())
        removed_group = Group.objects.get(pk=result['id'])
        #self.assertFalse(removed_group.active) # FIXME: Disabled for now because automatically deleting group with no parents is also disabled.

        # Removing a group from a hierarchy should migrate its children to the
        # parent.  The group itself will be deleted (marked inactive), and all
        # relationships removed.
        url = reverse('api:group_children_list', args=(gx2.pk,))
        data = {
            'id': gx3.pk,
            'disassociate': 1,
        }
        with self.current_user(self.super_django_user):
            response = self.post(url, data, expect=204)
        gx3 = Group.objects.get(pk=gx3.pk)
        #self.assertFalse(gx3.active) # FIXME: Disabled for now....
        self.assertFalse(gx3 in gx2.children.all())
        #self.assertTrue(gx4 in gx2.children.all())

        # Try with invalid hostnames and invalid IPs.
        hosts         = reverse('api:host_list')
        invalid_expect = 400 # hostname validation is disabled for now.
        data = dict(name='', inventory=inv.pk)
        with self.current_user(self.super_django_user):
            response = self.post(hosts, data=data, expect=400)
        #data = dict(name='not a valid host name', inventory=inv.pk)
        #with self.current_user(self.super_django_user):
        #    response = self.post(hosts, data=data, expect=invalid_expect)
        data = dict(name='validhost:99999', inventory=inv.pk)
        with self.current_user(self.super_django_user):
            response = self.post(hosts, data=data, expect=invalid_expect)
        #data = dict(name='123.234.345.456', inventory=inv.pk)
        #with self.current_user(self.super_django_user):
        #    response = self.post(hosts, data=data, expect=invalid_expect)
        #data = dict(name='2001::1::3F', inventory=inv.pk)
        #with self.current_user(self.super_django_user):
        #    response = self.post(hosts, data=data, expect=invalid_expect)

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

    def test_get_inventory_script_view(self):
        i_a = self.inventory_a
        i_a.variables = json.dumps({'i-vars': 123})
        i_a.save()
        # Group A is parent of B, B is parent of C, C is parent of D.
        g_a = i_a.groups.create(name='A', variables=json.dumps({'A-vars': 'AAA'}))
        g_b = i_a.groups.create(name='B', variables=json.dumps({'B-vars': 'BBB'}))
        g_b.parents.add(g_a)
        g_c = i_a.groups.create(name='C', variables=json.dumps({'C-vars': 'CCC'}))
        g_c.parents.add(g_b)
        g_d = i_a.groups.create(name='D', variables=json.dumps({'D-vars': 'DDD'}))
        g_d.parents.add(g_c)
        # Each group "X" contains one host "x".
        h_a = i_a.hosts.create(name='a', variables=json.dumps({'a-vars': 'aaa'}))
        h_a.groups.add(g_a)
        h_b = i_a.hosts.create(name='b', variables=json.dumps({'b-vars': 'bbb'}))
        h_b.groups.add(g_b)
        h_c = i_a.hosts.create(name='c', variables=json.dumps({'c-vars': 'ccc'}))
        h_c.groups.add(g_c)
        h_d = i_a.hosts.create(name='d', variables=json.dumps({'d-vars': 'ddd'}))
        h_d.groups.add(g_d)
        # Add another host not in any groups.
        h_z = i_a.hosts.create(name='z', variables=json.dumps({'z-vars': 'zzz'}))

        # Old, slow 1.2 way.
        url = reverse('api:inventory_script_view', args=(i_a.pk,))
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertTrue('all' in response)
        self.assertEqual(response['all']['vars'], i_a.variables_dict)
        self.assertEqual(response['all']['hosts'], ['z'])
        for g in i_a.groups.all():
            self.assertTrue(g.name in response)
            self.assertEqual(response[g.name]['vars'], g.variables_dict)
            self.assertEqual(set(response[g.name]['children']),
                             set(g.children.values_list('name', flat=True)))
            self.assertEqual(set(response[g.name]['hosts']),
                             set(g.hosts.values_list('name', flat=True)))
        self.assertFalse('_meta' in response)
        for h in i_a.hosts.all():
            h_url = '%s?host=%s' % (url, h.name)
            with self.current_user(self.super_django_user):
                response = self.get(h_url, expect=200)
            self.assertEqual(response, h.variables_dict)

        # Now add localhost to the inventory.
        h_l = i_a.hosts.create(name='localhost', variables=json.dumps({'ansible_connection': 'local'}))

        # New 1.3 way.
        url = reverse('api:inventory_script_view', args=(i_a.pk,))
        url = '%s?hostvars=1' % url
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertTrue('all' in response)
        self.assertEqual(response['all']['vars'], i_a.variables_dict)
        self.assertEqual(response['all']['hosts'], ['localhost', 'z'])
        self.assertTrue('_meta' in response)
        self.assertTrue('hostvars' in response['_meta'])
        for h in i_a.hosts.all():
            self.assertEqual(response['_meta']['hostvars'][h.name],
                             h.variables_dict)

    def test_get_inventory_tree_view(self):
        # Group A is parent of B, B is parent of C, C is parent of D.
        g_a = self.inventory_a.groups.create(name='A')
        g_a.inventory_source
        g_b = self.inventory_a.groups.create(name='B')
        g_b.inventory_source
        g_b.parents.add(g_a)
        g_c = self.inventory_a.groups.create(name='C')
        g_c.inventory_source
        g_c.parents.add(g_b)
        g_d = self.inventory_a.groups.create(name='D')
        g_d.inventory_source
        g_d.parents.add(g_c)
        
        url = reverse('api:inventory_tree_view', args=(self.inventory_a.pk,))
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        
        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], g_a.pk)
        self.assertEqual(len(response[0]['children']), 1)
        self.assertEqual(response[0]['children'][0]['id'], g_b.pk)
        self.assertEqual(len(response[0]['children'][0]['children']), 1)
        self.assertEqual(response[0]['children'][0]['children'][0]['id'], g_c.pk)
        self.assertEqual(len(response[0]['children'][0]['children'][0]['children']), 1)
        self.assertEqual(response[0]['children'][0]['children'][0]['children'][0]['id'], g_d.pk)
        self.assertEqual(len(response[0]['children'][0]['children'][0]['children'][0]['children']), 0)

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

    def test_safe_delete_recursion(self):
        # First hierarchy
        top_group = self.inventory_a.groups.create(name='Top1')
        sub_group = self.inventory_a.groups.create(name='Sub1')
        low_group = self.inventory_a.groups.create(name='Low1')

        # Second hierarchy
        other_top_group = self.inventory_a.groups.create(name='Top2')
        other_sub_group = self.inventory_a.groups.create(name='Sub2')
        other_low_group = self.inventory_a.groups.create(name='Low2')

        sub_group.parents.add(top_group)
        low_group.parents.add(sub_group)

        other_sub_group.parents.add(other_top_group)
        other_low_group.parents.add(other_sub_group)

        t1 = self.inventory_a.hosts.create(name='t1')
        t1.groups.add(top_group)
        s1 = self.inventory_a.hosts.create(name='s1')
        s1.groups.add(sub_group)
        l1 = self.inventory_a.hosts.create(name='l1')
        l1.groups.add(low_group)

        t2 = self.inventory_a.hosts.create(name='t2')
        t2.groups.add(other_top_group)
        s2 = self.inventory_a.hosts.create(name='s2')
        s2.groups.add(other_sub_group)
        l2 = self.inventory_a.hosts.create(name='l2')
        l2.groups.add(other_low_group)

        # Copy second hierarchy subgroup under the first hierarchy subgroup
        other_sub_group.parents.add(sub_group)
        self.assertTrue(s2 in sub_group.all_hosts.all())
        self.assertTrue(other_sub_group in sub_group.children.all())

        # Now recursively remove its parent and the reference from subgroup should remain
        other_top_group.mark_inactive_recursive()
        other_top_group = Group.objects.get(pk=other_top_group.pk)
        self.assertTrue(s2 in sub_group.all_hosts.all())
        self.assertTrue(other_sub_group in sub_group.children.all())
        self.assertFalse(other_top_group.active)

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

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   IGNORE_CELERY_INSPECTOR=True,
                   UNIT_TEST_IGNORE_TASK_WAIT=True,
                   PEXPECT_TIMEOUT=60)
class InventoryUpdatesTest(BaseTransactionTest):

    def setUp(self):
        super(InventoryUpdatesTest, self).setUp()
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.organization.admins.add(self.normal_django_user)
        self.organization.users.add(self.other_django_user)
        self.organization.users.add(self.normal_django_user)
        self.inventory = self.organization.inventories.create(name='Cloud Inventory')
        self.group = self.inventory.groups.create(name='Cloud Group')
        self.inventory2 = self.organization.inventories.create(name='Cloud Inventory 2')
        self.group2 = self.inventory2.groups.create(name='Cloud Group 2')
        self.start_queue(settings.CALLBACK_CONSUMER_PORT, settings.CALLBACK_QUEUE_PORT)

    def tearDown(self):
        super(InventoryUpdatesTest, self).tearDown()
        self.terminate_queue()

    def update_inventory_source(self, group, **kwargs):
        inventory_source = group.inventory_source
        update_fields = []
        for field, value in kwargs.items():
            if getattr(inventory_source, field) != value:
                setattr(inventory_source, field, value)
                update_fields.append(field)
        if update_fields:
            inventory_source.save(update_fields=update_fields)
        return inventory_source

    def check_inventory_update(self, inventory_source, should_fail=False,
                               **kwargs):
        inventory_update = kwargs.pop('inventory_update', None)
        should_error = kwargs.pop('should_error', False)
        if not inventory_update:
            inventory_update = inventory_source.update(**kwargs)
            self.assertTrue(inventory_update)
        inventory_update = InventoryUpdate.objects.get(pk=inventory_update.pk)
        #print inventory_update.result_stdout
        if should_error:
            self.assertEqual(inventory_update.status, 'error',
                             inventory_update.result_stdout + \
                             inventory_update.result_traceback)
        elif should_fail:
            self.assertEqual(inventory_update.status, 'failed',
                             inventory_update.result_stdout + \
                             inventory_update.result_traceback)
        elif should_fail is False:
            self.assertEqual(inventory_update.status, 'successful',
                             inventory_update.result_stdout + \
                             inventory_update.result_traceback)
        else:
            pass # If should_fail is None, we don't care.
        return inventory_update

    def check_inventory_source(self, inventory_source, initial=True, enabled_host_pks=None):
        enabled_host_pks = enabled_host_pks or set()
        inventory_source = InventorySource.objects.get(pk=inventory_source.pk)
        inventory = inventory_source.group.inventory
        self.assertTrue(inventory_source.can_update)
        if initial:
            self.assertEqual(inventory.groups.count(), 1)
            self.assertEqual(inventory.hosts.count(), 0)
            self.assertEqual(inventory_source.groups.count(), 0)
            self.assertEqual(inventory_source.hosts.count(), 0)
        inventory_update = self.check_inventory_update(inventory_source)
        inventory_source = InventorySource.objects.get(pk=inventory_source.pk)
        self.assertNotEqual(inventory.groups.count(), 1)
        self.assertNotEqual(inventory.hosts.count(), 0)
        self.assertNotEqual(inventory_source.groups.count(), 0)
        self.assertNotEqual(inventory_source.hosts.count(), 0)
        with self.current_user(self.super_django_user):
            url = reverse('api:inventory_source_groups_list', args=(inventory_source.pk,))
            response = self.get(url, expect=200)
            self.assertNotEqual(response['count'], 0)
            url = reverse('api:inventory_source_hosts_list', args=(inventory_source.pk,))
            response = self.get(url, expect=200)
            self.assertNotEqual(response['count'], 0)
        for host in inventory.hosts.all():
            source_pks = host.inventory_sources.values_list('pk', flat=True)
            self.assertTrue(inventory_source.pk in source_pks)
            self.assertTrue(host.has_inventory_sources)
            if host.pk in enabled_host_pks:
                self.assertTrue(host.enabled)
            # Make sure EC2 RDS hosts are excluded.
            if inventory_source.source == 'ec2':
                self.assertFalse(re.match(r'^.+\.rds\.amazonaws\.com$', host.name, re.I),
                                 host.name)
            with self.current_user(self.super_django_user):
                url = reverse('api:host_inventory_sources_list', args=(host.pk,))
                response = self.get(url, expect=200)
                self.assertNotEqual(response['count'], 0)
        for group in inventory.groups.all():
            source_pks = group.inventory_sources.values_list('pk', flat=True)
            self.assertTrue(inventory_source.pk in source_pks)
            self.assertTrue(group.has_inventory_sources)
            self.assertTrue(group.children.filter(active=True).exists() or
                            group.hosts.filter(active=True).exists())
            # Make sure EC2 instance ID groups and RDS groups are excluded.
            if inventory_source.source == 'ec2':
                self.assertFalse(re.match(r'^i-[0-9a-f]{8}$', group.name, re.I),
                                 group.name)
                self.assertFalse(re.match(r'^rds|rds_.+|type_db_.+$', group.name, re.I),
                                 group.name)
            # Make sure Rackspace instance ID groups are excluded.
            if inventory_source.source == 'rax':
                self.assertFalse(re.match(r'^instance-.+$', group.name, re.I),
                                 group.name)
            with self.current_user(self.super_django_user):
                url = reverse('api:group_inventory_sources_list', args=(group.pk,))
                response = self.get(url, expect=200)
                self.assertNotEqual(response['count'], 0)
        # Try to set a source on a child group that was imported.  Should not
        # be allowed.
        for group in inventory_source.group.children.all():
            inv_src_2 = group.inventory_source
            inv_src_url2 = reverse('api:inventory_source_detail', args=(inv_src_2.pk,))
            with self.current_user(self.super_django_user):
                data = self.get(inv_src_url2, expect=200)
                if inventory_source.credential is not None:
                    data.update({
                        'source': inventory_source.source,
                        'credential': inventory_source.credential.pk,
                    })
                else:
                    data.update({'source': inventory_source.source})
                response = self.put(inv_src_url2, data, expect=400)
                self.assertTrue('source' in response, response)
        # Make sure we can delete the inventory update.
        inv_up_url = reverse('api:inventory_update_detail', args=(inventory_update.pk,))
        with self.current_user(self.super_django_user):
            self.get(inv_up_url, expect=200)
            self.delete(inv_up_url, expect=204)
            self.get(inv_up_url, expect=404)

    def test_put_inventory_source_detail_with_regions(self):
        creds_url = reverse('api:credential_list')
        inv_src_url1 = reverse('api:inventory_source_detail',
                               args=(self.group.inventory_source.pk,))
        inv_src_url2 = reverse('api:inventory_source_detail',
                               args=(self.group2.inventory_source.pk,))
        # Create an AWS credential to use for first inventory source.
        aws_cred_data = {
            'name': 'AWS key that does not need to have valid info because '
                    'we do not care if the update actually succeeds',
            'kind': 'aws',
            'user': self.super_django_user.pk,
            'username': 'aws access key id goes here',
            'password': 'aws secret access key goes here',
        }
        with self.current_user(self.super_django_user):
            aws_cred_response = self.post(creds_url, aws_cred_data, expect=201)
        aws_cred_id = aws_cred_response['id']
        # Create a RAX credential to use for second inventory source.
        rax_cred_data = {
            'name': 'RAX cred that does not need to have valid info because '
                    'we do not care if the update actually succeeds',
            'kind': 'rax',
            'user': self.super_django_user.pk,
            'username': 'rax username',
            'password': 'rax api key',
        }
        with self.current_user(self.super_django_user):
            rax_cred_response = self.post(creds_url, rax_cred_data, expect=201)
        rax_cred_id = rax_cred_response['id']
        # Verify the options request gives ec2 and rax region choices.
        with self.current_user(self.super_django_user):
            response = self.options(inv_src_url1, expect=200)
            self.assertTrue('ec2_region_choices' in response['actions']['GET']['source_regions'])
            self.assertTrue('rax_region_choices' in response['actions']['GET']['source_regions'])
        # Updaate the first inventory source to use EC2 with empty regions.
        inv_src_data = {
            'source': 'ec2',
            'credential': aws_cred_id,
            'source_regions': '',
        }
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], '')
        # All region.
        inv_src_data['source_regions'] = 'ALL'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'all')
        # Invalid region.
        inv_src_data['source_regions'] = 'us-north-99'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # All takes precedence over any other regions.
        inv_src_data['source_regions'] = 'us-north-99,,all'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'all')
        # Valid region.
        inv_src_data['source_regions'] = 'us-west-1'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'us-west-1')
        # Invalid region (along with valid one).
        inv_src_data['source_regions'] = 'us-west-1, us-north-99'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Valid regions.
        inv_src_data['source_regions'] = 'us-west-1, us-east-1, '
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'us-west-1,us-east-1')
        # Updaate the second inventory source to use RAX with empty regions.
        inv_src_data = {
            'source': 'rax',
            'credential': rax_cred_id,
            'source_regions': '',
        }
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], '')
        # All region.
        inv_src_data['source_regions'] = 'all'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'ALL')
        # Invalid region.
        inv_src_data['source_regions'] = 'RDU'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=400)
        # All takes precedence over any other regions.
        inv_src_data['source_regions'] = 'RDU,,all'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'ALL')
        # Valid region.
        inv_src_data['source_regions'] = 'dfw'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'DFW')
        # Invalid region (along with valid one).
        inv_src_data['source_regions'] = 'dfw, rdu'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=400)
        # Valid regions.
        inv_src_data['source_regions'] = 'ORD, iad, '
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url2, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], 'ORD,IAD')

    def test_post_inventory_source_update(self):
        creds_url = reverse('api:credential_list')
        inv_src_url = reverse('api:inventory_source_detail',
                              args=(self.group.inventory_source.pk,))
        inv_src_update_url = reverse('api:inventory_source_update_view',
                                     args=(self.group.inventory_source.pk,))
        # Create a credential to use for this inventory source.
        aws_cred_data = {
            'name': 'AWS key that does not need to have valid info because we '
                    'do not care if the update actually succeeds',
            'kind': 'aws',
            'user': self.super_django_user.pk,
            'username': 'aws access key id goes here',
            'password': 'aws secret access key goes here',
        }
        with self.current_user(self.super_django_user):
            aws_cred_response = self.post(creds_url, aws_cred_data, expect=201)
        aws_cred_id = aws_cred_response['id']
        # Updaate the inventory source to use EC2.
        inv_src_data = {
            'source': 'ec2',
            'credential': aws_cred_id,
        }
        with self.current_user(self.super_django_user):
            self.put(inv_src_url, inv_src_data, expect=200)
        # Read the inventory source, verify the update URL returns can_update.
        with self.current_user(self.super_django_user):
            self.get(inv_src_url, expect=200)
            response = self.get(inv_src_update_url, expect=200)
            self.assertTrue(response['can_update'])
        # Now do the update.
        with self.current_user(self.super_django_user):
            self.post(inv_src_update_url, {}, expect=202)
        # Normal user should be allowed as an org admin.
        with self.current_user(self.normal_django_user):
            self.get(inv_src_url, expect=200)
            response = self.get(inv_src_update_url, expect=200)
            self.assertTrue(response['can_update'])
        with self.current_user(self.normal_django_user):
            self.post(inv_src_update_url, {}, expect=202)
        # Other user should be denied as only an org user.
        with self.current_user(self.other_django_user):
            self.get(inv_src_url, expect=403)
            response = self.get(inv_src_update_url, expect=403)
        with self.current_user(self.other_django_user):
            self.post(inv_src_update_url, {}, expect=403)
        # If given read permission to the inventory, other user should be able
        # to see the inventory source and update view, but not start an update.
        other_perms_url = reverse('api:user_permissions_list',
                                  args=(self.other_django_user.pk,))
        other_perms_data = {
            'name': 'read only inventory permission for other',
            'user': self.other_django_user.pk,
            'inventory': self.inventory.pk,
            'permission_type': 'read',
        }
        with self.current_user(self.super_django_user):
            self.post(other_perms_url, other_perms_data, expect=201)
        with self.current_user(self.other_django_user):
            self.get(inv_src_url, expect=200)
            response = self.get(inv_src_update_url, expect=200)
        with self.current_user(self.other_django_user):
            self.post(inv_src_update_url, {}, expect=403)
        # Once given write permission, the normal user is able to update the
        # inventory source.
        other_perms_data = {
            'name': 'read-write inventory permission for other',
            'user': self.other_django_user.pk,
            'inventory': self.inventory.pk,
            'permission_type': 'write',
        }
        with self.current_user(self.super_django_user):
            self.post(other_perms_url, other_perms_data, expect=201)
        with self.current_user(self.other_django_user):
            self.get(inv_src_url, expect=200)
            response = self.get(inv_src_update_url, expect=200)
            # FIXME: This is misleading, as an update would fail...
            self.assertTrue(response['can_update'])
        with self.current_user(self.other_django_user):
            self.post(inv_src_update_url, {}, expect=202)
        # Nobody user should be denied as well.
        with self.current_user(self.nobody_django_user):
            self.get(inv_src_url, expect=403)
            response = self.get(inv_src_update_url, expect=403)
        with self.current_user(self.nobody_django_user):
            self.post(inv_src_update_url, {}, expect=403)

    def test_update_from_ec2(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        if not all([source_username, source_password]):
            self.skipTest('no test ec2 credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               user=self.super_django_user,
                                               username=source_username,
                                               password=source_password)
        # Set parent group name to one that might be created by the sync.
        group = self.group
        group.name = 'ec2'
        group.save()
        self.group = group
        cache_path = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path)
        inventory_source = self.update_inventory_source(self.group,
            source='ec2', credential=credential, source_regions=source_regions,
            source_vars='---\n\nnested_groups: false\ncache_path: %s\n' % cache_path)
        # Check first without instance_id set (to import by name only).
        with self.settings(EC2_INSTANCE_ID_VAR=''):
            self.check_inventory_source(inventory_source)
        # Rename hosts and verify the import picks up the instance_id present
        # in host variables.
        for host in self.inventory.hosts.all():
            self.assertFalse(host.instance_id, host.instance_id)
            host.name = 'updated-%s' % host.name
            host.save()
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertEqual(old_host_pks, new_host_pks)
        # Manually disable all hosts, verify a new update re-enables them.
        # Also change the host name, and verify it is not deleted, but instead
        # updated because the instance ID matches.
        enabled_host_pks = set(self.inventory.hosts.filter(enabled=True).values_list('pk', flat=True))
        for host in self.inventory.hosts.all():
            host.enabled = False
            host.name = 'changed-%s' % host.name
            host.save()
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False, enabled_host_pks=enabled_host_pks)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertEqual(old_host_pks, new_host_pks)
        # Verify that main group is in top level groups (hasn't been added as
        # its own child).
        self.assertTrue(self.group in self.inventory.root_groups)

    def test_update_from_ec2_with_nested_groups(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        if not all([source_username, source_password]):
            self.skipTest('no test ec2 credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               user=self.super_django_user,
                                               username=source_username,
                                               password=source_password)
        group = self.group
        group.name = 'AWS Inventory'
        group.save()
        self.group = group
        cache_path_pattern = os.path.join(tempfile.gettempdir(), 'awx_ec2_*')
        old_cache_paths = set(glob.glob(cache_path_pattern))
        inventory_source = self.update_inventory_source(self.group,
            source='ec2', credential=credential, source_regions=source_regions,
            source_vars='---') # nested_groups is true by default.
        self.check_inventory_source(inventory_source)
        # Verify that main group is in top level groups (hasn't been added as
        # its own child).
        self.assertTrue(self.group in self.inventory.root_groups)
        # Verify that returned groups are nested:
        child_names = self.group.children.values_list('name', flat=True)
        for name in child_names:
            self.assertFalse(name.startswith('us-'))
            self.assertFalse(name.startswith('type_'))
            self.assertFalse(name.startswith('key_'))
            self.assertFalse(name.startswith('security_group_'))
            self.assertFalse(name.startswith('tag_'))
        self.assertTrue('ec2' in child_names)
        self.assertTrue('regions' in child_names)
        self.assertTrue('types' in child_names)
        self.assertTrue('keys' in child_names)
        self.assertTrue('security_groups' in child_names)
        self.assertTrue('tags' in child_names)
        # Make sure we clean up the cache path when finished (when one is not
        # provided explicitly via source_vars).
        new_cache_paths = set(glob.glob(cache_path_pattern))
        self.assertEqual(old_cache_paths, new_cache_paths)
        return
        # Print out group/host tree for debugging.
        print
        def draw_tree(g, d=0):
            print ('  ' * d) + '+ ' + g.name
            for h in g.hosts.order_by('name'):
                print ('  ' * d) + '  - ' + h.name
            for c in g.children.order_by('name'):
                draw_tree(c, d+1)
        for g in self.inventory.root_groups.order_by('name'):
            draw_tree(g)
        
    def test_update_from_rax(self):
        source_username = getattr(settings, 'TEST_RACKSPACE_USERNAME', '')
        source_password = getattr(settings, 'TEST_RACKSPACE_API_KEY', '')
        source_regions = getattr(settings, 'TEST_RACKSPACE_REGIONS', '')
        if not all([source_username, source_password]):
            self.skipTest('no test rackspace credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='rax',
                                               user=self.super_django_user,
                                               username=source_username,
                                               password=source_password)
        # Set parent group name to one that might be created by the sync.
        group = self.group
        group.name = 'DFW'
        group.save()
        self.group = group
        inventory_source = self.update_inventory_source(self.group,
            source='rax', credential=credential, source_regions=source_regions)
        # Check first without instance_id set (to import by name only).
        with self.settings(RAX_INSTANCE_ID_VAR=''):
            self.check_inventory_source(inventory_source)
        # Rename hosts and verify the import picks up the instance_id present
        # in host variables.
        for host in self.inventory.hosts.all():
            self.assertFalse(host.instance_id, host.instance_id)
            host.name = 'updated-%s' % host.name
            host.save()
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertEqual(old_host_pks, new_host_pks)
        # Manually disable all hosts, verify a new update re-enables them.
        # Also change the host name, and verify it is not deleted, but instead
        # updated because the instance ID matches.
        enabled_host_pks = set(self.inventory.hosts.filter(enabled=True).values_list('pk', flat=True))
        for host in self.inventory.hosts.all():
            host.enabled = False
            host.name = 'changed-%s' % host.name
            host.save()
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False, enabled_host_pks=enabled_host_pks)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertEqual(old_host_pks, new_host_pks)
        # If test source regions is given, test again with empty string.
        if source_regions:
            inventory_source2 = self.update_inventory_source(self.group2,
                source='rax', credential=credential, source_regions='')
            self.check_inventory_source(inventory_source2)
        # Verify that main group is in top level groups (hasn't been added as
        # its own child).
        self.assertTrue(self.group in self.inventory.root_groups)

    def test_update_from_custom_script(self):
        # Create the inventory script
        self.create_test_license_file()
        inventory_scripts = reverse('api:inventory_script_list')
        new_script = dict(name="Test", description="Test Script", script=TEST_SIMPLE_INVENTORY_SCRIPT)
        script_data = self.post(inventory_scripts, data=new_script, expect=201, auth=self.get_super_credentials())

        custom_inv = self.organization.inventories.create(name='Custom Script Inventory')
        custom_group = custom_inv.groups.create(name="Custom Script Group")
        custom_inv_src = reverse('api:inventory_source_detail',
                                 args=(custom_group.inventory_source.pk,))
        custom_inv_update = reverse('api:inventory_source_update_view',
                                    args=(custom_group.inventory_source.pk,))
        inv_src_opts = {'source': 'custom',
                        'source_script': script_data["id"]}
        with self.current_user(self.super_django_user):
            response = self.put(custom_inv_src, inv_src_opts, expect=200)
        self.check_inventory_source(custom_group.inventory_source)
