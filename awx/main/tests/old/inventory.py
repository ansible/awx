# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import glob
import json
import os
import re
import tempfile
import time
import unittest2 as unittest


# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseTest, BaseTransactionTest

__all__ = ['InventoryTest', 'InventoryUpdatesTest', 'InventoryCredentialTest']

TEST_SIMPLE_INVENTORY_SCRIPT = "#!/usr/bin/env python\nimport json\nprint json.dumps({'hosts': ['ahost-01', 'ahost-02', 'ahost-03', 'ahost-04']})"
TEST_SIMPLE_INVENTORY_SCRIPT_WITHOUT_HASHBANG = "import json\nprint json.dumps({'hosts': ['ahost-01', 'ahost-02', 'ahost-03', 'ahost-04']})"

TEST_UNICODE_INVENTORY_SCRIPT = u"""#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
inventory = dict()
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'] = list()
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'].append('host-\xb3\u01a0\u0157\u0157\u0157\u0157:\u02fe\u032d\u015f')
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'].append('host-\u0124\u01bd\u03d1j\xffFK\u0145\u024c\u024c')
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'].append('host-@|\u022e|\u022e\xbf\u03db\u0148\u02b9\xbf')
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'].append('host-;\u023a\u023a\u0181\u017f\u0242\u0242\u029c\u0250')
inventory['group-\u037c\u03b4\u0138\u0137\u03cd\u03a1\u0121\u0137\u0138\u01a1'].append('host-B\u0338\u0338\u0330\u0365\u01b2\u02fa\xdd\u013b\u01b2')
print json.dumps(inventory)
"""


