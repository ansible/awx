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
    replaces = [('main', '0002_v300_tower_settings_changes'),
                ('main', '0003_v300_notification_changes'),
                ('main', '0004_v300_fact_changes'),
                ('main', '0005_v300_migrate_facts'),
                ('main', '0006_v300_active_flag_cleanup'),
                ('main', '0007_v300_active_flag_removal'),
                ('main', '0008_v300_rbac_changes'),
                ('main', '0009_v300_rbac_migrations'),
                ('main', '0010_v300_create_system_job_templates'),
                ('main', '0011_v300_credential_domain_field'),
                ('main', '0012_v300_create_labels'),
                ('main', '0013_v300_label_changes'),
                ('main', '0014_v300_invsource_cred'),
                ('main', '0015_v300_label_changes'),
                ('main', '0016_v300_prompting_changes'),
                ('main', '0017_v300_prompting_migrations'),
                ('main', '0018_v300_host_ordering'),
                ('main', '0019_v300_new_azure_credential'),]

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
                ('value_type', models.CharField(max_length=12, choices=[('string', 'String'), ('int', 'Integer'), ('float', 'Decimal'), ('json', 'JSON'), ('bool', 'Boolean'), ('password', 'Password'), ('list', 'List')])),
                ('user', models.ForeignKey(related_name='settings', default=None, editable=False, to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)),
            ],
        ),
        # Notification changes
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('status', models.CharField(default='pending', max_length=20, editable=False, choices=[('pending', 'Pending'), ('successful', 'Successful'), ('failed', 'Failed')])),
                ('error', models.TextField(default='', editable=False, blank=True)),
                ('notifications_sent', models.IntegerField(default=0, editable=False)),
                ('notification_type', models.CharField(max_length=32, choices=[('email', 'Email'), ('slack', 'Slack'), ('twilio', 'Twilio'), ('pagerduty', 'Pagerduty'), ('hipchat', 'HipChat'), ('webhook', 'Webhook'), ('mattermost', 'Mattermost'), ('rocketchat', 'Rocket.Chat'), ('irc', 'IRC')])),
                ('recipients', models.TextField(default='', editable=False, blank=True)),
                ('subject', models.TextField(default='', editable=False, blank=True)),
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
                ('description', models.TextField(default='', blank=True)),
                ('name', models.CharField(unique=True, max_length=512)),
                ('notification_type', models.CharField(max_length=32, choices=[('email', 'Email'), ('slack', 'Slack'), ('twilio', 'Twilio'), ('pagerduty', 'Pagerduty'), ('hipchat', 'HipChat'), ('webhook', 'Webhook'), ('mattermost', 'Mattermost'), ('rocketchat', 'Rocket.Chat'), ('irc', 'IRC')])),
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
            field=models.ForeignKey(related_name='notifications', editable=False, on_delete=models.CASCADE, to='main.NotificationTemplate'),
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
                ('facts', awx.main.fields.JSONBField(default=dict, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True)),
                ('host', models.ForeignKey(related_name='facts', to='main.Host', on_delete=models.CASCADE, help_text='Host for the facts that the fact scan captured.')),
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
            field=models.ForeignKey(related_name='projects', to='main.Organization', on_delete=models.CASCADE, blank=True, null=True),
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
            field=models.ForeignKey(related_name='credentials', on_delete=models.CASCADE, default=None, blank=True, to='main.Organization', null=True),
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
                ('implicit_parents', models.TextField(default='[]')),
                ('content_type', models.ForeignKey(default=None, to='contenttypes.ContentType', on_delete=models.CASCADE, null=True)),
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
                ('ancestor', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='main.Role')),
                ('descendent', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='main.Role')),
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
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_administrator'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_auditor', 'organization.auditor_role', 'use_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='organization.admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.auditor_role', 'organization.member_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='organization.admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='adhoc_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.auditor_role',  'update_role', 'use_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['project.organization.admin_role', 'inventory.organization.admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['project.organization.auditor_role', 'inventory.organization.auditor_role', 'execute_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='singleton:system_administrator', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='singleton:system_auditor', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['member_role', 'auditor_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='project',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.admin_role', 'singleton:system_administrator'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='project',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='project',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='project',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.auditor_role', 'singleton:system_auditor', 'use_role', 'update_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='team',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='organization.admin_role', to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=None, to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['admin_role', 'organization.auditor_role', 'member_role'], to='main.Role', null='True'),
        ),

        # System Job Templates
        migrations.RunPython(create_system_job_templates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='systemjob',
            name='job_type',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data')]),
        ),
        migrations.AlterField(
            model_name='systemjobtemplate',
            name='job_type',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data')]),
        ),
        # Credential domain field
        migrations.AddField(
            model_name='credential',
            name='domain',
            field=models.CharField(default='', help_text='The identifier for the domain.', max_length=100, verbose_name='Domain', blank=True),
        ),
        # Create Labels
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default='', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='labels', on_delete=django.db.models.deletion.CASCADE, to='main.Organization', help_text='Organization this label belongs to.')),
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
            field=models.ForeignKey(related_name='labels', on_delete=django.db.models.deletion.CASCADE, default=None, blank=True, to='main.Organization', help_text='Organization this label belongs to.', null=True),
        ),
        migrations.AlterField(
            model_name='label',
            name='organization',
            field=models.ForeignKey(related_name='labels', on_delete=django.db.models.deletion.CASCADE, to='main.Organization', help_text='Organization this label belongs to.'),
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
            field=models.CharField(default='', help_text='Password used by the authorize mechanism.', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_team',
            field=models.ForeignKey(related_name='deprecated_credentials', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Team', null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_user',
            field=models.ForeignKey(related_name='deprecated_credentials', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default='ssh', max_length=32, choices=[('ssh', 'Machine'), ('net', 'Network'), ('scm', 'Source Control'), ('aws', 'Amazon Web Services'), ('rax', 'Rackspace'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure'), ('openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
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
            field=models.CharField(default='', help_text='Client Id or Application Id for the credential', max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='secret',
            field=models.CharField(default='', help_text='Secret Token for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='subscription',
            field=models.CharField(default='', help_text='Subscription identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='tenant',
            field=models.CharField(default='', help_text='Tenant identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default='ssh', max_length=32, choices=[('ssh', 'Machine'), ('net', 'Network'), ('scm', 'Source Control'), ('aws', 'Amazon Web Services'), ('rax', 'Rackspace'), ('vmware', 'VMware vCenter'), ('satellite6', 'Satellite 6'), ('cloudforms', 'CloudForms'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='host',
            name='instance_id',
            field=models.CharField(default='', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Satellite 6'), ('cloudforms', 'CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Satellite 6'), ('cloudforms', 'CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
    ]
