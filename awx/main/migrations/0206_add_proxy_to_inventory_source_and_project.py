from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorysource',
            name='proxy',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Proxy URL to use when running inventory updates '
                    '(sets http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY). '
                    'Overrides the global proxy set in Extra Environment Variables.'
                ),
                max_length=1024,
            ),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='proxy',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Proxy URL to use when running inventory updates '
                    '(sets http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY). '
                    'Overrides the global proxy set in Extra Environment Variables.'
                ),
                max_length=1024,
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='proxy',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Proxy URL to use when running project updates '
                    '(sets http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY). '
                    'Overrides the global proxy set in Extra Environment Variables.'
                ),
                max_length=1024,
            ),
        ),
        migrations.AddField(
            model_name='projectupdate',
            name='proxy',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Proxy URL to use when running project updates '
                    '(sets http_proxy/https_proxy/HTTP_PROXY/HTTPS_PROXY). '
                    'Overrides the global proxy set in Extra Environment Variables.'
                ),
                max_length=1024,
            ),
        ),
    ]
