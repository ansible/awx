# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals

import awx.main.fields

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils.timezone import now

import jsonfield.fields
import jsonbfield.fields
import taggit.managers


def create_system_job_templates(apps, schema_editor):
    '''
    Create default system job templates if not present. Create default schedules
    only if new system job templates were created (i.e. new database).
    '''

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    now_str = now_dt.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_jobs',
        defaults=dict(
            name='Cleanup Job Details',
            description='Remove job history',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sched = Schedule(
            name='Cleanup Job Schedule',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'days': '120'},
            created=now_dt,
            modified=now_dt,
        )
        sched.unified_job_template = sjt
        sched.save()

    existing_cd_jobs = SystemJobTemplate.objects.filter(job_type='cleanup_deleted')
    Schedule.objects.filter(unified_job_template__in=existing_cd_jobs).delete()
    existing_cd_jobs.delete()

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_activitystream',
        defaults=dict(
            name='Cleanup Activity Stream',
            description='Remove activity stream history',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sched = Schedule(
            name='Cleanup Activity Schedule',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'days': '355'},
            created=now_dt,
            modified=now_dt,
        )
        sched.unified_job_template = sjt
        sched.save()

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_facts',
        defaults=dict(
            name='Cleanup Fact Details',
            description='Remove system tracking history',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sched = Schedule(
            name='Cleanup Fact Schedule',
            rrule='DTSTART:%s RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=1' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'older_than': '120d', 'granularity': '1w'},
            created=now_dt,
            modified=now_dt,
        )
        sched.unified_job_template = sjt
        sched.save()


