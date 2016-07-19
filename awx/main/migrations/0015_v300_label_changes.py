# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_v300_invsource_cred'),
    ]

    operations = [
        migrations.AlterField(
            model_name='label',
            name='organization',
            field=models.ForeignKey(related_name='labels', to='main.Organization', help_text='Organization this label belongs to.'),
        ),
    ]
