# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0014_v330_saved_launchtime_configs'),
    ]

    operations = [
        # This list is intentionally empty.
        # Tower 3.3 included several data migrations that are no longer
        # necessary (this list is now empty because Tower 3.3 is past EOL and
        # cannot be directly upgraded to modern versions)
    ]
