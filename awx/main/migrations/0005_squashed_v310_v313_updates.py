# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations

from . import _squashed
from ._squashed_31 import SQUASHED_31


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_squashed_v310_release'),
    ]

    replaces = _squashed.replaces(SQUASHED_31)
    operations = _squashed.operations(SQUASHED_31)
