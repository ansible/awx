# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sso', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userenterpriseauth',
            name='provider',
            field=models.CharField(max_length=32, choices=[(b'radius', 'RADIUS'), (b'tacacs+', 'TACACS+'), (b'saml', 'SAML')]),
        ),
    ]
