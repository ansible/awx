# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSessionMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('session', models.OneToOneField(related_name='+', to='sessions.Session')),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('created', models.DateTimeField(default=None, editable=False)),
            ],
        ),
    ]
