# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_squashed_v310_v313_updates'),
    ]

    replaces = [
        (b'main', '0036_v311_insights'),
    ]

    operations = [
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
    ]