@unittest.skipIf(os.environ.get('SKIP_SLOW_TESTS', False), 'Skipping slow test')
class InventoryTest(BaseTest):

    def setUp(self):
        self.start_rabbit()
        super(InventoryTest, self).setUp()
        self.setup_instances()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 3)
        self.organizations[0].admin_role.members.add(self.normal_django_user)
        self.organizations[0].member_role.members.add(self.other_django_user)
        self.organizations[0].member_role.members.add(self.normal_django_user)

        self.inventory_a = Inventory.objects.create(name='inventory-a', description='foo', organization=self.organizations[0])
        self.inventory_b = Inventory.objects.create(name='inventory-b', description='bar', organization=self.organizations[1])

        # the normal user is an org admin of org 0

        # create a permission here on the 'other' user so they have edit access on the org
        # we may add another permission type later.
        self.inventory_b.read_role.members.add(self.other_django_user)

    def tearDown(self):
        super(InventoryTest, self).tearDown()
        self.stop_rabbit()

    def test_get_inventory_list(self):
        url = reverse('api:inventory_list')
        qs = Inventory.objects.distinct()

        # Check list view with invalid authentication.
        self.check_invalid_auth(url)

        # a super user can list all inventories
        self.check_get_list(url, self.super_django_user, qs)

        # an org admin can list inventories but is filtered to what he adminsters
        normal_qs = qs.filter(organization__admin_role__members=self.normal_django_user)
        self.check_get_list(url, self.normal_django_user, normal_qs)

        # a user who is on a team who has a read permissions on an inventory can see filtered inventories
        other_qs = Inventory.accessible_objects(self.other_django_user, 'read_role').distinct()
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
        a_pk = self.inventory_a.pk
        b_pk = self.inventory_b.pk

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
            self.get(url_b, expect=200)
            self.delete(url_b, expect=403)

        # an org admin can delete inventory records for his orgs only.
        with self.current_user(self.normal_django_user):
            self.get(url_a, expect=200)
            self.delete(url_a, expect=204)
            self.delete(url_b, expect=403)

        # Verify that the inventory was deleted
        assert Inventory.objects.filter(pk=a_pk).count() == 0

        # a super user can delete inventory records
        with self.current_user(self.super_django_user):
            self.delete(url_a, expect=404)
            self.delete(url_b, expect=204)

        # Verify that the inventory was deleted
        assert Inventory.objects.filter(pk=b_pk).count() == 0

    def test_inventory_access_deleted_permissions(self):
        temp_org = self.make_organizations(self.super_django_user, 1)[0]
        temp_org.admin_role.members.add(self.normal_django_user)
        temp_org.member_role.members.add(self.other_django_user)
        temp_org.member_role.members.add(self.normal_django_user)
        temp_inv = temp_org.inventories.create(name='Delete Org Inventory')
        temp_inv.groups.create(name='Delete Org Inventory Group')

        temp_inv.read_role.members.add(self.other_django_user)

        reverse('api:organization_detail', args=(temp_org.pk,))
        inventory_detail = reverse('api:inventory_detail', args=(temp_inv.pk,))
        read_role_users_list = reverse('api:role_users_list', args=(temp_inv.read_role.pk,))

        self.get(inventory_detail, expect=200, auth=self.get_other_credentials())
        self.post(read_role_users_list, data={'disassociate': True, "id": self.other_django_user.id}, expect=204, auth=self.get_super_credentials())
        self.get(inventory_detail, expect=403, auth=self.get_other_credentials())

    def test_create_inventory_script(self):
        inventory_scripts = reverse('api:inventory_script_list')
        new_script = dict(name="Test", description="Test Script", script=TEST_SIMPLE_INVENTORY_SCRIPT, organization=self.organizations[0].id)
        self.post(inventory_scripts, data=new_script, expect=201, auth=self.get_super_credentials())

        got = self.get(inventory_scripts, expect=200, auth=self.get_super_credentials())
        self.assertEquals(got['count'], 1)

        new_failed_script = dict(name="Should not fail", description="This test should not fail", script=TEST_SIMPLE_INVENTORY_SCRIPT, organization=self.organizations[0].id)
        self.post(inventory_scripts, data=new_failed_script, expect=201, auth=self.get_normal_credentials())

        failed_no_shebang = dict(name="ShouldFail", descript="This test should fail", script=TEST_SIMPLE_INVENTORY_SCRIPT_WITHOUT_HASHBANG,
                                 organization=self.organizations[0].id)
        self.post(inventory_scripts, data=failed_no_shebang, expect=400, auth=self.get_super_credentials())

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
        i_a.hosts.create(name='z', variables=json.dumps({'z-vars': 'zzz'}))

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
        i_a.hosts.create(name='localhost', variables=json.dumps({'ansible_connection': 'local'}))

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
        g_c.delete()
        self.assertTrue(g_d in g_a.children.all())
        self.assertTrue(h_c in g_a.hosts.all())
        self.assertFalse(h_d in g_a.hosts.all())

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
        other_top_group.delete_recursive()
        self.assertTrue(s2 in sub_group.all_hosts.all())
        self.assertTrue(other_sub_group in sub_group.children.all())

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

    def test_dashboard_hosts_count(self):
        url = reverse('api:dashboard_view')

        # Test with zero hosts.
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertEqual(response['hosts']['total'], 0)
        self.assertEqual(response['hosts']['failed'], 0)

        # Create hosts with the same name in different inventories.  This host
        # count should include total hosts, not unique names.
        for x in xrange(4):
            hostname = 'host-%d' % x
            self.inventory_a.hosts.create(name=hostname)
            self.inventory_b.hosts.create(name=hostname)
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertEqual(response['hosts']['total'], 8)
        self.assertEqual(response['hosts']['failed'], 0)

        # Mark all hosts in one inventory as failed.  Failed count should
        # reflect all hosts, not unique hostnames.
        for host in self.inventory_a.hosts.all():
            host.has_active_failures = True
            host.save()
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertEqual(response['hosts']['total'], 8)
        self.assertEqual(response['hosts']['failed'], 4)

        # Mark all hosts in the other inventory as failed.  Failed count
        # should reflect all hosts and never be greater than total.
        for host in self.inventory_b.hosts.all():
            host.has_active_failures = True
            host.save()
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        self.assertEqual(response['hosts']['total'], 8)
        self.assertEqual(response['hosts']['failed'], 8)


