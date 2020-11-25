from django.db import migrations
from awx.main.migrations._inventory_source import delete_cloudforms_inv_source


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0121_delete_toweranalyticsstate'),
    ]

    operations = [
        migrations.RunPython(delete_cloudforms_inv_source),
    ]
