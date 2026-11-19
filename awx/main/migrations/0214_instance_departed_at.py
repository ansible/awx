from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0213_project_galaxy_update_on_launch'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='departed_at',
            field=models.DateTimeField(
                default=None,
                editable=False,
                help_text='When this instance announced it was leaving the cluster. Cleared by its next healthy health check.',
                null=True,
            ),
        ),
    ]
