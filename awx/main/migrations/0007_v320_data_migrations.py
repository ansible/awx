# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations, models

# AWX
from awx.main.migrations import ActivityStreamDisabledMigration
import awx.main.fields


class Migration(ActivityStreamDisabledMigration):

    dependencies = [
        ('main', '0006_v320_release'),
    ]

    operations = [
        # This list is intentionally empty.
        # Tower 3.2 included several data migrations that are no longer
        # necessary (this list is now empty because Tower 3.2 is past EOL and
        # cannot be directly upgraded to modern versions of Tower)
    ]
