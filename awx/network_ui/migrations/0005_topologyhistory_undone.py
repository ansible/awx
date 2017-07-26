# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_ui', '0004_client_messagetype_topologyhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='topologyhistory',
            name='undone',
            field=models.BooleanField(default=b'False'),
        ),
    ]
