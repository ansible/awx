# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import json
import os
import re

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.timezone import now

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTest, BaseTransactionTest

__all__ = ['ScheduleTest']

UNTIL_SCHEDULE = "DTSTART:20140331T075000Z RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=30230401T075000Z"
EXPIRED_SCHEDULES = ["DTSTART:19340331T055000Z RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5"]
INFINITE_SCHEDULES = ["DTSTART:30340331T055000Z RRULE:FREQ=MINUTELY;INTERVAL=10"]
GOOD_SCHEDULES = ["DTSTART:20500331T055000Z RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
                  "DTSTART:20240331T075000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1",
                  "DTSTART:20140331T075000Z RRULE:FREQ=MINUTELY;INTERVAL=1;UNTIL=20230401T075000Z",
                  "DTSTART:20140331T075000Z RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR",
                  "DTSTART:20140331T075000Z RRULE:FREQ=WEEKLY;INTERVAL=5;BYDAY=MO",
                  "DTSTART:20140331T075000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=6",
                  "DTSTART:20140331T075000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYSETPOS=4;BYDAY=SU",
                  "DTSTART:20140331T075000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYSETPOS=-1;BYDAY=MO,TU,WE,TH,FR",
                  "DTSTART:20140331T075000Z RRULE:FREQ=MONTHLY;INTERVAL=1;BYSETPOS=-1;BYDAY=MO,TU,WE,TH,FR,SA,SU",
                  "DTSTART:20140331T075000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYMONTH=4;BYMONTHDAY=1",
                  "DTSTART:20140331T075000Z RRULE:FREQ=YEARLY;INTERVAL=1;BYSETPOS=-1;BYMONTH=8;BYDAY=SU",
                  "DTSTART:20140331T075000Z RRULE:FREQ=WEEKLY;INTERVAL=1;UNTIL=20230401T075000Z;BYDAY=MO,WE,FR",
                  "DTSTART:20140331T075000Z RRULE:FREQ=HOURLY;INTERVAL=1;UNTIL=20230610T075000Z",
                  "DTSTART:20140411T040000Z RRULE:FREQ=WEEKLY;INTERVAL=1;UNTIL=20140411T040000Z;BYDAY=WE"]
BAD_SCHEDULES = ["", "DTSTART:20140331T055000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
                 "RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
                 "FREQ=MINUTELY;INTERVAL=10;COUNT=5",
                 "DTSTART:20240331T075000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=10000000",
                 "DTSTART;TZID=US-Eastern:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
                 "DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY",
                 "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYDAY=20MO;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=MONTHLY;BYMONTHDAY=10,15;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYMONTH=1,2;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYYEARDAY=120;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYWEEKNO=10;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=HOURLY;INTERVAL=1 DTSTART:20140331T055000Z RRULE:FREQ=HOURLY;INTERVAL=1",
                 "DTSTART:20140331T055000Z RRULE:FREQ=HOURLY;INTERVAL=1 RRULE:FREQ=HOURLY;INTERVAL=1"]