class Migration(migrations.Migration):
    replaces = [(b'main', '0002_v300_tower_settings_changes'),
                (b'main', '0003_v300_notification_changes'),
                (b'main', '0004_v300_fact_changes'),
                (b'main', '0005_v300_migrate_facts'),
                (b'main', '0006_v300_active_flag_cleanup'),
                (b'main', '0007_v300_active_flag_removal'),
                (b'main', '0008_v300_rbac_changes'),
                (b'main', '0009_v300_rbac_migrations'),
                (b'main', '0010_v300_create_system_job_templates'),
                (b'main', '0011_v300_credential_domain_field'),
                (b'main', '0012_v300_create_labels'),
                (b'main', '0013_v300_label_changes'),
                (b'main', '0014_v300_invsource_cred'),
                (b'main', '0015_v300_label_changes'),
                (b'main', '0016_v300_prompting_changes'),
                (b'main', '0017_v300_prompting_migrations'),
                (b'main', '0018_v300_host_ordering'),
                (b'main', '0019_v300_new_azure_credential'),]

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0001_initial'),
    ]

    operations = [
        # Tower settings changes
        migrations.CreateModel(
            name='TowerSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('key', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=128)),
                ('value', models.TextField(blank=True)),
                ('value_type', models.CharField(max_length=12, choices=[(b'string', 'String'), (b'int', 'Integer'), (b'float', 'Decimal'), (b'json', 'JSON'), (b'bool', 'Boolean'), (b'password', 'Password'), (b'list', 'List')])),
                ('user', models.ForeignKey(related_name='settings', default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        # Notification changes
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('status', models.CharField(default=b'pending', max_length=20, editable=False, choices=[(b'pending', 'Pending'), (b'successful', 'Successful'), (b'failed', 'Failed')])),
                ('error', models.TextField(default=b'', editable=False, blank=True)),
                ('notifications_sent', models.IntegerField(default=0, editable=False)),
                ('notification_type', models.CharField(max_length=32, choices=[(b'email', 'Email'), (b'slack', 'Slack'), (b'twilio', 'Twilio'), (b'pagerduty', 'Pagerduty'), (b'hipchat', 'HipChat'), (b'webhook', 'Webhook'), (b'mattermost', 'Mattermost'), (b'irc', 'IRC')])),
                ('recipients', models.TextField(default=b'', editable=False, blank=True)),
                ('subject', models.TextField(default=b'', editable=False, blank=True)),
                ('body', jsonfield.fields.JSONField(default=dict, blank=True)),
            ],
            options={
                'ordering': ('pk',),
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(unique=True, max_length=512)),
                ('notification_type', models.CharField(max_length=32, choices=[(b'email', 'Email'), (b'slack', 'Slack'), (b'twilio', 'Twilio'), (b'pagerduty', 'Pagerduty'), (b'hipchat', 'HipChat'), (b'webhook', 'Webhook'), (b'mattermost', 'Mattermost'), (b'irc', 'IRC')])),
                ('notification_configuration', jsonfield.fields.JSONField(default=dict)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'notificationtemplate', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'notificationtemplate', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='notification_templates', on_delete=django.db.models.deletion.SET_NULL, to='main.Organization', null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
        ),
        migrations.AddField(
            model_name='notification',
            name='notification_template',
            field=models.ForeignKey(related_name='notifications', editable=False, to='main.NotificationTemplate'),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='notification',
            field=models.ManyToManyField(to='main.Notification', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='notification_template',
            field=models.ManyToManyField(to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notification_templates_any',
            field=models.ManyToManyField(related_name='organization_notification_templates_for_any', to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notification_templates_error',
            field=models.ManyToManyField(related_name='organization_notification_templates_for_errors', to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notification_templates_success',
            field=models.ManyToManyField(related_name='organization_notification_templates_for_success', to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='notifications',
            field=models.ManyToManyField(related_name='unifiedjob_notifications', editable=False, to='main.Notification'),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notification_templates_any',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notification_templates_for_any', to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notification_templates_error',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notification_templates_for_errors', to='main.NotificationTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notification_templates_success',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notification_templates_for_success', to='main.NotificationTemplate', blank=True),
        ),
        # Fact changes
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=None, help_text='Date and time of the corresponding fact scan gathering time.', editable=False)),
                ('module', models.CharField(max_length=128)),
                ('facts', jsonbfield.fields.JSONField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True)),
                ('host', models.ForeignKey(related_name='facts', to='main.Host', help_text='Host for the facts that the fact scan captured.')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='fact',
            index_together=set([('timestamp', 'module', 'host')]),
        ),
        # Active flag removal
        migrations.RemoveField(
            model_name='credential',
            name='active',
        ),
        migrations.RemoveField(
            model_name='custominventoryscript',
            name='active',
        ),
        migrations.RemoveField(
            model_name='group',
            name='active',
        ),
        migrations.RemoveField(
            model_name='host',
            name='active',
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='active',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='active',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='active',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='active',
        ),
        migrations.RemoveField(
            model_name='team',
            name='active',
        ),
        migrations.RemoveField(
            model_name='unifiedjob',
            name='active',
        ),
        migrations.RemoveField(
            model_name='unifiedjobtemplate',
            name='active',
        ),

        # RBAC Changes
        # ############
        migrations.RenameField(
            'Organization',
            'admins',
            'deprecated_admins',
        ),
        migrations.RenameField(
            'Organization',
            'users',
            'deprecated_users',
        ),
        migrations.RenameField(
            'Team',
            'users',
            'deprecated_users',
        ),
        migrations.RenameField(
            'Team',
            'projects',
            'deprecated_projects',
        ),
        migrations.AddField(
            model_name='project',
            name='organization',
            field=models.ForeignKey(related_name='projects', to='main.Organization', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='deprecated_projects',
            field=models.ManyToManyField(related_name='deprecated_teams', to='main.Project', blank=True),
        ),
        migrations.RenameField(
            model_name='organization',
            old_name='projects',
            new_name='deprecated_projects',
        ),
        migrations.AlterField(
            model_name='organization',
            name='deprecated_projects',
            field=models.ManyToManyField(related_name='deprecated_organizations', to='main.Project', blank=True),
        ),
        migrations.RenameField(
            'Credential',
            'team',
            'deprecated_team',
        ),
        migrations.RenameField(
            'Credential',
            'user',
            'deprecated_user',
        ),
        migrations.AlterField(
            model_name='organization',
            name='deprecated_admins',
            field=models.ManyToManyField(related_name='deprecated_admin_of_organizations', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='deprecated_users',
            field=models.ManyToManyField(related_name='deprecated_organizations', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='deprecated_users',
            field=models.ManyToManyField(related_name='deprecated_teams', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='credential',
            name='organization',
            field=models.ForeignKey(related_name='credentials', default=None, blank=True, to='main.Organization', null=True),
        ),

        #
        # New RBAC models and fields
        #
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role_field', models.TextField()),
                ('singleton_name', models.TextField(default=None, unique=True, null=True, db_index=True)),
                ('members', models.ManyToManyField(related_name='roles', to=settings.AUTH_USER_MODEL)),
                ('parents', models.ManyToManyField(related_name='children', to='main.Role')),
                ('implicit_parents', models.TextField(default=b'[]')),
                ('content_type', models.ForeignKey(default=None, to='contenttypes.ContentType', null=True)),
                ('object_id', models.PositiveIntegerField(default=None, null=True)),

            ],
            options={
                'db_table': 'main_rbac_roles',
                'verbose_name_plural': 'roles',
            },
        ),
        migrations.CreateModel(
            name='RoleAncestorEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role_field', models.TextField()),
                ('content_type_id', models.PositiveIntegerField()),
                ('object_id', models.PositiveIntegerField()),
                ('ancestor', models.ForeignKey(related_name='+', to='main.Role')),
                ('descendent', models.ForeignKey(related_name='+', to='main.Role')),
            ],
            options={
                'db_table': 'main_rbac_role_ancestors',
                'verbose_name_plural': 'role_ancestors',
            },
        ),
        migrations.AddField(
            model_name='role',
            name='ancestors',
            field=models.ManyToManyField(related_name='descendents', through='main.RoleAncestorEntry', to='main.Role'),
        ),
        migrations.AlterIndexTogether(
            name='role',
            index_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterIndexTogether(
            name='roleancestorentry',
            index_together=set([('ancestor', 'content_type_id', 'object_id'), ('ancestor', 'content_type_id', 'role_field'), ('ancestor', 'descendent')]),
        ),
        migrations.AddField(
            model_name='credential',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_administrator'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'organization.auditor_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'organization.member_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'adhoc_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role',  b'update_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'project.organization.admin_role', b'inventory.organization.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'project.organization.auditor_role', b'inventory.organization.auditor_role', b'execute_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'singleton:system_administrator', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'singleton:system_auditor', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'member_role', b'auditor_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.admin_role', b'singleton:system_administrator'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'singleton:system_auditor', b'use_role', b'update_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=None, to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role', b'organization.auditor_role', b'member_role'], to='main.Role', null=b'True'),
        ),

        # System Job Templates
        migrations.RunPython(create_system_job_templates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='systemjob',
            name='job_type',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'cleanup_jobs', 'Remove jobs older than a certain number of days'), (b'cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), (b'cleanup_facts', 'Purge and/or reduce the granularity of system tracking data')]),
        ),
        migrations.AlterField(
            model_name='systemjobtemplate',
            name='job_type',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'cleanup_jobs', 'Remove jobs older than a certain number of days'), (b'cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), (b'cleanup_facts', 'Purge and/or reduce the granularity of system tracking data')]),
        ),
        # Credential domain field
        migrations.AddField(
            model_name='credential',
            name='domain',
            field=models.CharField(default=b'', help_text='The identifier for the domain.', max_length=100, verbose_name='Domain', blank=True),
        ),
        # Create Labels
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='labels', to='main.Organization', help_text='Organization this label belongs to.')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('organization', 'name'),
            },
        ),
        migrations.AddField(
            model_name='activitystream',
            name='label',
            field=models.ManyToManyField(to='main.Label', blank=True),
        ),
        migrations.AddField(
            model_name='job',
            name='labels',
            field=models.ManyToManyField(related_name='job_labels', to='main.Label', blank=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='labels',
            field=models.ManyToManyField(related_name='jobtemplate_labels', to='main.Label', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='label',
            unique_together=set([('name', 'organization')]),
        ),
        # Label changes
        migrations.AlterField(
            model_name='label',
            name='organization',
            field=models.ForeignKey(related_name='labels', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Organization', help_text='Organization this label belongs to.', null=True),
        ),
        migrations.AlterField(
            model_name='label',
            name='organization',
            field=models.ForeignKey(related_name='labels', to='main.Organization', help_text='Organization this label belongs to.'),
        ),
        # InventorySource Credential
        migrations.AddField(
            model_name='job',
            name='network_credential',
            field=models.ForeignKey(related_name='jobs_as_network_credential+', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='network_credential',
            field=models.ForeignKey(related_name='jobtemplates_as_network_credential+', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='authorize',
            field=models.BooleanField(default=False, help_text='Whether to use the authorize mechanism.'),
        ),
        migrations.AddField(
            model_name='credential',
            name='authorize_password',
            field=models.CharField(default=b'', help_text='Password used by the authorize mechanism.', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_team',
            field=models.ForeignKey(related_name='deprecated_credentials', default=None, blank=True, to='main.Team', null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_user',
            field=models.ForeignKey(related_name='deprecated_credentials', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default=b'ssh', max_length=32, choices=[(b'ssh', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'aws', 'Amazon Web Services'), (b'rax', 'Rackspace'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='team',
            name='deprecated_projects',
            field=models.ManyToManyField(related_name='deprecated_teams', to='main.Project', blank=True),
        ),
        # Prompting changes
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_limit_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_inventory_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_credential_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_job_type_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='job',
            name='inventory',
            field=models.ForeignKey(related_name='jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='inventory',
            field=models.ForeignKey(related_name='jobtemplates', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
        # Host ordering
        migrations.AlterModelOptions(
            name='host',
            options={'ordering': ('name',)},
        ),
        # New Azure credential
        migrations.AddField(
            model_name='credential',
            name='client',
            field=models.CharField(default=b'', help_text='Client Id or Application Id for the credential', max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='secret',
            field=models.CharField(default=b'', help_text='Secret Token for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='subscription',
            field=models.CharField(default=b'', help_text='Subscription identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='tenant',
            field=models.CharField(default=b'', help_text='Tenant identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default=b'ssh', max_length=32, choices=[(b'ssh', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'aws', 'Amazon Web Services'), (b'rax', 'Rackspace'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='host',
            name='instance_id',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
    ]
