# Generated by Django 4.2.10 on 2024-08-07 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0196_remove_activitystream_o_auth2_access_token_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OAuth2Application',
        ),
    ]
