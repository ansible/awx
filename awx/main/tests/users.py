# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import json
import urllib

# Django
from django.contrib.auth.models import User
import django.test
from django.test.client import Client
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTest

class UsersTest(BaseTest):

    def collection(self):
        return reverse('main:user_list')

    def setUp(self):
        super(UsersTest, self).setUp()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 1)
        self.organizations[0].admins.add(self.normal_django_user)
        self.organizations[0].users.add(self.other_django_user)
        self.organizations[0].users.add(self.normal_django_user)
 
    def test_only_super_user_or_org_admin_can_add_users(self):
        url = reverse('main:user_list')
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
        auth_token_url = reverse('main:auth_token_view')

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
        result = self.post(auth_token_url, data, expect=200, auth=None)
        self.assertTrue('token' in result)
        self.assertEqual(result['token'], self.normal_django_user.auth_token.key)
        auth_token = result['token']

        # Verify we can access our own user information with the auth token.
        data = self.get(reverse('main:user_me_list'), expect=200, auth=auth_token)
        self.assertEquals(data['results'][0]['username'], 'normal')
        self.assertEquals(data['count'], 1)

    def test_ordinary_user_can_modify_some_fields_about_himself_but_not_all_and_passwords_work(self):

        detail_url = reverse('main:user_detail', args=(self.other_django_user.pk,))
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
        url = reverse('main:user_list')
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
        url = reverse('main:user_detail', args=(self.super_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertTrue('password' not in data)

        url = reverse('main:user_list')
        data = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertTrue('password' not in data['results'][0])

    def test_user_list_filtered(self):
        url = reverse('main:user_list')
        data3 = self.get(url, expect=200, auth=self.get_super_credentials())
        self.assertEquals(data3['count'], 4)
        data2 = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data2['count'], 2)
        data1 = self.get(url, expect=200, auth=self.get_other_credentials())
        self.assertEquals(data1['count'], 2)

    def test_super_user_can_delete_a_user_but_only_marked_inactive(self):
        user_pk = self.normal_django_user.pk
        url = reverse('main:user_detail', args=(user_pk,))
        data = self.delete(url, expect=204, auth=self.get_super_credentials())
        data = self.get(url, expect=404, auth=self.get_super_credentials())
        obj = User.objects.get(pk=user_pk)
        self.assertEquals(obj.is_active, False)
 
    def test_non_org_admin_user_cannot_delete_any_user_including_himself(self):
        url1 = reverse('main:user_detail', args=(self.super_django_user.pk,))
        url2 = reverse('main:user_detail', args=(self.normal_django_user.pk,))
        url3 = reverse('main:user_detail', args=(self.other_django_user.pk,))
        data = self.delete(url1, expect=403, auth=self.get_other_credentials())
        data = self.delete(url2, expect=403, auth=self.get_other_credentials())
        data = self.delete(url3, expect=403, auth=self.get_other_credentials())

    def test_there_exists_an_obvious_url_where_a_user_may_find_his_user_record(self):
        url = reverse('main:user_me_list')
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
        url = reverse('main:user_detail', args=(self.super_django_user.pk,))
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
        url = reverse('main:user_organizations_list',
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
        url = reverse('main:user_admin_of_organizations_list',
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
        url = reverse('main:user_teams_list', args=(self.normal_django_user.pk,))
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
        url = reverse('main:user_organizations_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 1)
        url = reverse('main:user_admin_of_organizations_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 0)
        url = reverse('main:user_teams_list',
                      args=(self.other_django_user.pk,))
        data = self.get(url, expect=200, auth=self.get_normal_credentials())
        self.assertEquals(data['count'], 0)

        # FIXME: add test that shows posting a user w/o id to /organizations/2/users/ can create a new one & associate
        # FIXME: add test that shows posting a user w/o id to /organizations/2/admins/ can create a new one & associate
        # FIXME: add test that shows posting a projects w/o id to /organizations/2/projects/ can create a new one & associate

    def test_user_list_ordering(self):
        base_url = reverse('main:user_list')
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
        base_url = reverse('main:user_list')
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

        # Exclude by username.
        url = '%s?not__username=normal' % base_url
        qs = base_qs.exclude(username='normal')
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
