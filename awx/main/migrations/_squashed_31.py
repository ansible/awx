from django.db import (
    migrations,
    models,
)

SQUASHED_31 = {
    '0035_v310_remove_tower_settings': [
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
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_type',
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
    ],
    '0036_v311_insights': [
        migrations.AlterField(
            model_name='project',
            name='scm_type',
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_type',
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
    ],
    '0037_v313_instance_version': [
        # Remove Tower settings, these settings are now in separate awx.conf app.
        migrations.AddField(
            model_name='instance',
            name='version',
            field=models.CharField(max_length=24, blank=True),
        ),
    ],
}

__all__ = ['SQUASHED_31']
