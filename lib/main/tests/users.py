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
from lib.main.tests.base import BaseTest

class UsersTest(BaseTest):

    def collection(self):
        return '/api/v1/users/'

    def setUp(self):
        #self.object_ctr = 0
        self.setup_users(just_super_user=True)
 
    def test_only_super_user_can_add_users(self):
        self.assertTrue(False)
        pass

    def test_normal_user_can_modify_some_fields_about_himself_but_not_all(self):
        self.assertTrue(False)
        pass

    def test_normal_user_cannot_modify_another_user(self):
        self.assertTrue(False)
        pass

    def test_superuser_can_modify_anything_about_anyone(self):
        self.assertTrue(False)
        pass

    def test_password_not_shown_in_get_operations(self):
        self.assertTrue(False)
        pass

    def test_created_user_can_login(self):
        self.assertTrue(False)
        pass

    def test_user_list_filtered_for_non_admin_users(self):
        self.assertTrue(False)
        pass

    def test_user_list_non_filtered_for_admin_users(self):
        self.assertTrue(False)
        pass

    def test_super_user_can_delete_a_user_but_only_marked_inactive(self):
        self.assertTrue(False)
        pass
 
    def test_non_super_user_cannot_delete_any_user_including_himself(self):
        self.assertTrue(False)
        pass

    def test_there_exists_an_obvious_url_where_a_user_may_find_his_user_record(self):
        self.assertTrue(False)
        pass



