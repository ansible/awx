# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserEnterpriseAuth',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider', models.CharField(max_length=32, choices=[(b'radius', 'RADIUS'), (b'tacacs+', 'TACACS+')])),
                ('user', models.ForeignKey(related_name='enterprise_auth', on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userenterpriseauth',
            unique_together=set([('user', 'provider')]),
        ),
    ]
