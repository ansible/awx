# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved

import zmq

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Launch external job status/event receiver'

    def handle(self, *args, **kwargs):
        pass

