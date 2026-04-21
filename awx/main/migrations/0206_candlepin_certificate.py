# Generated manually for candlepin integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandlepinCertificate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'consumer_uuid',
                    models.CharField(blank=True, default='00000000-0000-0000-0000-000000000000', help_text='Candlepin consumer UUID', max_length=255),
                ),
                ('cert_pem', models.TextField(blank=True, default='', help_text='PEM-encoded certificate (encrypted)')),
                ('key_pem', models.TextField(blank=True, default='', help_text='PEM-encoded private key (encrypted)')),
                ('serial_number', models.CharField(blank=True, default='', help_text='Certificate serial number for tracking', max_length=255)),
                ('expires_at', models.DateTimeField(blank=True, help_text='Certificate expiry timestamp', null=True)),
            ],
            options={
                'verbose_name': 'Candlepin Certificate',
                'verbose_name_plural': 'Candlepin Certificates',
                'db_table': 'main_candlepin_certificate',
            },
        ),
    ]
