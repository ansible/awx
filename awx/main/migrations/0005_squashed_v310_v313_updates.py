# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_squashed_v310_release'),
    ]

    replaces = [
        (b'main', '0035_v310_remove_tower_settings'),
        (b'main', '0036_v311_insights'),
        (b'main', '0037_v313_instance_version'),
    ]

    operations = [
        # Remove Tower settings, these settings are now in separate awx.conf app.
        migrations.RemoveField(
            model_name='towersettings',
            name='user',
        ),
        migrations.DeleteModel(
            name='TowerSettings',
        ),

        migrations.AlterField(
            model_name='project',
            name='scm_type',
            field=models.CharField(default=b'', choices=[(b'', 'Manual'), (b'git', 'Git'), (b'hg', 'Mercurial'), (b'svn', 'Subversion'), (b'insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_type',
            field=models.CharField(default=b'', choices=[(b'', 'Manual'), (b'git', 'Git'), (b'hg', 'Mercurial'), (b'svn', 'Subversion'), (b'insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),

        migrations.AddField(
            model_name='instance',
            name='version',
            field=models.CharField(max_length=24, blank=True),
        ),

    ]
