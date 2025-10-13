# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

# AWX
import awx.main.fields
from awx.main.models import CredentialType
from awx.main.utils.common import set_current_apps


def setup_akeyless_credential_type(apps, schema_editor):
    """
    Ensure the Akeyless credential type is registered in the database.
    This will be handled by the credential plugin loading system.
    """
    set_current_apps(apps)
    # The credential type will be automatically created by the plugin loading system
    # when load_credentials() is called during app startup
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0204_squashed_deletions'),
    ]

    operations = [
        migrations.RunPython(setup_akeyless_credential_type),
    ]
