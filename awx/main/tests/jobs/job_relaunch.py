# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import

# Django
import django
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import * # noqa
from .base import BaseJobTestMixin

__all__ = ['JobRelaunchTest',]

class JobRelaunchTest(BaseJobTestMixin, django.test.TestCase):
    def setUp(self):
        super(JobRelaunchTest, self).setUp()

        self.url = reverse('api:job_template_list')
        self.data = dict(
            name         = 'launched job template',
            job_type     = PERM_INVENTORY_DEPLOY,
            inventory    = self.inv_eng.pk,
            project      = self.proj_dev.pk,
            credential   = self.cred_sue.pk,
            playbook     = self.proj_dev.playbooks[0],
        )

        with self.current_user(self.user_sue):
            response = self.post(self.url, self.data, expect=201)
            self.launch_url = reverse('api:job_template_launch',
                                      args=(response['id'],))
            response = self.post(self.launch_url, {}, expect=202)
            self.relaunch_url = reverse('api:job_relaunch',
                                        args=(response['job'],))

    def test_relaunch_job(self):
        with self.current_user(self.user_sue):
            response = self.post(self.relaunch_url, {}, expect=201)

    def test_relaunch_inactive_project(self):
        self.proj_dev.mark_inactive()
        with self.current_user(self.user_sue):
            response = self.post(self.relaunch_url, {}, expect=400)

    def test_relaunch_inactive_inventory(self): 
        self.inv_eng.mark_inactive()
        with self.current_user(self.user_sue):
            response = self.post(self.relaunch_url, {}, expect=400)

    def test_relaunch_deleted_inventory(self): 
        self.inv_eng.delete()
        with self.current_user(self.user_sue):
            response = self.post(self.relaunch_url, {}, expect=400)

    def test_relaunch_deleted_project(self): 
        self.proj_dev.delete()
        with self.current_user(self.user_sue):
            response = self.post(self.relaunch_url, {}, expect=400)
