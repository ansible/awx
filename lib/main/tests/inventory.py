# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json

from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from lib.main.models import *
from lib.main.tests.base import BaseTest

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

        # and make one more user that won't be a part of any org, just for negative-access testing

        self.nobody_django_user = User.objects.create(username='nobody')
        self.nobody_django_user.set_password('nobody')
        self.nobody_django_user.save()

    def get_nobody_credentials(self):
        # here is a user without any permissions...
        return ('nobody', 'nobody')

    def test_main_line(self):
       
        # some basic URLs... 
        inventories   = '/api/v1/inventories/'
        inventories_1 = '/api/v1/inventories/1/'
        inventories_2 = '/api/v1/inventories/2/'
        hosts         = '/api/v1/hosts/'
        groups        = '/api/v1/groups/'
        variables     = '/api/v1/variables/'

        # a super user can list inventories
        data = self.get(inventories, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['count'], 2)

        # an org admin can list inventories but is filtered to what he adminsters
        data = self.get(inventories, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 1)

        # a user who is on a team who has a read permissions on an inventory can see filtered inventories
        data = self.get(inventories, expect=200, auth=self.get_other_credentials())
        self.assertEquals(data['count'], 1)      

        # a regular user not part of anything cannot see any inventories
        data = self.get(inventories, expect=200, auth=self.get_nobody_credentials())
        self.assertEquals(data['count'], 0)

        # a super user can get inventory records
        data = self.get(inventories_1, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['name'], 'inventory-a')

        # an org admin can get inventory records
        data = self.get(inventories_1, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['name'], 'inventory-a')

        # a user who is on a team who has read permissions on an inventory can see inventory records
        data = self.get(inventories_1, expect=403, auth=self.get_other_credentials())
        data = self.get(inventories_2, expect=200, auth=self.get_other_credentials())
        self.assertEquals(data['name'], 'inventory-b')

        # a regular user cannot read any inventory records
        data = self.get(inventories_1, expect=403, auth=self.get_nobody_credentials())
        data = self.get(inventories_2, expect=403, auth=self.get_nobody_credentials())

        # a super user can create inventory
        new_inv_1 = dict(name='inventory-c', description='baz', organization=1)
        data = self.post(inventories, data=new_inv_1, expect=201, auth=self.get_super_credentials())
        self.assertEquals(data['id'], 3)

        # an org admin of any org can create inventory, if it is one of his organizations
        # the organization parameter is required!
        new_inv_incomplete = dict(name='inventory-d', description='baz')
        data = self.post(inventories, data=new_inv_incomplete, expect=400,  auth=self.get_normal_credentials())
        new_inv_not_my_org = dict(name='inventory-d', description='baz', organization=3)

        data = self.post(inventories, data=new_inv_not_my_org, expect=403,  auth=self.get_normal_credentials())
        new_inv_my_org = dict(name='inventory-d', description='baz', organization=1)
        data = self.post(inventories, data=new_inv_my_org, expect=201, auth=self.get_normal_credentials())

        # a regular user cannot create inventory
        new_inv_denied = dict(name='inventory-e', description='glorp', organization=1)
        data = self.post(inventories, data=new_inv_denied, expect=403, auth=self.get_other_credentials())

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

        ###########################################
        # GROUPS

        invalid       = dict(name='web1')
        new_group_a   = dict(name='web2', inventory=inv.pk)
        new_group_b   = dict(name='web3', inventory=inv.pk)
        new_group_c   = dict(name='web4', inventory=inv.pk)
        new_group_d   = dict(name='web5', inventory=inv.pk)
        new_group_e   = dict(name='web6', inventory=inv.pk)
        data0 = self.post(groups, data=invalid, expect=400, auth=self.get_super_credentials())
        data0 = self.post(groups, data=new_group_a, expect=201, auth=self.get_super_credentials())

        # an org admin can add hosts
        group_data1 = self.post(groups, data=new_group_e, expect=201, auth=self.get_normal_credentials())

        # a normal user cannot add hosts
        group_data2 = self.post(groups, data=new_group_b, expect=403, auth=self.get_nobody_credentials())

        # a normal user with inventory edit permissions (on any inventory) can create hosts
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
       
        url = '/api/v1/inventories/1/hosts/'
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
        url5 = '/api/v1/inventories/5/hosts/'
        added_by_collection_d = self.post(url5, data=new_host_d, expect=201, auth=self.get_other_credentials())

        ##################################################
        # GROUPS->inventories POST via subcollection
        
        url = '/api/v1/inventories/1/groups/'
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
        url5 = '/api/v1/inventories/5/groups/'
        added_by_collection = self.post(url5, data=new_group_d, expect=201, auth=self.get_other_credentials())
        # make sure duplicates give 400s
        added_by_collection2 = self.post(url5, data=new_group_d, expect=400, auth=self.get_other_credentials())

        ###################################################
        # VARIABLES

        vars_a = dict(asdf=1234, dog='fido',  cat='fluffy', unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_b = dict(asdf=4321, dog='barky', cat='snarf',  unstructured=dict(a=[1,2,3],b=dict(x=2,y=3)))
        vars_c = dict(asdf=5555, dog='mouse', cat='mogwai', unstructured=dict(a=[3,0,3],b=dict(z=2600)))

        # attempting to get a variable object creates it, even though it does not already exist
        vdata_url = "/api/v1/hosts/%s/variable_data/" % (added_by_collection_a['id'])
        got = self.get(vdata_url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got, dict())

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

        # a normal user with inventory write permissions can edit variable objects
        vdata_url = "/api/v1/hosts/1/variable_data/" 
        got = self.put(vdata_url, data=vars_b, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(got, vars_b)        

        # this URL is not one end users will use, but is what you get back from a put
        # as a result, it also needs to be access controlled and working.  You will not
        # be able to put to it.
        backend_url = '/api/v1/variable_data/1/'
        got = self.get(backend_url, expect=200, auth=self.get_normal_credentials())
        got = self.put(backend_url, data=dict(), expect=403, auth=self.get_super_credentials())

        ###################################################
        # VARIABLES -> GROUPS

        # a super user can associate variable objects with groups

        # an org admin can associate variable objects with groups
 
        # a normal user cannot associate variable objects with groups

        # a normal user with inventory edit permissions can associate variable objects with groups

        ####################################################
        # SUBGROUPS

        # a super user can set subgroups

        # an org admin can set subgroups
 
        # a normal user cannot set subgroups

        # a normal user with inventory edit permissions can associate subgroups

        # FIXME: go back and put in GET requests after all the post stuff
         
        #########################################################
        # GROUP CHILDREN ACCESS

        # a super user can see the children attached to a group

        # a org admin can see the children attached to a group

        # a user who is on a team who has read permissions on an inventory can see the children attached to a group
      
        # a regular user cannot see children attached to a group
        
        #########################################################
        # DISASSOCIATION TESTS
        #    hosts from inventory
        #    groups from inventory
        #    subgroups from groups
        #    others?
 
        #########################################################
        # TAGS

        # the following objects can be tagged and the tags can be read

        #    inventory

        #    host records

        #    group records

        #    variable records

        #########################################################
        # RELATED FIELDS

        #  on an inventory resource, I can see related resources for hosts and groups and permissions
        #  and these work 

        #  on a host resource, I can see related resources variables and inventories
        #  and these work

        #  on a group resource, I can see related resources for variables, inventories, and children
        #  and these work
                
    

       

