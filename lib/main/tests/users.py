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
        self.setup_users()
 
    def test_only_super_user_can_add_users(self):
        url = '/api/v1/users/'
        new_user = dict(username='blippy')
        self.post(url, expect=401, data=new_user, auth=None)
        self.post(url, expect=401, data=new_user, auth=self.get_invalid_credentials())
        self.post(url, expect=403, data=new_user, auth=self.get_normal_credentials())
        self.post(url, expect=403, data=new_user, auth=self.get_other_credentials())
        self.post(url, expect=201, data=new_user, auth=self.get_super_credentials())
        self.post(url, expect=400, data=new_user, auth=self.get_super_credentials())

    def test_ordinary_user_can_modify_some_fields_about_himself_but_not_all_and_passwords_work(self):

        detail_url = '/api/v1/users/%s/' % self.other_django_user.pk
        data = self.get(detail_url, expect=200, auth=self.get_other_credentials())

        # can't change first_name, last_name, etc
        data['last_name'] = "NewLastName"
        self.put(detail_url, data, expect=403, auth=self.get_other_credentials())

        # can't change username
        data['username'] = 'newUsername'
        self.put(detail_url, data, expect=403, auth=self.get_other_credentials())

        # if superuser, CAN change lastname and username and such
        self.put(detail_url, data, expect=200, auth=self.get_super_credentials())
        
        # and user can still login
        creds = self.get_other_credentials()
        creds = ('newUsername', creds[1])
        data = self.get(detail_url, expect=200, auth=creds)

        # user can change their password (submit as text) and can still login
        # and password is not stored as plaintext

        data['password'] = 'newPassWord1234Changed'
        changed = self.put(detail_url, data, expect=200, auth=creds)
        creds = (creds[0], data['password'])
        self.get(detail_url, expect=200, auth=creds)
       
        # make another nobody user, and make sure they can't send any edits
        obj = User.objects.create(username='new_user')
        obj.set_password('new_user')
        obj.save()
        hacked = dict(password='asdf')
        changed = self.put(detail_url, hacked, expect=403, auth=('new_user', 'new_user'))
        hacked = dict(username='asdf')
        changed = self.put(detail_url, hacked, expect=403, auth=('new_user', 'new_user'))

        # password is not stored in plaintext
        self.assertTrue(User.objects.get(pk=self.normal_django_user.pk).password != data['password'])

    def test_user_created_with_password_can_login(self):
        pass

    def test_normal_user_cannot_modify_another_user(self):
        #self.assertTrue(False)
        pass

    def test_superuser_can_modify_anything_about_anyone(self):
        #self.assertTrue(False)
        pass

    def test_password_not_shown_in_get_operations(self):
        #self.assertTrue(False)
        pass

    def test_user_list_filtered(self):
        # I can see a user if I'm on a team with them, am their org admin, am a superuser, or am them
        #self.assertTrue(False)
        pass

    def test_super_user_can_delete_a_user_but_only_marked_inactive(self):
        #self.assertTrue(False)
        pass
 
    def test_non_super_user_cannot_delete_any_user_including_himself(self):
        #self.assertTrue(False)
        pass

    def test_there_exists_an_obvious_url_where_a_user_may_find_his_user_record(self):
        #self.assertTrue(False)
        pass



