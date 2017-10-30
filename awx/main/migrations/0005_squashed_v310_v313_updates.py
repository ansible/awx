# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations

import _squashed
from _squashed_310 import SQUASHED_310


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_squashed_v310_release'),
    ]

    replaces = _squashed.replaces(SQUASHED_310)
    operations = _squashed.operations(SQUASHED_310)
