# Generated by Django 3.2.13 on 2022-10-24 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0172_prevent_instance_fallback'),
    ]

    operations = [
        migrations.AddField(
            model_name='instancegroup',
            name='max_concurrent_jobs',
            field=models.IntegerField(
                default=0,
                help_text='Maximum number of concurrent jobs to run on a group. Zero means no limit, jobs will be scheduled based on instance capacity.',
            ),
        ),
    ]
