# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Psycopg2
from psycopg2.extensions import AsIs

# Django
from django.db import migrations, models

# AWX
import awx.main.fields
from awx.main.models import Host


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0037_v313_instance_version'),
    ]

    operations = [
        # Inventory Refresh
        migrations.RenameField(
            'InventorySource',
            'group',
            'deprecated_group'
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='deprecated_group',
            field=models.OneToOneField(related_name='deprecated_inventory_source', null=True, default=None, to='main.Group'),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='inventory',
            field=models.ForeignKey(related_name='inventory_sources', default=None, to='main.Inventory', null=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='host_filter',
            field=awx.main.fields.DynamicFilterField(default=None, help_text='Filter that will be applied to the hosts of this inventory.', null=True, blank=True),
        ),

        # Facts
        migrations.AlterField(
            model_name='fact',
            name='facts',
            field=awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True),
        ),
        migrations.AddField(
            model_name='host',
            name='ansible_facts',
            field=awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of most recent ansible_facts, per-host.', blank=True),
        ),
        migrations.RunSQL([("CREATE INDEX host_ansible_facts_default_gin ON %s USING gin"
                            "(ansible_facts jsonb_path_ops);", [AsIs(Host._meta.db_table)])],
                          [('DROP INDEX host_ansible_facts_default_gin;', None)]),

        # SCM file-based inventories
        migrations.AddField(
            model_name='inventorysource',
            name='scm_last_revision',
            field=models.CharField(default=b'', max_length=1024, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='inventorysource',
            name='scm_project',
            field=models.ForeignKey(related_name='scm_inventory_sources', default=None, blank=True, to='main.Project', help_text='Project containing inventory file used as source.', null=True),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='scm_project_update',
            field=models.ForeignKey(related_name='scm_inventory_updates', default=None, blank=True, to='main.ProjectUpdate', help_text='Inventory files from this Project Update were used for the inventory update.', null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='inventory_files',
            field=awx.main.fields.JSONField(default=[], help_text='Suggested list of content that could be Ansible inventory in the project', verbose_name='Inventory Files', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'File, Directory or Script Locally or in Project'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'File, Directory or Script Locally or in Project'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source_path',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source_path',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='launch_type',
            field=models.CharField(default=b'manual', max_length=20, editable=False, choices=[(b'manual', 'Manual'), (b'relaunch', 'Relaunch'), (b'callback', 'Callback'), (b'scheduled', 'Scheduled'), (b'dependency', 'Dependency'), (b'workflow', 'Workflow'), (b'sync', 'Sync'), (b'scm', 'SCM Update')]),
        ),

        # Named URL
        migrations.AlterField(
            model_name='notificationtemplate',
            name='name',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='organization',
            field=models.ForeignKey(related_name='notification_templates', to='main.Organization', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='notificationtemplate',
            unique_together=set([('organization', 'name')]),
        ),
    ]
