# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('conf', '0002_v310_copy_tower_settings')]

    operations = [migrations.AlterField(model_name='setting', name='value', field=models.JSONField(null=True))]
