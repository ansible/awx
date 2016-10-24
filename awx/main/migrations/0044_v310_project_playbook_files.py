# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_v310_scm_revision'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='playbook_files',
            field=jsonfield.fields.JSONField(default=[], help_text='List of playbooks found in the project', verbose_name='Playbook Files', editable=False, blank=True),
        ),
    ]
