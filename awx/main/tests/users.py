# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import json
import urllib

# Django
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models import Q
import django.test
from django.test.client import Client
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTest

__all__ = ['UsersTest', 'LdapTest']

class UsersTest(BaseTest):

    def collection(self):
        return reverse('api:user_list')

    def setUp(self):
        super(UsersTest, self).setUp()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 2)
        self.organizations[0].admins.add(self.normal_django_user)
        self.organizations[0].users.add(self.other_django_user)
        self.organizations[0].users.add(self.normal_django_user)
        self.organizations[1].users.add(self.other_django_user)
 
    def test_only_super_user_or_org_admin_can_add_users(self):
        url = reverse('api:user_list')
        new_user = dict(username='blippy')
        new_user2 = dict(username='blippy2')
        self.post(url, expect=401, data=new_user, auth=None)
        self.post(url, expect=401, data=new_user, auth=self.get_invalid_credentials())
        self.post(url, expect=403, data=new_user, auth=self.get_other_credentials())
        self.post(url, expect=201, data=new_user, auth=self.get_super_credentials())
        self.post(url, expect=400, data=new_user, auth=self.get_super_credentials())
        self.post(url, expect=201, data=new_user2, auth=self.get_normal_credentials())
        self.post(url, expect=400, data=new_user2, auth=self.get_normal_credentials())

    def test_auth_token_login(self):
        auth_token_url = reverse('api:auth_token_view')
        user_me_url = reverse('api:user_me_list')

        # Always returns a 405 for any GET request, regardless of credentials.
        self.get(auth_token_url, expect=405, auth=None)
        self.get(auth_token_url, expect=405, auth=self.get_invalid_credentials())
        self.get(auth_token_url, expect=405, auth=self.get_normal_credentials())
        
        # Posting without username/password fields or invalid username/password
        # returns a 400 error.
        data = {}
        self.post(auth_token_url, data, expect=400)
        data = dict(zip(('username', 'password'), self.get_invalid_credentials()))
        self.post(auth_token_url, data, expect=400)

        # A valid username/password should give us an auth token.
        data = dict(zip(('username', 'password'), self.get_normal_credentials()))
        response = self.post(auth_token_url, data, expect=200, auth=None)
        self.assertTrue('token' in response)
        self.assertTrue('expires' in response)
        self.assertEqual(response['token'], self.normal_django_user.auth_tokens.all()[0].key)
        auth_token = response['token']

        # Verify we can access our own user information with the auth token.
        response = self.get(user_me_url, expect=200, auth=auth_token)
        self.assertEquals(response['results'][0]['username'], 'normal')
        self.assertEquals(response['count'], 1)

        # If basic auth is passed via the Authorization header and the UI also
        # passes token auth via the X-Auth-Token header, the API should favor
        # the X-Auth-Token value.
        mixed_auth = {
            'basic': self.get_super_credentials(),
            'token': auth_token,
        }
        response = self.get(user_me_url, expect=200, auth=mixed_auth)
        self.assertEquals(response['results'][0]['username'], 'normal')
        self.assertEquals(response['count'], 1)

        # If we simulate a different remote address, should not be able to use
        # the first auth token.
        remote_addr = '127.0.0.2'
        response = self.get(user_me_url, expect=401, auth=auth_token,
                            remote_addr=remote_addr)
        self.assertEqual(response['detail'], 'Invalid token')

        # The WWW-Authenticate header should specify Token auth, since that
        # auth method was used in the request.
        response_header = response.response.get('WWW-Authenticate', '')
        self.assertEqual(response_header.split()[0], 'Token')
        
        # Request a new auth token from the new remote address.
        data = dict(zip(('username', 'password'), self.get_normal_credentials()))
        response = self.post(auth_token_url, data, expect=200, auth=None,
                             remote_addr=remote_addr)
        self.assertTrue('token' in response)
        self.assertTrue('expires' in response)
        self.assertEqual(response['token'], self.normal_django_user.auth_tokens.all()[1].key)
        auth_token2 = response['token']

        # Verify we can access our own user information with the second auth
        # token from the other remote address.
        response = self.get(user_me_url, expect=200, auth=auth_token2,
                            remote_addr=remote_addr)
        self.assertEquals(response['results'][0]['username'], 'normal')
        self.assertEquals(response['count'], 1)

        # The second auth token also can't be used from the first address, but
        # the first auth token is still valid from its address.
        response = self.get(user_me_url, expect=401, auth=auth_token2)
        self.assertEqual(response['detail'], 'Invalid token')
        response_header = response.response.get('WWW-Authenticate', '')
        self.assertEqual(response_header.split()[0], 'Token')
        response = self.get(user_me_url, expect=200, auth=auth_token)

        # A request without authentication should ask for Basic by default.
        response = self.get(user_me_url, expect=401)
        response_header = response.response.get('WWW-Authenticate', '')
        self.assertEqual(response_header.split()[0], 'Basic')
        
        # A request that attempts Basic auth should request Basic auth again.
        response = self.get(user_me_url, expect=401,
                            auth=('invalid', 'password'))
        response_header = response.response.get('WWW-Authenticate', '')
        self.assertEqual(response_header.split()[0], 'Basic')

        # Invalidate a key (simulate expiration), now token auth should fail
        # with the first token, but still work with the second.
        self.normal_django_user.auth_tokens.get(key=auth_token).invalidate()
        response = self.get(user_me_url, expect=401, auth=auth_token)
        self.assertEqual(response['detail'], 'Token is expired')
        response = self.get(user_me_url, expect=200, auth=auth_token2,
                            remote_addr=remote_addr)

        # Token auth should be denied if the user is inactive.
        self.normal_django_user.mark_inactive()
        response = self.get(user_me_url, expect=401, auth=auth_token2,
                            remote_addr=remote_addr)
        self.assertEqual(response['detail'], 'User inactive or deleted')

    def test_ordinary_user_can_modify_some_fields_about_himself_but_not_all_and_passwords_work(self):

        detail_url = reverse('api:user_detail', args=(self.other_django_user.pk,))
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

        # this is something an org admin can do...
        url = reverse('api:user_list')
        data  = dict(username='username',  password='password')
        data2 = dict(username='username2', password='password2')
        data = self.post(url, expect=201, data=data, auth=self.get_normal_credentials())

        # verify that the login works...
        self.get(url, expect=200, auth=('username', 'password'))

        # but a regular user cannot        
        data = self.post(url, expect=403, data=data2, auth=self.get_other_credentials())
        
        # a super user can also create new users   
        data = self.post(url, expect=201, data=data2, auth=self.get_super_credentials())

        # verify that the login works
        self.get(url, expect=200, auth=('username2', 'password2'))

        # verify that if you post a user with a pk, you do not alter that user's password info
        mod = dict(id=self.super_django_user.pk, username='change', password='change')
        data = self.post(url, expect=201, data=mod, auth=self.get_super_credentials())
        orig = User.objects.get(pk=self.super_django_user.pk)
        self.assertTrue(orig.username != 'change')
 
    def test_password_not_shown_in_get_operations_for_list_or_detail(self):
        url = reverse('api:user_detail', args=(self.super_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertTrue('password' not in data)

        url = reverse('api:user_list')
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertTrue('password' not in data['results'][0])

    def test_user_list_filtered(self):
        url = reverse('api:user_list')
        data3 = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data3['count'], 4)
        # Normal user is an org admin, can see all users.
        data2 = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data2['count'], 4)
        data1 = self.get(url, expect=200, auth=self.get_other_credentials())
        self.assertEquals(data1['count'], 2)

    def test_super_user_can_delete_a_user_but_only_marked_inactive(self):
        user_pk = self.normal_django_user.pk
        url = reverse('api:user_detail', args=(user_pk,))
        data = self.delete(url, expect=204, auth=self.get_super_credentials())
        data = self.get(url, expect=404, auth=self.get_super_credentials())
        obj = User.objects.get(pk=user_pk)
        self.assertEquals(obj.is_active, False)
 
    def test_non_org_admin_user_cannot_delete_any_user_including_himself(self):
        url1 = reverse('api:user_detail', args=(self.super_django_user.pk,))
        url2 = reverse('api:user_detail', args=(self.normal_django_user.pk,))
        url3 = reverse('api:user_detail', args=(self.other_django_user.pk,))
        data = self.delete(url1, expect=403, auth=self.get_other_credentials())
        data = self.delete(url2, expect=403, auth=self.get_other_credentials())
        data = self.delete(url3, expect=403, auth=self.get_other_credentials())

    def test_there_exists_an_obvious_url_where_a_user_may_find_his_user_record(self):
        url = reverse('api:user_me_list')
        data = self.get(url, expect=401, auth=None)
        data = self.get(url, expect=401, auth=self.get_invalid_credentials())
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['results'][0]['username'], 'normal')
        self.assertEquals(data['count'], 1)
        data = self.get(url, expect=200, auth=self.get_other_credentials())
        self.assertEquals(data['results'][0]['username'], 'other')
        self.assertEquals(data['count'], 1)
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['results'][0]['username'], 'admin')
        self.assertEquals(data['count'], 1)

    def test_superuser_can_change_admin_only_fields_about_himself(self):
        url = reverse('api:user_detail', args=(self.super_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        data['username'] += '2'
        data['first_name'] += ' Awesome'
        data['last_name'] += ', Jr.'
        response = self.put(url, data, expect=200,
                            auth=self.get_super_credentials())
        # FIXME: Test if super user mark himself as no longer a super user, or
        # delete himself.

    def test_user_related_resources(self):

        # organizations the user is a member of, should be 1
        url = reverse('api:user_organizations_list',
                      args=(self.normal_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 1) 
        # also accessible via superuser
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['count'], 1) 
        # and also by other user... 
        data = self.get(url, expect=200, auth=self.get_other_credentials())
        # but not by nobody user
        data = self.get(url, expect=403, auth=self.get_nobody_credentials())

        # organizations the user is an admin of, should be 1
        url = reverse('api:user_admin_of_organizations_list',
                      args=(self.normal_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 1)
        # also accessible via superuser
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['count'], 1)
        # and also by other user
        data = self.get(url, expect=200, auth=self.get_other_credentials())
        # but not by nobody user
        data = self.get(url, expect=403, auth=self.get_nobody_credentials())
 
        # teams the user is on, should be 0
        url = reverse('api:user_teams_list', args=(self.normal_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 0)
        # also accessible via superuser
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data['count'], 0)
        # and also by other user
        data = self.get(url, expect=200, auth=self.get_other_credentials())
        # but not by nobody user
        data = self.get(url, expect=403, auth=self.get_nobody_credentials())

        # verify org admin can still read other user data too
        url = reverse('api:user_organizations_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 1)
        url = reverse('api:user_admin_of_organizations_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 0)
        url = reverse('api:user_teams_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 0)

        # FIXME: add test that shows posting a user w/o id to /organizations/2/users/ can create a new one & associate
        # FIXME: add test that shows posting a user w/o id to /organizations/2/admins/ can create a new one & associate
        # FIXME: add test that shows posting a projects w/o id to /organizations/2/projects/ can create a new one & associate

    def test_user_list_ordering(self):
        base_url = reverse('api:user_list')
        base_qs = User.objects.distinct()

        # Check list view with ordering by name.
        url = '%s?order_by=username' % base_url
        qs = base_qs.order_by('username')
        self.check_get_list(url, self.super_django_user, qs, check_order=True)

        # Check list view with ordering by username in reverse.
        url = '%s?order=-username' % base_url
        qs = base_qs.order_by('-username')
        self.check_get_list(url, self.super_django_user, qs, check_order=True)

        # Check list view with multiple ordering fields.
        url = '%s?order_by=-pk,username' % base_url
        qs = base_qs.order_by('-pk', 'username')
        self.check_get_list(url, self.super_django_user, qs, check_order=True)

        # Check list view with invalid field name.
        url = '%s?order_by=invalidfieldname' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Check list view with no field name.
        url = '%s?order_by=' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

    def test_user_list_filtering(self):
        # Also serves as general-purpose testing for custom API filters.
        base_url = reverse('api:user_list')
        base_qs = User.objects.distinct()

        # Filter by username.
        url = '%s?username=normal' % base_url
        qs = base_qs.filter(username='normal')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __exact suffix.
        url = '%s?username__exact=normal' % base_url
        qs = base_qs.filter(username__exact='normal')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        
        # Filter by username with __iexact suffix.
        url = '%s?username__iexact=NORMAL' % base_url
        qs = base_qs.filter(username__iexact='NORMAL')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __contains suffix.
        url = '%s?username__contains=dmi' % base_url
        qs = base_qs.filter(username__contains='dmi')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __icontains suffix.
        url = '%s?username__icontains=DMI' % base_url
        qs = base_qs.filter(username__icontains='DMI')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __startswith suffix.
        url = '%s?username__startswith=no' % base_url
        qs = base_qs.filter(username__startswith='no')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __istartswith suffix.
        url = '%s?username__istartswith=NO' % base_url
        qs = base_qs.filter(username__istartswith='NO')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __endswith suffix.
        url = '%s?username__endswith=al' % base_url
        qs = base_qs.filter(username__endswith='al')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __iendswith suffix.
        url = '%s?username__iendswith=AL' % base_url
        qs = base_qs.filter(username__iendswith='AL')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __regex suffix.
        url = '%s?username__regex=%s' % (base_url, urllib.quote_plus(r'^admin|no.+$'))
        qs = base_qs.filter(username__regex=r'^admin|no.+$')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by username with __iregex suffix.
        url = '%s?username__iregex=%s' % (base_url, urllib.quote_plus(r'^ADMIN|NO.+$'))
        qs = base_qs.filter(username__iregex=r'^ADMIN|NO.+$')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by invalid regex value.
        url = '%s?username__regex=%s' % (base_url, urllib.quote_plus('['))
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by multiple usernames (AND).
        url = '%s?username=normal&username=nobody' % base_url
        qs = base_qs.filter(username='normal', username__exact='nobody')
        self.assertFalse(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by multiple usernames (OR).
        url = '%s?or__username=normal&or__username=nobody' % base_url
        qs = base_qs.filter(Q(username='normal') | Q(username='nobody'))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Exclude by username.
        url = '%s?not__username=normal' % base_url
        qs = base_qs.exclude(username='normal')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Exclude by multiple usernames.
        url = '%s?not__username=normal&not__username=nobody' % base_url
        qs = base_qs.filter(~Q(username='normal') & ~Q(username='nobody'))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Exclude by multiple usernames with OR.
        url = '%s?or__not__username=normal&or__not__username=nobody' % base_url
        qs = base_qs.filter(~Q(username='normal') | ~Q(username='nobody'))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Exclude by username with suffix.
        url = '%s?not__username__startswith=no' % base_url
        qs = base_qs.exclude(username__startswith='no')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by multiple username specs.
        url = '%s?username__startswith=no&username__endswith=al' % base_url
        qs = base_qs.filter(username__startswith='no', username__endswith='al')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_superuser (when True).
        url = '%s?is_superuser=True' % base_url
        qs = base_qs.filter(is_superuser=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_superuser (when False).
        url = '%s?is_superuser=False' % base_url
        qs = base_qs.filter(is_superuser=False)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_superuser (when 1).
        url = '%s?is_superuser=1' % base_url
        qs = base_qs.filter(is_superuser=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_superuser (when 0).
        url = '%s?is_superuser=0' % base_url
        qs = base_qs.filter(is_superuser=False)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_superuser (when TRUE).
        url = '%s?is_superuser=TRUE' % base_url
        qs = base_qs.filter(is_superuser=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by invalid value for boolean field.
        url = '%s?is_superuser=notatbool' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by custom __int suffix on boolean field.
        url = '%s?is_superuser__int=1' % base_url
        qs = base_qs.filter(is_superuser=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by is_staff (field not exposed via API).  FIXME: Should 
        # eventually not be allowed!
        url = '%s?is_staff=true' % base_url
        qs = base_qs.filter(is_staff=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by pk/id
        url = '%s?pk=%d' % (base_url, self.normal_django_user.pk)
        qs = base_qs.filter(pk=self.normal_django_user.pk)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?id=%d' % (base_url, self.normal_django_user.pk)
        qs = base_qs.filter(id=self.normal_django_user.pk)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by pk gt/gte/lt/lte.
        url = '%s?pk__gt=0' % base_url
        qs = base_qs.filter(pk__gt=0)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?pk__gte=0' % base_url
        qs = base_qs.filter(pk__gt=0)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?pk__lt=999' % base_url
        qs = base_qs.filter(pk__lt=999)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?pk__lte=999' % base_url
        qs = base_qs.filter(pk__lte=999)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by invalid value for integer field.
        url = '%s?pk=notanint' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by int using custom __int suffix.
        url = '%s?pk__int=%d' % (base_url, self.super_django_user.pk)
        qs = base_qs.filter(pk=self.super_django_user.pk)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Verify difference between normal AND filter vs. filtering with
        # chain__ prefix.
        url = '%s?organizations__name__startswith=org0&organizations__name__startswith=org1' % base_url
        qs = base_qs.filter(Q(organizations__name__startswith='org0'),
                            Q(organizations__name__startswith='org1'))
        self.assertFalse(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?chain__organizations__name__startswith=org0&chain__organizations__name__startswith=org1' % base_url
        qs = base_qs.filter(organizations__name__startswith='org0')
        qs = qs.filter(organizations__name__startswith='org1')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by related organization not present.
        url = '%s?organizations=None' % base_url
        qs = base_qs.filter(organizations=None)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = '%s?organizations__isnull=true' % base_url
        qs = base_qs.filter(organizations__isnull=True)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by related organization present.
        url = '%s?organizations__isnull=0' % base_url
        qs = base_qs.filter(organizations__isnull=False)
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by related organizations name.
        url = '%s?organizations__name__startswith=org' % base_url
        qs = base_qs.filter(organizations__name__startswith='org')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by related organizations admins username.
        url = '%s?organizations__admins__username__startswith=norm' % base_url
        qs = base_qs.filter(organizations__admins__username__startswith='norm')
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        
        # Filter by username with __in list.
        url = '%s?username__in=normal,admin' % base_url
        qs = base_qs.filter(username__in=('normal', 'admin'))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by organizations with __in list.
        url = '%s?organizations__in=%d,0' % (base_url, self.organizations[0].pk)
        qs = base_qs.filter(organizations__in=(self.organizations[0].pk, 0))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Exclude by organizations with __in list.
        url = '%s?not__organizations__in=%d,0' % (base_url, self.organizations[0].pk)
        qs = base_qs.exclude(organizations__in=(self.organizations[0].pk, 0))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by organizations created timestamp (passing only a date).
        url = '%s?organizations__created__gt=2013-01-01' % base_url
        qs = base_qs.filter(organizations__created__gt=datetime.date(2013, 1, 1))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by organizations created timestamp (passing datetime).
        url = '%s?organizations__created__lt=%s' % (base_url, urllib.quote_plus('2037-03-07 12:34:56'))
        qs = base_qs.filter(organizations__created__lt=datetime.datetime(2037, 3, 7, 12, 34, 56))
        self.assertTrue(qs.count())
        self.check_get_list(url, self.super_django_user, qs)

        # Filter by organizations created timestamp (invalid datetime value).
        url = '%s?organizations__created__gt=yesterday' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by organizations created year (valid django lookup, but not
        # allowed via API).
        url = '%s?organizations__created__year=2013' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by invalid field.
        url = '%s?email_address=nobody@example.com' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by invalid field across lookups.
        url = '%s?organizations__users__teams__laser=green' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by invalid relation within lookups.
        url = '%s?organizations__users__llamas__name=freddie' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter by invalid query string field names.
        url = '%s?__' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)
        url = '%s?not__' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)
        url = '%s?__foo' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)
        url = '%s?username__' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)
        url = '%s?username+=normal' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

        # Filter with some unicode characters included in field name and value.
        url = u'%s?username=arrr\u2620' % base_url
        qs = base_qs.filter(username=u'arrr\u2620')
        self.assertFalse(qs.count())
        self.check_get_list(url, self.super_django_user, qs)
        url = u'%s?user\u2605name=normal' % base_url
        self.check_get_list(url, self.super_django_user, base_qs, expect=400)

    def test_user_list_pagination(self):
        base_url = reverse('api:user_list')
        base_qs = User.objects.distinct()

        # Check list view with page size of 1.
        url = '%s?order_by=username&page_size=1' % base_url
        qs = base_qs.order_by('username')
        self.check_get_list(url, self.super_django_user, qs, check_order=True,
                            limit=1)

        # Check list view with page size of 1, remaining pages.
        qs = base_qs.order_by('username')
        for n in xrange(1, base_qs.count()):
            url = '%s?order_by=username&page_size=1&page=%d' % (base_url, n+1)
            self.check_get_list(url, self.super_django_user, qs,
                                check_order=True, offset=n, limit=1)

        # Check list view with page size of 2.
        qs = base_qs.order_by('username')
        for n in xrange(0, base_qs.count(), 2):
            url = '%s?order_by=username&page_size=2&page=%d' % (base_url, (n/2)+1)
            self.check_get_list(url, self.super_django_user, qs,
                                check_order=True, offset=n, limit=2)

        # Check list view with page size of 0 (to allow getting count of items
        # matching a given filter). # FIXME: Make this work at some point!
        #url = '%s?order_by=username&page_size=0' % base_url
        #qs = base_qs.order_by('username')
        #self.check_get_list(url, self.super_django_user, qs, check_order=True,
        #                    limit=0)

    def test_user_list_searching(self):
        base_url = reverse('api:user_list')
        base_qs = User.objects.distinct()

        # Check search query parameter.
        url = '%s?search=no' % base_url
        qs = base_qs.filter(username__icontains='no')
        self.check_get_list(url, self.super_django_user, qs)

        # Check search query parameter.
        url = '%s?search=example' % base_url
        qs = base_qs.filter(email__icontains='example')
        self.check_get_list(url, self.super_django_user, qs)


class LdapTest(BaseTest):

    def use_test_setting(self, name, default=None, from_name=None):
        from_name = from_name or name
        setattr(settings, 'AUTH_LDAP_%s' % name,
                getattr(settings, 'TEST_AUTH_LDAP_%s' % from_name, default))

    def setUp(self):
        super(LdapTest, self).setUp()
        # Skip tests if basic LDAP test settings aren't defined.
        if not getattr(settings, 'TEST_AUTH_LDAP_SERVER_URI', None):
            self.skipTest('no test LDAP auth server defined')
        self.ldap_username = getattr(settings, 'TEST_AUTH_LDAP_USERNAME', None)
        if not self.ldap_username:
            self.skipTest('no test LDAP username defined')
        self.ldap_password = getattr(settings, 'TEST_AUTH_LDAP_PASSWORD', None)
        if not self.ldap_password:
            self.skipTest('no test LDAP password defined')
        # Set test LDAP settings that are always needed.
        for name in ('SERVER_URI', 'BIND_DN', 'BIND_PASSWORD', 'USE_TLS'):
            self.use_test_setting(name)

    def check_login(self, username=None, password=None, should_fail=False):
        self.assertEqual(Group.objects.count(), 0)
        username = username or self.ldap_username
        password = password or self.ldap_password
        result = self.client.login(username=username, password=password)
        self.assertNotEqual(result, should_fail)
        self.assertEqual(Group.objects.count(), 0)
        if not should_fail:
            user = User.objects.get(username=username)
            self.assertTrue(user.profile)
            self.assertTrue(user.profile.ldap_dn)
            return user

    def test_ldap_auth(self):
        self.use_test_setting('USER_SEARCH')
        self.use_test_setting('ALWAYS_UPDATE_USER')
        self.assertEqual(User.objects.filter(username=self.ldap_username).count(), 0)
        # Test logging in, user should be created with no flags or fields set.
        user = self.check_login()
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.first_name)
        self.assertFalse(user.last_name)
        self.assertFalse(user.email)
        # Test logging in with bad username or password.
        self.check_login(username='not a valid user', should_fail=True)
        self.check_login(password='not a valid pass', should_fail=True)
        # Test using a flat DN instead of user search.
        self.use_test_setting('USER_DN_TEMPLATE', None)
        if settings.AUTH_LDAP_USER_DN_TEMPLATE:
            user = self.check_login()
            del settings.AUTH_LDAP_USER_DN_TEMPLATE
        # Test user attributes assigned from LDAP.
        self.use_test_setting('USER_ATTR_MAP', {})
        if settings.AUTH_LDAP_USER_ATTR_MAP:
            user = self.check_login()
            for attr in settings.AUTH_LDAP_USER_ATTR_MAP.keys():
                self.assertTrue(getattr(user, attr))
        # Turn on group search fields.
        for name in ('GROUP_SEARCH', 'GROUP_TYPE'):
            self.use_test_setting(name)
        # Test that user must be in required group.
        self.use_test_setting('REQUIRE_GROUP', from_name='REQUIRE_GROUP_FAIL')
        if settings.AUTH_LDAP_REQUIRE_GROUP:
            user = self.check_login(should_fail=True)
        self.use_test_setting('REQUIRE_GROUP')
        user = self.check_login()
        # Test that user must not be in deny group.
        self.use_test_setting('DENY_GROUP', from_name='DENY_GROUP_FAIL')
        if settings.AUTH_LDAP_DENY_GROUP:
            user = self.check_login(should_fail=True)
        self.use_test_setting('DENY_GROUP')
        user = self.check_login()
        # Check that user flags are set from group membership.
        self.use_test_setting('USER_FLAGS_BY_GROUP')
        if settings.AUTH_LDAP_USER_FLAGS_BY_GROUP:
            user = self.check_login()
            for attr in settings.AUTH_LDAP_USER_FLAGS_BY_GROUP.keys():
                self.assertTrue(getattr(user, attr))

    def test_ldap_organization_mapping(self):
        for name in ('USER_SEARCH', 'ALWAYS_UPDATE_USER', 'USER_ATTR_MAP',
                     'GROUP_SEARCH', 'GROUP_TYPE', 'USER_FLAGS_BY_GROUP'):
            self.use_test_setting(name)
        self.assertEqual(User.objects.filter(username=self.ldap_username).count(), 0)
        self.use_test_setting('ORGANIZATION_MAP', {})
        self.use_test_setting('ORGANIZATION_MAP_RESULT', {})
        for org_name in settings.AUTH_LDAP_ORGANIZATION_MAP.keys():
            self.assertEqual(Organization.objects.filter(name=org_name).count(), 0)
        user = self.check_login()
        for org_name in settings.AUTH_LDAP_ORGANIZATION_MAP.keys():
            self.assertEqual(Organization.objects.filter(name=org_name).count(), 1)
        for org_name, org_result in settings.AUTH_LDAP_ORGANIZATION_MAP_RESULT.items():
            org = Organization.objects.get(name=org_name)
            if org_result.get('admins', False):
                self.assertTrue(user in org.admins.all())
            else:
                self.assertFalse(user in org.admins.all())
            if org_result.get('users', False):
                self.assertTrue(user in org.users.all())
            else:
                self.assertFalse(user in org.users.all())
        # Try again with different test mapping.
        self.use_test_setting('ORGANIZATION_MAP', {},
                              from_name='ORGANIZATION_MAP_2')
        self.use_test_setting('ORGANIZATION_MAP_RESULT', {},
                              from_name='ORGANIZATION_MAP_2_RESULT')
        user = self.check_login()
        for org_name in settings.AUTH_LDAP_ORGANIZATION_MAP.keys():
            self.assertEqual(Organization.objects.filter(name=org_name).count(), 1)
        for org_name, org_result in settings.AUTH_LDAP_ORGANIZATION_MAP_RESULT.items():
            org = Organization.objects.get(name=org_name)
            if org_result.get('admins', False):
                self.assertTrue(user in org.admins.all())
            else:
                self.assertFalse(user in org.admins.all())
            if org_result.get('users', False):
                self.assertTrue(user in org.users.all())
            else:
                self.assertFalse(user in org.users.all())

    def test_prevent_changing_ldap_user_fields(self):
        for name in ('USER_SEARCH', 'ALWAYS_UPDATE_USER', 'USER_ATTR_MAP',
                     'GROUP_SEARCH', 'GROUP_TYPE', 'USER_FLAGS_BY_GROUP'):
            self.use_test_setting(name)
        user = self.check_login()
        self.setup_users()
        url = reverse('api:api_v1_config_view')
        with self.current_user(self.super_django_user):
            response = self.get(url, expect=200)
        user_ldap_fields = response.get('user_ldap_fields', [])
        self.assertTrue(user_ldap_fields)
        url = reverse('api:user_detail', args=(user.pk,))
        for user_field in user_ldap_fields:
            with self.current_user(self.super_django_user):
                data = self.get(url, expect=200)
            if user_field == 'password':
                data[user_field] = 'my new password'
                with self.current_user(self.super_django_user):
                    self.put(url, data, expect=200)
                user = User.objects.get(pk=user.pk)
                self.assertFalse(user.has_usable_password())
                #with self.current_user(self.super_django_user):
                #    self.patch(url, {'password': 'try again'}, expect=200)
                #user = User.objects.get(pk=user.pk)
                #self.assertFalse(user.has_usable_password())
            elif user_field in data:
                value = data[user_field]
                if isinstance(value, bool):
                    value = not value
                else:
                    value = unicode(value).upper()
                data[user_field] = value
                with self.current_user(self.super_django_user):
                    self.put(url, data, expect=400)
                #patch_data = {user_field: data[user_field]}
                #with self.current_user(self.super_django_user):
                #    self.patch(url, patch_data, expect=400)
