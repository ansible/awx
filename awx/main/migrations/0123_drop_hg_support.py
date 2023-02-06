from django.db import migrations, models
from awx.main.migrations._hg_removal import delete_hg_scm


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0122_really_remove_cloudforms_inventory'),
    ]

    operations = [
        migrations.RunPython(delete_hg_scm),
        migrations.AlterField(
            model_name='project',
            name='scm_type',
            field=models.CharField(
                blank=True,
                choices=[('', 'Manual'), ('git', 'Git'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights'), ('archive', 'Remote Archive')],
                default='',
                help_text='Specifies the source control system used to store the project.',
                max_length=8,
                verbose_name='SCM Type',
            ),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_type',
            field=models.CharField(
                blank=True,
                choices=[('', 'Manual'), ('git', 'Git'), ('svn', 'Subversion'), ('insights', 'Red Hat Insights'), ('archive', 'Remote Archive')],
                default='',
                help_text='Specifies the source control system used to store the project.',
                max_length=8,
                verbose_name='SCM Type',
            ),
        ),
    ]
