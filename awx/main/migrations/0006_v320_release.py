# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Psycopg2
from psycopg2.extensions import AsIs

# Django
from django.db import (
    connection,
    migrations,
    models,
    OperationalError,
    ProgrammingError
)
from django.conf import settings
import taggit.managers

# AWX
import awx.main.fields
from awx.main.models import Host


def replaces():
    squashed = ['0005a_squashed_v310_v313_updates', '0005b_squashed_v310_v313_updates']
    try:
        recorder = migrations.recorder.MigrationRecorder(connection)
        result = recorder.migration_qs.filter(app='main').filter(name__in=squashed).all()
        return [('main', m.name) for m in result]
    except (OperationalError, ProgrammingError):
        return []


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_squashed_v310_v313_updates'),
    ]

    replaces = replaces()

    operations = [
        # Release UJT unique_together constraint
        migrations.AlterUniqueTogether(
            name='unifiedjobtemplate',
            unique_together=set([]),
        ),

        # Inventory Refresh
        migrations.RenameField(
            'InventorySource',
            'group',
            'deprecated_group'
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='deprecated_group',
            field=models.OneToOneField(related_name='deprecated_inventory_source', on_delete=models.CASCADE, null=True, default=None, to='main.Group'),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='inventory',
            field=models.ForeignKey(related_name='inventory_sources', default=None, to='main.Inventory', on_delete=models.CASCADE, null=True),
        ),

        # Smart Inventory
        migrations.AddField(
            model_name='inventory',
            name='host_filter',
            field=awx.main.fields.SmartFilterField(default=None, help_text='Filter that will be applied to the hosts of this inventory.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='kind',
            field=models.CharField(default='', help_text='Kind of inventory being represented.', max_length=32, blank=True, choices=[('', 'Hosts have a direct link to this inventory.'), ('smart', 'Hosts for inventory generated using the host_filter property.')]),
        ),
        migrations.CreateModel(
            name='SmartInventoryMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.ForeignKey(related_name='+', on_delete=models.CASCADE, to='main.Host')),
            ],
        ),
        migrations.AddField(
            model_name='smartinventorymembership',
            name='inventory',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='main.Inventory'),
        ),
        migrations.AddField(
            model_name='host',
            name='smart_inventories',
            field=models.ManyToManyField(related_name='_host_smart_inventories_+', through='main.SmartInventoryMembership', to='main.Inventory'),
        ),
        migrations.AlterUniqueTogether(
            name='smartinventorymembership',
            unique_together=set([('host', 'inventory')]),
        ),

        # Background Inventory deletion
        migrations.AddField(
            model_name='inventory',
            name='pending_deletion',
            field=models.BooleanField(default=False, help_text='Flag indicating the inventory is being deleted.', editable=False),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='organization',
            field=models.ForeignKey(related_name='inventories', on_delete=models.SET_NULL, to='main.Organization', help_text='Organization containing this inventory.', null=True),
        ),

        # Facts
        migrations.AlterField(
            model_name='fact',
            name='facts',
            field=awx.main.fields.JSONBField(default=dict, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True),
        ),
        migrations.AddField(
            model_name='host',
            name='ansible_facts',
            field=awx.main.fields.JSONBField(default=dict, help_text='Arbitrary JSON structure of most recent ansible_facts, per-host.', blank=True),
        ),
        migrations.AddField(
            model_name='host',
            name='ansible_facts_modified',
            field=models.DateTimeField(default=None, help_text='The date and time ansible_facts was last modified.', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='job',
            name='use_fact_cache',
            field=models.BooleanField(default=False, help_text='If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the end of a playbook run to the database and caching facts for use by Ansible.'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='use_fact_cache',
            field=models.BooleanField(default=False, help_text='If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the end of a playbook run to the database and caching facts for use by Ansible.'),
        ),
        migrations.RunSQL([("CREATE INDEX host_ansible_facts_default_gin ON %s USING gin"
                            "(ansible_facts jsonb_path_ops);", [AsIs(Host._meta.db_table)])],
                          [('DROP INDEX host_ansible_facts_default_gin;', None)]),


        # SCM file-based inventories
        migrations.AddField(
            model_name='inventorysource',
            name='scm_last_revision',
            field=models.CharField(default='', max_length=1024, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='inventorysource',
            name='source_project',
            field=models.ForeignKey(related_name='scm_inventory_sources', on_delete=models.CASCADE, default=None, blank=True, to='main.Project', help_text='Project containing inventory file used as source.', null=True),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='source_project_update',
            field=models.ForeignKey(related_name='scm_inventory_updates', on_delete=models.CASCADE, default=None, blank=True, to='main.ProjectUpdate', help_text='Inventory files from this Project Update were used for the inventory update.', null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='inventory_files',
            field=awx.main.fields.JSONField(default=[], help_text='Suggested list of content that could be Ansible inventory in the project', verbose_name='Inventory Files', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'File, Directory or Script'), ('scm', 'Sourced from a Project'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'File, Directory or Script'), ('scm', 'Sourced from a Project'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source_path',
            field=models.CharField(default='', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source_path',
            field=models.CharField(default='', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='launch_type',
            field=models.CharField(default='manual', max_length=20, editable=False, choices=[('manual', 'Manual'), ('relaunch', 'Relaunch'), ('callback', 'Callback'), ('scheduled', 'Scheduled'), ('dependency', 'Dependency'), ('workflow', 'Workflow'), ('sync', 'Sync'), ('scm', 'SCM Update')]),
        ),
        migrations.AddField(
            model_name='inventorysource',
            name='update_on_project_update',
            field=models.BooleanField(default=False),
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
            field=models.ForeignKey(related_name='notification_templates', on_delete=models.CASCADE, to='main.Organization', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='notificationtemplate',
            unique_together=set([('organization', 'name')]),
        ),

        # Add verbosity option to inventory updates
        migrations.AddField(
            model_name='inventorysource',
            name='verbosity',
            field=models.PositiveIntegerField(default=1, blank=True, choices=[(0, '0 (WARNING)'), (1, '1 (INFO)'), (2, '2 (DEBUG)')]),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='verbosity',
            field=models.PositiveIntegerField(default=1, blank=True, choices=[(0, '0 (WARNING)'), (1, '1 (INFO)'), (2, '2 (DEBUG)')]),
        ),

        # Job Templates
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_verbosity_on_launch',
            field=models.BooleanField(default=False),
        ),

        # Workflows
        migrations.AddField(
            model_name='workflowjob',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),

        # Permission and Deprecated Field Removal
        migrations.RemoveField(
            model_name='permission',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='inventory',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='project',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='team',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='user',
        ),
        migrations.RemoveField(
            model_name='activitystream',
            name='permission',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='deprecated_team',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='deprecated_user',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='deprecated_admins',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='deprecated_projects',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='deprecated_users',
        ),
        migrations.RemoveField(
            model_name='team',
            name='deprecated_projects',
        ),
        migrations.RemoveField(
            model_name='team',
            name='deprecated_users',
        ),
        migrations.DeleteModel(
            name='Permission',
        ),

        # Insights
        migrations.AddField(
            model_name='host',
            name='insights_system_id',
            field=models.TextField(default=None, help_text='Red Hat Insights host unique identifier.', null=True, db_index=True, blank=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='insights_credential',
            field=models.ForeignKey(related_name='insights_inventories', on_delete=models.SET_NULL, default=None, blank=True, to='main.Credential', help_text='Credentials to be used by hosts belonging to this inventory when accessing Red Hat Insights API.', null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='kind',
            field=models.CharField(default='', help_text='Kind of inventory being represented.', max_length=32, blank=True, choices=[('', 'Hosts have a direct link to this inventory.'), ('smart', 'Hosts for inventory generated using the host_filter property.')]),
        ),

        # Timeout help text update
        migrations.AlterField(
            model_name='inventorysource',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time (in seconds) to run before the task is canceled.', blank=True),
        ),
        migrations.AddField(
            model_name='adhoccommand',
            name='diff_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_diff_mode_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='job',
            name='diff_mode',
            field=models.BooleanField(default=False, help_text='If enabled, textual changes made to any templated files on the host are shown in the standard output'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='diff_mode',
            field=models.BooleanField(default=False, help_text='If enabled, textual changes made to any templated files on the host are shown in the standard output'),
        ),

        migrations.CreateModel(
            name='CredentialType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default='', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('kind', models.CharField(max_length=32, choices=[('ssh', 'Machine'), ('vault', 'Vault'), ('net', 'Network'), ('scm', 'Source Control'), ('cloud', 'Cloud'), ('insights', 'Insights')])),
                ('managed_by_tower', models.BooleanField(default=False, editable=False)),
                ('inputs', awx.main.fields.CredentialTypeInputField(default=dict, blank=True, help_text='Enter inputs using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax.')),
                ('injectors', awx.main.fields.CredentialTypeInjectorField(default=dict, blank=True, help_text='Enter injectors using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax.')),
                ('created_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_created+", on_delete=models.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_modified+", on_delete=models.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('kind', 'name'),
            },
        ),
        migrations.AlterModelOptions(
            name='credential',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='credential',
            name='inputs',
            field=awx.main.fields.CredentialInputField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='credential_type',
            field=models.ForeignKey(related_name='credentials', on_delete=models.CASCADE, to='main.CredentialType', null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='job',
            name='vault_credential',
            field=models.ForeignKey(related_name='jobs_as_vault_credential+', on_delete=models.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='vault_credential',
            field=models.ForeignKey(related_name='jobtemplates_as_vault_credential+', on_delete=models.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='extra_credentials',
            field=models.ManyToManyField(related_name='_job_extra_credentials_+', to='main.Credential'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='extra_credentials',
            field=models.ManyToManyField(related_name='_jobtemplate_extra_credentials_+', to='main.Credential'),
        ),
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'credential_type')]),
        ),

        migrations.AlterField(
            model_name='credential',
            name='become_method',
            field=models.CharField(default='', help_text='Privilege escalation method.', max_length=32, blank=True, choices=[('', 'None'), ('sudo', 'Sudo'), ('su', 'Su'), ('pbrun', 'Pbrun'), ('pfexec', 'Pfexec'), ('dzdo', 'DZDO'), ('pmrun', 'Pmrun'), ('runas', 'Runas')]),
        ),

        # Connecting activity stream
        migrations.AddField(
            model_name='activitystream',
            name='credential_type',
            field=models.ManyToManyField(to='main.CredentialType', blank=True),
        ),

        migrations.CreateModel(
            name='InstanceGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=250)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('controller', models.ForeignKey(related_name='controlled_groups', on_delete=models.CASCADE, default=None, editable=False, to='main.InstanceGroup', help_text='Instance Group to remotely control this group.', null=True)),
                ('instances', models.ManyToManyField(help_text='Instances that are members of this InstanceGroup', related_name='rampart_groups', editable=False, to='main.Instance')),
            ],
        ),
        migrations.AddField(
            model_name='inventory',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='instance_group',
            field=models.ForeignKey(on_delete=models.SET_NULL, default=None, blank=True, to='main.InstanceGroup', help_text='The Instance group the job was run under', null=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='instance_group',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='instance',
            name='last_isolated_check',
            field=models.DateTimeField(editable=False, null=True),
        ),
        # Migrations that don't change db schema but simply to make Django ORM happy.
        # e.g. Choice updates, help_text updates, etc.
        migrations.AlterField(
            model_name='schedule',
            name='enabled',
            field=models.BooleanField(default=True, help_text='Enables processing of this schedule.'),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='execution_node',
            field=models.TextField(default='', help_text='The node the job executed on.', editable=False, blank=True),
        ),
    ]
