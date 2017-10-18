# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='credential',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='credentialtype',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='credentialtype',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='group',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='group',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='host',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='host',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='inventory',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='inventory',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='label',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='label',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='organization',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='organization',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='schedule',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='schedule',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='team',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='team',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='parent_uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='self_uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True, editable=False),
        ),
    ]
