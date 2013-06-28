# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import datetime
import json

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from django.core.urlresolvers import reverse
from awx.main.models import *
from awx.main.tests.base import BaseTest
from awx.main.licenses import *

class LicensesTest(BaseTest):

    def setUp(self):
        super(LicensesTest, self).setUp()

    def test_license_writer(self):
        assert 2 == 4

    def test_license_reader(self):
        assert 2 == 3