@unittest.skipIf(os.environ.get('SKIP_SLOW_TESTS', False), 'Skipping slow test')
@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   IGNORE_CELERY_INSPECTOR=True,
                   UNIT_TEST_IGNORE_TASK_WAIT=True,
                   PEXPECT_TIMEOUT=60)
class InventoryUpdatesTest(BaseTransactionTest):

    def setUp(self):
        super(InventoryUpdatesTest, self).setUp()
        self.setup_instances()
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.organization.admin_role.members.add(self.normal_django_user)
        self.organization.member_role.members.add(self.other_django_user)
        self.organization.member_role.members.add(self.normal_django_user)
        self.inventory = self.organization.inventories.create(name='Cloud Inventory')
        self.group = self.inventory.groups.create(name='Cloud Group')
        self.inventory2 = self.organization.inventories.create(name='Cloud Inventory 2')
        self.group2 = self.inventory2.groups.create(name='Cloud Group 2')
        self.start_queue()

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
            if not should_fail and not should_error:
                self.assertTrue(inventory_update)
            elif not inventory_update:
                return None
        inventory_update = InventoryUpdate.objects.get(pk=inventory_update.pk)
        #print inventory_update.result_stdout
        if should_error:
            self.assertEqual(inventory_update.status, 'error',
                             inventory_update.result_stdout +
                             inventory_update.result_traceback)
        elif should_fail:
            self.assertEqual(inventory_update.status, 'failed',
                             inventory_update.result_stdout +
                             inventory_update.result_traceback)
        elif should_fail is False:
            self.assertEqual(inventory_update.status, 'successful',
                             inventory_update.result_stdout +
                             inventory_update.result_traceback)
        else:
            pass # If should_fail is None, we don't care.
        return inventory_update

    def check_inventory_source(self, inventory_source, initial=True, enabled_host_pks=None, instance_id_group_ok=False):
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
            self.assertTrue(group.children.exists() or
                            group.hosts.exists())
            # Make sure EC2 instance ID groups and RDS groups are excluded.
            if inventory_source.source == 'ec2' and not instance_id_group_ok:
                self.assertFalse(re.match(r'^i-[0-9a-f]{8}$', group.name, re.I),
                                 group.name)
            if inventory_source.source == 'ec2':
                self.assertFalse(re.match(r'^rds|rds_.+|type_db_.+$', group.name, re.I),
                                 group.name)
            # Make sure Rackspace instance ID groups are excluded.
            if inventory_source.source == 'rax' and not instance_id_group_ok:
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
                if inventory_source.source == 'custom':
                    data['source_script'] = inventory_source.source_script.pk
                response = self.put(inv_src_url2, data, expect=400)
                self.assertTrue('source' in response, response)
        # Make sure we can delete the inventory update.
        inv_up_url = reverse('api:inventory_update_detail', args=(inventory_update.pk,))
        with self.current_user(self.super_django_user):
            self.get(inv_up_url, expect=200)
            self.delete(inv_up_url, expect=204)
            self.get(inv_up_url, expect=404)

    def print_group_tree(self, group, depth=0):
        print ('  ' * depth) + '+ ' + group.name
        for host in group.hosts.order_by('name'):
            print ('  ' * depth) + '  - ' + host.name
        for child in group.children.order_by('name'):
            self.print_group_tree(child, depth + 1)

    def print_inventory_tree(self, inventory):
        # Print out group/host tree for debugging.
        for group in inventory.root_groups.order_by('name'):
            self.print_group_tree(group)

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
            'instance_filters': '',
            'group_by': '',
        }
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['source_regions'], '')
        # EC2 sources should allow an empty credential (to support IAM roles).
        inv_src_data['credential'] = None
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['credential'], None)
        inv_src_data['credential'] = aws_cred_id
        # Null for instance filters and group_by should be converted to empty
        # string.
        inv_src_data['instance_filters'] = None
        inv_src_data['group_by'] = None
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
            self.assertEqual(response['instance_filters'], '')
            self.assertEqual(response['group_by'], '')
        # Invalid string for instance filters.
        inv_src_data['instance_filters'] = 'tag-key_123=Name,'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Invalid field name for instance filters.
        inv_src_data['instance_filters'] = 'foo=bar,'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Invalid tag expression for instance filters.
        inv_src_data['instance_filters'] = 'tag:=,'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Another invalid tag expression for instance filters.
        inv_src_data['instance_filters'] = 'tag:Name,'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Valid string for instance filters.
        inv_src_data['instance_filters'] = 'tag-key=Name'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
        # Another valid value for instance filters.
        inv_src_data['instance_filters'] = 'tag:Name=test*'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
        # Another valid instance filter with nothing after =.
        inv_src_data['instance_filters'] = 'tag:Name='
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
        # Invalid string for group_by.
        inv_src_data['group_by'] = 'ec2_region,'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=400)
        # Valid string for group_by.
        inv_src_data['group_by'] = 'region,key_pair,instance_type'
        with self.current_user(self.super_django_user):
            response = self.put(inv_src_url1, inv_src_data, expect=200)
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
            'instance_filters': None,
            'group_by': None,
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

    def test_update_from_ec2(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        if not all([source_username, source_password]):
            self.skipTest('no test ec2 credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               username=source_username,
                                               password=source_password)
        credential.admin_role.members.add(self.super_django_user)
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
        instance_types = {}
        key_names = {}
        for host in self.inventory.hosts.all():
            host.enabled = False
            host.name = 'changed-%s' % host.name
            host.save()
            # Get instance types for later use with instance_filters.
            instance_type = host.variables_dict.get('ec2_instance_type', '')
            if instance_type:
                instance_types.setdefault(instance_type, []).append(host.pk)
            # Get key names for later use with instance_filters.
            key_name = host.variables_dict.get('ec2_key_name', '')
            if key_name:
                key_names.setdefault(key_name, []).append(host.pk)
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False, enabled_host_pks=enabled_host_pks)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertEqual(old_host_pks, new_host_pks)
        # Verify that main group is in top level groups (hasn't been added as
        # its own child).
        self.assertTrue(self.group in self.inventory.root_groups)

        # Now add instance filters and verify that only matching hosts are
        # synced, specify new cache path to force refresh.
        cache_path = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path)
        instance_type = max(instance_types.items(), key=lambda x: len(x[1]))[0]
        inventory_source.instance_filters = 'instance-type=%s' % instance_type
        inventory_source.source_vars = '---\n\nnested_groups: false\ncache_path: %s\n' % cache_path
        inventory_source.overwrite = True
        inventory_source.save()
        self.check_inventory_source(inventory_source, initial=False)
        for host in self.inventory.hosts.all():
            self.assertEqual(host.variables_dict['ec2_instance_type'], instance_type)

        # Try invalid instance filters that should be ignored:
        # empty filter, only "=", more than one "=", whitespace, invalid value
        # for given filter name.
        cache_path = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path)
        key_name = max(key_names.items(), key=lambda x: len(x[1]))[0]
        inventory_source.instance_filters = ',=,image-id=ami=12345678,instance-type=%s, key-name=%s, architecture=ppc' % (instance_type, key_name)
        inventory_source.source_vars = '---\n\nnested_groups: false\ncache_path: %s\n' % cache_path
        inventory_source.save()
        self.check_inventory_source(inventory_source, initial=False)


    def test_update_from_ec2_sts_iam(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        source_token = getattr(settings, 'TEST_AWS_SECURITY_TOKEN', '')
        if not all([source_username, source_password, source_token]):
            self.skipTest('no test ec2 sts credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               username=source_username,
                                               password=source_password,
                                               security_token=source_token)
        credential.admin_role.members.add(self.super_django_user)
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
        self.check_inventory_source(inventory_source)

    def test_update_from_ec2_sts_iam_bad_token(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               username=source_username,
                                               password=source_password,
                                               security_token="BADTOKEN")
        credential.admin_role.members.add(self.super_django_user)

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
        self.check_inventory_update(inventory_source, should_fail=True)

    def test_update_from_ec2_without_credential(self):
        self.create_test_license_file()
        group = self.group
        group.name = 'ec2'
        group.save()
        self.group = group
        cache_path = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path)
        inventory_source = self.update_inventory_source(self.group, source='ec2')
        self.check_inventory_update(inventory_source, should_fail=True)

    def test_update_from_ec2_with_nested_groups(self):
        source_username = getattr(settings, 'TEST_AWS_ACCESS_KEY_ID', '')
        source_password = getattr(settings, 'TEST_AWS_SECRET_ACCESS_KEY', '')
        source_regions = getattr(settings, 'TEST_AWS_REGIONS', 'all')
        if not all([source_username, source_password]):
            self.skipTest('no test ec2 credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='aws',
                                               username=source_username,
                                               password=source_password)
        credential.admin_role.members.add(self.super_django_user)
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
        #self.print_inventory_tree(self.inventory)
        child_names = self.group.children.values_list('name', flat=True)
        for name in child_names:
            self.assertFalse(name.startswith('us-'))
            self.assertFalse(name.startswith('type_'))
            self.assertFalse(name.startswith('key_'))
            self.assertFalse(name.startswith('security_group_'))
            self.assertFalse(re.search(r'tag_.*?_', name))
            self.assertFalse(name.startswith('ami-'))
            self.assertFalse(name.startswith('vpc-'))
        self.assertTrue('ec2' in child_names)
        self.assertTrue('regions' in child_names)
        self.assertTrue('types' in child_names)
        self.assertTrue('keys' in child_names)
        self.assertTrue('security_groups' in child_names)
        self.assertTrue('tags' in child_names)
        self.assertTrue('images' in child_names)
        self.assertFalse('tag_none' in child_names)
        # Only check for tag_none as a child of tags if there is a tag_none group;
        # the test inventory *may* have tags set for all hosts.
        if self.inventory.groups.filter(name='tag_none').exists():
            self.assertTrue('tag_none' in self.group.children.get(name='tags').children.values_list('name', flat=True))
        self.assertFalse('instances' in child_names)
        # Make sure we clean up the cache path when finished (when one is not
        # provided explicitly via source_vars).
        new_cache_paths = set(glob.glob(cache_path_pattern))
        self.assertEqual(old_cache_paths, new_cache_paths)
        # Sync again with group_by set to a non-empty value.
        cache_path = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path)
        inventory_source.group_by = 'region,instance_type'
        inventory_source.source_vars = '---\n\ncache_path: %s\n' % cache_path
        inventory_source.overwrite = True
        inventory_source.save()
        self.check_inventory_source(inventory_source, initial=False)
        # Verify that only the desired groups are returned.
        child_names = self.group.children.values_list('name', flat=True)
        self.assertTrue('ec2' in child_names)
        self.assertTrue('regions' in child_names)
        self.assertTrue(self.group.children.get(name='regions').children.count())
        self.assertTrue('types' in child_names)
        self.assertTrue(self.group.children.get(name='types').children.count())
        self.assertFalse('keys' in child_names)
        self.assertFalse('security_groups' in child_names)
        self.assertFalse('tags' in child_names)
        self.assertFalse('images' in child_names)
        self.assertFalse('vpcs' in child_names)
        self.assertFalse('instances' in child_names)
        # Sync again with group_by set to include all possible groups.
        cache_path2 = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path2)
        inventory_source.group_by = 'instance_id, region, availability_zone, ami_id, instance_type, key_pair, vpc_id, security_group, tag_keys, tag_none'
        inventory_source.source_vars = '---\n\ncache_path: %s\n' % cache_path2
        inventory_source.overwrite = True
        inventory_source.save()
        self.check_inventory_source(inventory_source, initial=False, instance_id_group_ok=True)
        # Verify that only the desired groups are returned.
        # Skip vpcs as selected inventory may or may not have any.
        child_names = self.group.children.values_list('name', flat=True)
        self.assertTrue('ec2' in child_names)
        self.assertFalse('tag_none' in child_names)
        self.assertTrue('regions' in child_names)
        self.assertTrue(self.group.children.get(name='regions').children.count())
        self.assertTrue('types' in child_names)
        self.assertTrue(self.group.children.get(name='types').children.count())
        self.assertTrue('keys' in child_names)
        self.assertTrue(self.group.children.get(name='keys').children.count())
        self.assertTrue('security_groups' in child_names)
        self.assertTrue(self.group.children.get(name='security_groups').children.count())
        self.assertTrue('tags' in child_names)
        self.assertTrue(self.group.children.get(name='tags').children.count())
        # Only check for tag_none as a child of tags if there is a tag_none group;
        # the test inventory *may* have tags set for all hosts.
        if self.inventory.groups.filter(name='tag_none').exists():
            self.assertTrue('tag_none' in self.group.children.get(name='tags').children.values_list('name', flat=True))
        self.assertTrue('images' in child_names)
        self.assertTrue(self.group.children.get(name='images').children.count())
        self.assertTrue('instances' in child_names)
        self.assertTrue(self.group.children.get(name='instances').children.count())
        # Sync again with overwrite set to False after renaming a group that
        # was created by the sync.  With overwrite false, the renamed group and
        # the original group (created again by the sync) will both exist.
        region_group = self.group.children.get(name='regions').children.all()[0]
        region_group_original_name = region_group.name
        region_group.name = region_group.name + '-renamed'
        region_group.save(update_fields=['name'])
        cache_path3 = tempfile.mkdtemp(prefix='awx_ec2_')
        self._temp_paths.append(cache_path3)
        inventory_source.source_vars = '---\n\ncache_path: %s\n' % cache_path3
        inventory_source.overwrite = False
        inventory_source.save()
        self.check_inventory_source(inventory_source, initial=False, instance_id_group_ok=True)
        child_names = self.group.children.values_list('name', flat=True)
        self.assertTrue(region_group_original_name in self.group.children.get(name='regions').children.values_list('name', flat=True))
        self.assertTrue(region_group.name in self.group.children.get(name='regions').children.values_list('name', flat=True))
        # Replacement text should not be left in inventory source name.
        self.assertFalse(InventorySource.objects.filter(name__icontains='__replace_').exists())
        # Inventory update name should be based on inventory/group names and need not have the inventory source pk.
        #print InventoryUpdate.objects.values_list('name', 'inventory_source__name')
        for inventory_update in InventoryUpdate.objects.all():
            self.assertFalse(inventory_update.name.endswith(inventory_update.inventory_source.name), inventory_update.name)

    def test_update_from_rax(self):
        self.skipTest('Skipping until we can resolve the CERTIFICATE_VERIFY_FAILED issue: #1706')
        source_username = getattr(settings, 'TEST_RACKSPACE_USERNAME', '')
        source_password = getattr(settings, 'TEST_RACKSPACE_API_KEY', '')
        source_regions = getattr(settings, 'TEST_RACKSPACE_REGIONS', '')
        if not all([source_username, source_password]):
            self.skipTest('no test rackspace credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='rax',
                                               username=source_username,
                                               password=source_password)
        credential.admin_role.members.add(self.super_django_user)
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

    def test_update_from_vmware(self):
        source_host = getattr(settings, 'TEST_VMWARE_HOST', '')
        source_username = getattr(settings, 'TEST_VMWARE_USER', '')
        source_password = getattr(settings, 'TEST_VMWARE_PASSWORD', '')
        if not all([source_host, source_username, source_password]):
            self.skipTest('no test vmware credentials defined!')
        self.create_test_license_file()
        credential = Credential.objects.create(kind='vmware',
                                               username=source_username,
                                               password=source_password,
                                               host=source_host)
        credential.admin_role.members.add(self.super_django_user)
        inventory_source = self.update_inventory_source(self.group,
                                                        source='vmware', credential=credential)
        # Check first without instance_id set (to import by name only).
        with self.settings(VMWARE_INSTANCE_ID_VAR=''):
            self.check_inventory_source(inventory_source)
        # Rename hosts and verify the import picks up the instance_id present
        # in host variables.
        for host in self.inventory.hosts.all():
            self.assertFalse(host.instance_id, host.instance_id)
            if host.enabled and host.variables_dict.get('vmware_ipAddress', ''):
                self.assertTrue(host.variables_dict.get('ansible_ssh_host', ''))
            # Test a field that should be present for host systems, not VMs.
            self.assertFalse(host.variables_dict.get('vmware_product_name', ''))
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
        # Update again and include host systems in addition to guests.
        inventory_source.source_vars = '---\n\nguests_only: false\n'
        inventory_source.save()
        old_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.check_inventory_source(inventory_source, initial=False)
        new_host_pks = set(self.inventory.hosts.values_list('pk', flat=True))
        self.assertTrue(new_host_pks > old_host_pks)
        for host in self.inventory.hosts.filter(pk__in=(new_host_pks - old_host_pks)):
            if host.enabled:
                self.assertTrue(host.variables_dict.get('ansible_ssh_host', ''))
            # Test a field only present for host systems.
            self.assertTrue(host.variables_dict.get('vmware_product_name', ''))

    def test_update_from_custom_script(self):
        # Create the inventory script
        self.create_test_license_file()
        inventory_scripts = reverse('api:inventory_script_list')
        new_script = dict(name="Test", description="Test Script", script=TEST_SIMPLE_INVENTORY_SCRIPT, organization=self.organization.id)
        script_data = self.post(inventory_scripts, data=new_script, expect=201, auth=self.get_super_credentials())

        custom_inv = self.organization.inventories.create(name='Custom Script Inventory')
        custom_group = custom_inv.groups.create(name="Custom Script Group")
        custom_inv_src = reverse('api:inventory_source_detail',
                                 args=(custom_group.inventory_source.pk,))
        reverse('api:inventory_source_update_view',
                args=(custom_group.inventory_source.pk,))
        inv_src_opts = {'source': 'custom',
                        'source_script': script_data["id"],
                        'source_vars': json.dumps({'HOME': 'no-place-like', 'USER': 'notme', '_': 'nope', 'INVENTORY_SOURCE_ID': -1})
                        }
        with self.current_user(self.super_django_user):
            self.put(custom_inv_src, inv_src_opts, expect=200)
        self.check_inventory_source(custom_group.inventory_source)

        # Delete script, verify that update fails.
        inventory_source = InventorySource.objects.get(pk=custom_group.inventory_source.pk)
        self.assertTrue(inventory_source.can_update)
        self.delete(script_data['url'], expect=204, auth=self.get_super_credentials())
        inventory_source = InventorySource.objects.get(pk=inventory_source.pk)
        self.assertFalse(inventory_source.can_update)
        self.check_inventory_update(inventory_source, should_fail=True)

        # Test again using a script containing some funky unicode gibberish.
        unicode_script = dict(name="Unicodes", description="", script=TEST_UNICODE_INVENTORY_SCRIPT, organization=self.organization.id)
        script_data = self.post(inventory_scripts, data=unicode_script, expect=201, auth=self.get_super_credentials())

        custom_inv = self.organization.inventories.create(name='Unicode Script Inventory')
        custom_group = custom_inv.groups.create(name="Unicode Script Group")
        custom_inv_src = reverse('api:inventory_source_detail',
                                 args=(custom_group.inventory_source.pk,))
        reverse('api:inventory_source_update_view',
                args=(custom_group.inventory_source.pk,))
        inv_src_opts = {'source': 'custom', 'source_script': script_data["id"]}
        with self.current_user(self.super_django_user):
            self.put(custom_inv_src, inv_src_opts, expect=200)
        self.check_inventory_source(custom_group.inventory_source)

        # This shouldn't work because we are trying to use a custom script from one organization with
        # an inventory that belong to a different organization
        other_org = self.make_organizations(self.super_django_user, 1)[0]
        other_inv = other_org.inventories.create(name="A Different Org")
        other_group = other_inv.groups.create(name='A Different Org Group')
        other_inv_src = reverse('api:inventory_source_detail',
                                args=(other_group.inventory_source.pk,))
        reverse('api:inventory_source_update_view',
                args=(other_group.inventory_source.pk,))
        other_inv_src_opts = {'source': 'custom', 'source_script': script_data['id']}
        with self.current_user(self.super_django_user):
            self.put(other_inv_src, other_inv_src_opts, expect=400)

    def test_update_expired_license(self):
        self.create_test_license_file(license_date=int(time.time() - 3600))
        inventory_scripts = reverse('api:inventory_script_list')
        new_script = dict(name="Test", description="Test Script", script=TEST_SIMPLE_INVENTORY_SCRIPT, organization=self.organization.id)
        script_data = self.post(inventory_scripts, data=new_script, expect=201, auth=self.get_super_credentials())

        custom_inv = self.organization.inventories.create(name='Custom Script Inventory')
        custom_group = custom_inv.groups.create(name="Custom Script Group")
        custom_inv_src = reverse('api:inventory_source_detail',
                                 args=(custom_group.inventory_source.pk,))
        reverse('api:inventory_source_update_view',
                args=(custom_group.inventory_source.pk,))
        inv_src_opts = {'source': 'custom',
                        'source_script': script_data["id"],
                        'source_vars': json.dumps({'HOME': 'no-place-like', 'USER': 'notme', '_': 'nope', 'INVENTORY_SOURCE_ID': -1})
                        }
        with self.current_user(self.super_django_user):
            response = self.put(custom_inv_src, inv_src_opts, expect=200)

        inventory_source = InventorySource.objects.get(pk=response['id'])
        inventory_update = inventory_source.update(inventory_source=inventory_source)
        self.assertFalse(inventory_update.license_error)

    def test_update_from_openstack(self):
        api_url = getattr(settings, 'TEST_OPENSTACK_HOST', '')
        api_user = getattr(settings, 'TEST_OPENSTACK_USER', '')
        api_password = getattr(settings, 'TEST_OPENSTACK_PASSWORD', '')
        api_project = getattr(settings, 'TEST_OPENSTACK_PROJECT', '')
        if not all([api_url, api_user, api_password, api_project]):
            self.skipTest("No test openstack credentials defined")
        self.create_test_license_file()
        credential = Credential.objects.create(kind='openstack',
                                               host=api_url,
                                               username=api_user,
                                               password=api_password,
                                               project=api_project)
        inventory_source = self.update_inventory_source(self.group, source='openstack', credential=credential)
        self.check_inventory_source(inventory_source)
        self.assertFalse(self.group.all_hosts.filter(instance_id='').exists())

    def test_update_from_openstack_with_domain(self):
        # Check that update works with Keystone v3 identity service
        api_url = getattr(settings, 'TEST_OPENSTACK_HOST_V3', '')
        api_user = getattr(settings, 'TEST_OPENSTACK_USER', '')
        api_password = getattr(settings, 'TEST_OPENSTACK_PASSWORD', '')
        api_project = getattr(settings, 'TEST_OPENSTACK_PROJECT', '')
        api_domain = getattr(settings, 'TEST_OPENSTACK_DOMAIN', '')
        if not all([api_url, api_user, api_password, api_project, api_domain]):
            self.skipTest("No test openstack credentials defined with a domain")
        self.create_test_license_file()
        credential = Credential.objects.create(kind='openstack',
                                               host=api_url,
                                               username=api_user,
                                               password=api_password,
                                               project=api_project,
                                               domain=api_domain)
        inventory_source = self.update_inventory_source(self.group, source='openstack', credential=credential)
        self.check_inventory_source(inventory_source)
        self.assertFalse(self.group.all_hosts.filter(instance_id='').exists())

    def test_update_from_azure(self):
        source_username = getattr(settings, 'TEST_AZURE_USERNAME', '')
        source_key_data = getattr(settings, 'TEST_AZURE_KEY_DATA', '')
        if not all([source_username, source_key_data]):
            self.skipTest("No test azure credentials defined")
        self.create_test_license_file()
        credential = Credential.objects.create(kind='azure',
                                               username=source_username,
                                               ssh_key_data=source_key_data)
        inventory_source = self.update_inventory_source(self.group, source='azure', credential=credential)
        self.check_inventory_source(inventory_source)
        self.assertFalse(self.group.all_hosts.filter(instance_id='').exists())

