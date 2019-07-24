# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_webhook_notification_template_fields(apps, schema_editor):
    # loop over all existing webhook notification templates and make
    # sure they have the new "http_method" field filled in with "POST"
    NotificationTemplate = apps.get_model('main', 'notificationtemplate')
    webhooks = NotificationTemplate.objects.filter(notification_type='webhook')
    for w in webhooks:
        w.notification_configuration['http_method'] = 'POST'
        w.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0081_v360_notify_on_start'),
    ]

    operations = [
        migrations.RunPython(add_webhook_notification_template_fields, migrations.RunPython.noop),
    ]
