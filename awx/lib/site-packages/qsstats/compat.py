# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.datetime.now