class ScheduleTest(BaseTest):

    def setUp(self):
        super(ScheduleTest, self).setUp()
        self.start_redis()
        self.setup_instances()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 2)
        self.organizations[0].admins.add(self.normal_django_user)
        self.organizations[0].users.add(self.other_django_user)
        self.organizations[0].users.add(self.normal_django_user)

        self.diff_org_user = self.make_user('fred')
        self.organizations[1].users.add(self.diff_org_user)

        self.cloud_source = Credential.objects.create(kind='awx', user=self.super_django_user,
                                                      username='Dummy', password='Dummy')

        self.first_inventory = Inventory.objects.create(name='test_inventory', description='for org 0', organization=self.organizations[0])
        self.first_inventory.hosts.create(name='host_1')
        self.first_inventory_group = self.first_inventory.groups.create(name='group_1')
        self.first_inventory_source = self.first_inventory_group.inventory_source
        self.first_inventory_source.source = 'ec2'
        self.first_inventory_source.save()

        inv_read = Permission.objects.create(
            inventory       = self.first_inventory,
            user            = self.other_django_user,
            permission_type = 'read'
        )

        self.second_inventory = Inventory.objects.create(name='test_inventory_2', description='for org 0', organization=self.organizations[0])
        self.second_inventory.hosts.create(name='host_2')
        self.second_inventory_group = self.second_inventory.groups.create(name='group_2')
        self.second_inventory_source = self.second_inventory_group.inventory_source
        self.second_inventory_source.source = 'ec2'
        self.second_inventory_source.save()

        self.first_schedule = Schedule.objects.create(name='test_schedule_1', unified_job_template=self.first_inventory_source,
                                                      enabled=True, rrule=GOOD_SCHEDULES[0])
        self.second_schedule = Schedule.objects.create(name='test_schedule_2', unified_job_template=self.second_inventory_source,
                                                       enabled=True, rrule=GOOD_SCHEDULES[0])

        self.without_valid_source_inventory = Inventory.objects.create(name='without valid source', description='for org 0', organization=self.organizations[0])
        self.without_valid_source_inventory.hosts.create(name='host_3')
        self.without_valid_source_inventory_group = self.without_valid_source_inventory.groups.create(name='not valid source')
        self.without_valid_source_inventory_source = self.without_valid_source_inventory_group.inventory_source

    def tearDown(self):
        super(ScheduleTest, self).tearDown()
        self.stop_redis()

    def test_schedules_list(self):
        url = reverse('api:schedule_list')
        enabled_schedules = Schedule.objects.filter(enabled=True).distinct()
        empty_schedules = Schedule.objects.none()
        org_1_schedules = Schedule.objects.filter(unified_job_template=self.first_inventory_source)

        #Super user can see everything
        self.check_get_list(url, self.super_django_user, enabled_schedules)

        # Unauth user should have no access
        self.check_invalid_auth(url)

        # regular org user with read permission can see only their schedules
        self.check_get_list(url, self.other_django_user, org_1_schedules)

        # other org user with no read perm can't see anything
        self.check_get_list(url, self.diff_org_user, empty_schedules)

    def test_post_new_schedule(self):
        first_url = reverse('api:inventory_source_schedules_list', args=(self.first_inventory_source.pk,))
        second_url = reverse('api:inventory_source_schedules_list', args=(self.second_inventory_source.pk,))

        new_schedule = dict(name='newsched_1', description='newsched', enabled=True, rrule=GOOD_SCHEDULES[0])

        # No auth should fail
        self.check_invalid_auth(first_url, new_schedule, methods=('post',))

        # Super user can post a new schedule
        with self.current_user(self.super_django_user):
            data = self.post(first_url, data=new_schedule, expect=201)

        # #admin can post 
        admin_schedule = dict(name='newsched_2', description='newsched', enabled=True, rrule=GOOD_SCHEDULES[0])
        data = self.post(first_url, data=admin_schedule, expect=201, auth=self.get_normal_credentials())

        #normal user without write access can't post
        unauth_schedule = dict(name='newsched_3', description='newsched', enabled=True, rrule=GOOD_SCHEDULES[0])
        with self.current_user(self.other_django_user):
            data = self.post(first_url, data=unauth_schedule, expect=403)

        #give normal user write access and then they can post
        inv_write = Permission.objects.create(
            user = self.other_django_user,
            inventory = self.first_inventory,
            permission_type = PERM_INVENTORY_WRITE
        )
        auth_schedule = unauth_schedule
        with self.current_user(self.other_django_user):
            data = self.post(first_url, data=auth_schedule, expect=201)

        # another org user shouldn't be able to post a schedule to this org's schedule
        diff_user_schedule = dict(name='newsched_4', description='newsched', enabled=True, rrule=GOOD_SCHEDULES[0])
        with self.current_user(self.diff_org_user):
            data = self.post(first_url, data=diff_user_schedule, expect=403)

    def test_post_schedule_to_non_cloud_source(self):
        invalid_inv_url = reverse('api:inventory_source_schedules_list', args=(self.without_valid_source_inventory_source.pk,))
        new_schedule = dict(name='newsched_1', description='newsched', enabled=True, rrule=GOOD_SCHEDULES[0])

        with self.current_user(self.super_django_user):
            self.post(invalid_inv_url, data=new_schedule, expect=400)

    def test_update_existing_schedule(self):
        first_url = reverse('api:inventory_source_schedules_list', args=(self.first_inventory_source.pk,))

        new_schedule = dict(name='edit_schedule', description='going to change', enabled=True, rrule=EXPIRED_SCHEDULES[0])
        with self.current_user(self.normal_django_user):
            data = self.post(first_url, new_schedule, expect=201)
        self.assertEquals(data['next_run'], None)
        new_schedule_url = reverse('api:schedule_detail', args=(data['id'],))

        data['rrule'] = GOOD_SCHEDULES[0]
        with self.current_user(self.normal_django_user):
            data = self.put(new_schedule_url, data=data, expect=200)
        self.assertNotEqual(data['next_run'], None)
        #TODO: Test path needed for non org-admin users, but rather regular users who have permission to create the JT associated with the Schedule

    def test_infinite_schedule(self):
        first_url = reverse('api:inventory_source_schedules_list', args=(self.first_inventory_source.pk,))

        new_schedule = dict(name='inf_schedule', description='going forever', enabled=True, rrule=INFINITE_SCHEDULES[0])
        with self.current_user(self.normal_django_user):
            data = self.post(first_url, new_schedule, expect=201)
        self.assertEquals(data['dtend'], None)

        long_schedule = dict(name='long_schedule', description='going for a long time', enabled=True, rrule=UNTIL_SCHEDULE)
        with self.current_user(self.normal_django_user):
            data = self.post(first_url, long_schedule, expect=201)
        self.assertNotEquals(data['dtend'], None)
        
    def test_schedule_filtering(self):
        first_url = reverse('api:inventory_source_schedules_list', args=(self.first_inventory_source.pk,))

        start_time = now() + datetime.timedelta(minutes=5)
        dtstart_str = start_time.strftime("%Y%m%dT%H%M%SZ")
        new_schedule = dict(name="filter_schedule_1", enabled=True, rrule="DTSTART:%s RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5" % dtstart_str)
        with self.current_user(self.normal_django_user):
            data = self.post(first_url, new_schedule, expect=201)
        self.assertTrue(Schedule.objects.enabled().between(now(), now() + datetime.timedelta(minutes=10)).count(), 1)

        start_time = now()
        dtstart_str = start_time.strftime("%Y%m%dT%H%M%SZ")
        new_schedule_middle = dict(name="runnable_schedule", enabled=True, rrule="DTSTART:%s RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5" % dtstart_str)
        with self.current_user(self.normal_django_user):
            data = self.post(first_url, new_schedule_middle, expect=201)
        self.assertTrue(Schedule.objects.enabled().between(now() - datetime.timedelta(minutes=10), now() + datetime.timedelta(minutes=10)).count(), 1)

    def test_rrule_validation(self):
        first_url = reverse('api:inventory_source_schedules_list', args=(self.first_inventory_source.pk,))
        with self.current_user(self.normal_django_user):
            for good_rule in GOOD_SCHEDULES:
                sched_dict = dict(name=good_rule, enabled=True, rrule=good_rule)
                self.post(first_url, sched_dict, expect=201)
            for bad_rule in BAD_SCHEDULES:
                sched_dict = dict(name=bad_rule, enabled=True, rrule=bad_rule)
                self.post(first_url, sched_dict, expect=400)
