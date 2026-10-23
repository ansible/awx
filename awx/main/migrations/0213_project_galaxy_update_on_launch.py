from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0212_create_metrics_utility_functions'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='galaxy_update_on_launch',
            field=models.BooleanField(
                default=False,
                help_text='Bypass the ansible-galaxy response cache to fetch latest collection metadata when a job is launched that uses the project.',
            ),
        ),
    ]
