# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'InventoryUpdateNew'
        db.create_table(u'main_inventoryupdatenew', (
            (u'unifiedjob_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJob'], unique=True, primary_key=True)),
            ('source', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True)),
            ('source_path', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('source_vars', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='inventoryupdatenews', null=True, blank=True, to=orm['main.Credential'])),
            ('source_regions', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('overwrite', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('overwrite_vars', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('license_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('inventory_source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='inventory_updates', to=orm['main.InventorySourceNew'])),
        ))
        db.send_create_signal('main', ['InventoryUpdateNew'])

        # Adding model 'JobNew'
        db.create_table(u'main_jobnew', (
            (u'unifiedjob_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJob'], unique=True, primary_key=True)),
            ('job_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobnews', null=True, on_delete=models.SET_NULL, to=orm['main.Inventory'])),
            ('playbook', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobnews', on_delete=models.SET_NULL, default=None, to=orm['main.Credential'], blank=True, null=True)),
            ('cloud_credential', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobnews_as_cloud_credential+', on_delete=models.SET_NULL, default=None, to=orm['main.Credential'], blank=True, null=True)),
            ('forks', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('limit', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('verbosity', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('extra_vars', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('job_tags', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('job_template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', on_delete=models.SET_NULL, default=None, to=orm['main.JobTemplateNew'], blank=True, null=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', null=True, on_delete=models.SET_NULL, to=orm['main.ProjectNew'])),
        ))
        db.send_create_signal('main', ['JobNew'])

        # Adding model 'UnifiedJob'
        db.create_table(u'main_unifiedjob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype', self.gf('django.db.models.fields.related.ForeignKey')(related_name='polymorphic_main.unifiedjob_set', null=True, to=orm['contenttypes.ContentType'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'unifiedjob', 'app_label': 'main'}(class)s_created+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'unifiedjob', 'app_label': 'main'}(class)s_modified+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('old_pk', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('unified_job_template', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='unifiedjob_unified_jobs', null=True, to=orm['main.UnifiedJobTemplate'])),
            ('launch_type', self.gf('django.db.models.fields.CharField')(default='manual', max_length=20)),
            ('schedule', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Schedule'], null=True)),
            ('cancel_flag', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.CharField')(default='new', max_length=20)),
            ('failed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('elapsed', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=3)),
            ('job_args', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('job_cwd', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('job_env', self.gf('jsonfield.fields.JSONField')(default={}, blank=True)),
            ('start_args', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('result_stdout_text', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('result_stdout_file', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('result_traceback', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('celery_task_id', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True)),
        ))
        db.send_create_signal('main', ['UnifiedJob'])

        # Adding M2M table for field depends_on on 'UnifiedJob'
        m2m_table_name = db.shorten_name(u'main_unifiedjob_depends_on')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_unifiedjob', models.ForeignKey(orm['main.unifiedjob'], null=False)),
            ('to_unifiedjob', models.ForeignKey(orm['main.unifiedjob'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_unifiedjob_id', 'to_unifiedjob_id'])

        # Adding model 'Schedule'
        db.create_table(u'main_schedule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'schedule', 'app_label': 'main'}(class)s_created+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'schedule', 'app_label': 'main'}(class)s_modified+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('job_template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='schedules', to=orm['main.UnifiedJobTemplate'])),
            ('dtstart', self.gf('django.db.models.fields.DateTimeField')()),
            ('dtend', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('rrule', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('main', ['Schedule'])

        # Adding model 'InventorySourceNew'
        db.create_table(u'main_inventorysourcenew', (
            (u'unifiedjobtemplate_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJobTemplate'], unique=True, primary_key=True)),
            ('source', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True)),
            ('source_path', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('source_vars', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='inventorysourcenews', null=True, blank=True, to=orm['main.Credential'])),
            ('source_regions', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('overwrite', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('overwrite_vars', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('update_on_launch', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('update_cache_timeout', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='new_inventory_sources', null=True, to=orm['main.Inventory'])),
            ('group', self.gf('awx.main.fields.AutoOneToOneField')(related_name='new_inventory_source', null=True, default=None, to=orm['main.Group'], blank=True, unique=True)),
        ))
        db.send_create_signal('main', ['InventorySourceNew'])

        # Adding model 'JobTemplateNew'
        db.create_table('main_jobtemplatenew', (
            (u'unifiedjobtemplate_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJobTemplate'], unique=True, primary_key=True)),
            ('job_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobtemplatenews', null=True, on_delete=models.SET_NULL, to=orm['main.Inventory'])),
            ('playbook', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobtemplatenews', on_delete=models.SET_NULL, default=None, to=orm['main.Credential'], blank=True, null=True)),
            ('cloud_credential', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobtemplatenews_as_cloud_credential+', on_delete=models.SET_NULL, default=None, to=orm['main.Credential'], blank=True, null=True)),
            ('forks', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('limit', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('verbosity', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('extra_vars', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('job_tags', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('host_config_key', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='job_templates', null=True, on_delete=models.SET_NULL, to=orm['main.ProjectNew'])),
        ))
        db.send_create_signal('main', ['JobTemplateNew'])

        # Adding model 'ProjectNew'
        db.create_table(u'main_projectnew', (
            (u'unifiedjobtemplate_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJobTemplate'], unique=True, primary_key=True)),
            ('local_path', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('scm_type', self.gf('django.db.models.fields.CharField')(default='', max_length=8, blank=True)),
            ('scm_url', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('scm_branch', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('scm_clean', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('scm_delete_on_update', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='projectnews', null=True, blank=True, to=orm['main.Credential'])),
            ('scm_delete_on_next_update', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('scm_update_on_launch', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('scm_update_cache_timeout', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('main', ['ProjectNew'])

        # Adding model 'ProjectUpdateNew'
        db.create_table(u'main_projectupdatenew', (
            (u'unifiedjob_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.UnifiedJob'], unique=True, primary_key=True)),
            ('local_path', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('scm_type', self.gf('django.db.models.fields.CharField')(default='', max_length=8, blank=True)),
            ('scm_url', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('scm_branch', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('scm_clean', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('scm_delete_on_update', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='projectupdatenews', null=True, blank=True, to=orm['main.Credential'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='project_updates', to=orm['main.ProjectNew'])),
        ))
        db.send_create_signal('main', ['ProjectUpdateNew'])

        # Adding model 'UnifiedJobTemplate'
        db.create_table(u'main_unifiedjobtemplate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype', self.gf('django.db.models.fields.related.ForeignKey')(related_name='polymorphic_main.unifiedjobtemplate_set', null=True, to=orm['contenttypes.ContentType'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=None)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'unifiedjobtemplate', 'app_label': 'main'}(class)s_created+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name="{'class': 'unifiedjobtemplate', 'app_label': 'main'}(class)s_modified+", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('old_pk', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('current_job', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='unifiedjobtemplate_as_current_job+', null=True, to=orm['main.UnifiedJob'])),
            ('last_job', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='unifiedjobtemplate_as_last_job+', null=True, to=orm['main.UnifiedJob'])),
            ('last_job_failed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_job_run', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('has_schedules', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('next_job_run', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='ok', max_length=32)),
        ))
        db.send_create_signal('main', ['UnifiedJobTemplate'])

        # Adding unique constraint on 'UnifiedJobTemplate', fields ['polymorphic_ctype', 'name']
        db.create_unique(u'main_unifiedjobtemplate', ['polymorphic_ctype_id', 'name'])


        # Changing field 'Profile.created'
        db.alter_column(u'main_profile', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Profile.modified'
        db.alter_column(u'main_profile', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'ProjectUpdate.local_path'
        db.add_column(u'main_projectupdate', 'local_path',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'ProjectUpdate.scm_type'
        db.add_column(u'main_projectupdate', 'scm_type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=8, blank=True),
                      keep_default=False)

        # Adding field 'ProjectUpdate.scm_url'
        db.add_column(u'main_projectupdate', 'scm_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'ProjectUpdate.scm_branch'
        db.add_column(u'main_projectupdate', 'scm_branch',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True),
                      keep_default=False)

        # Adding field 'ProjectUpdate.scm_clean'
        db.add_column(u'main_projectupdate', 'scm_clean',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'ProjectUpdate.scm_delete_on_update'
        db.add_column(u'main_projectupdate', 'scm_delete_on_update',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'ProjectUpdate.credential'
        db.add_column(u'main_projectupdate', 'credential',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='projectupdates', null=True, blank=True, to=orm['main.Credential']),
                      keep_default=False)


        # Changing field 'ProjectUpdate.created'
        db.alter_column(u'main_projectupdate', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'ProjectUpdate.modified'
        db.alter_column(u'main_projectupdate', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding M2M table for field new_inventory_sources on 'Group'
        m2m_table_name = db.shorten_name(u'main_group_new_inventory_sources')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('inventorysourcenew', models.ForeignKey(orm['main.inventorysourcenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'inventorysourcenew_id'])


        # Changing field 'Group.created'
        db.alter_column(u'main_group', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Group.modified'
        db.alter_column(u'main_group', 'modified', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Job.created'
        db.alter_column(u'main_job', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Job.modified'
        db.alter_column(u'main_job', 'modified', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Inventory.created'
        db.alter_column(u'main_inventory', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Inventory.modified'
        db.alter_column(u'main_inventory', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'Host.new_last_job'
        db.add_column(u'main_host', 'new_last_job',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts_as_last_job+', on_delete=models.SET_NULL, default=None, to=orm['main.JobNew'], blank=True, null=True),
                      keep_default=False)

        # Adding M2M table for field new_inventory_sources on 'Host'
        m2m_table_name = db.shorten_name(u'main_host_new_inventory_sources')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('inventorysourcenew', models.ForeignKey(orm['main.inventorysourcenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['host_id', 'inventorysourcenew_id'])


        # Changing field 'Host.created'
        db.alter_column(u'main_host', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Host.modified'
        db.alter_column(u'main_host', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'JobHostSummary.new_job'
        db.add_column(u'main_jobhostsummary', 'new_job',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='new_job_host_summaries', null=True, to=orm['main.JobNew']),
                      keep_default=False)


        # Changing field 'JobHostSummary.created'
        db.alter_column(u'main_jobhostsummary', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'JobHostSummary.modified'
        db.alter_column(u'main_jobhostsummary', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding unique constraint on 'JobHostSummary', fields ['new_job', 'host']
        db.create_unique(u'main_jobhostsummary', ['new_job_id', 'host_id'])

        # Adding field 'InventoryUpdate.source'
        db.add_column(u'main_inventoryupdate', 'source',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True),
                      keep_default=False)

        # Adding field 'InventoryUpdate.source_path'
        db.add_column(u'main_inventoryupdate', 'source_path',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'InventoryUpdate.source_vars'
        db.add_column(u'main_inventoryupdate', 'source_vars',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'InventoryUpdate.credential'
        db.add_column(u'main_inventoryupdate', 'credential',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='inventoryupdates', null=True, blank=True, to=orm['main.Credential']),
                      keep_default=False)

        # Adding field 'InventoryUpdate.source_regions'
        db.add_column(u'main_inventoryupdate', 'source_regions',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'InventoryUpdate.overwrite'
        db.add_column(u'main_inventoryupdate', 'overwrite',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'InventoryUpdate.overwrite_vars'
        db.add_column(u'main_inventoryupdate', 'overwrite_vars',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


        # Changing field 'InventoryUpdate.created'
        db.alter_column(u'main_inventoryupdate', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'InventoryUpdate.modified'
        db.alter_column(u'main_inventoryupdate', 'modified', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Credential.created'
        db.alter_column(u'main_credential', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Credential.modified'
        db.alter_column(u'main_credential', 'modified', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'JobTemplate.created'
        db.alter_column(u'main_jobtemplate', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'JobTemplate.modified'
        db.alter_column(u'main_jobtemplate', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding M2M table for field unified_job_template on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_unified_job_template')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('unifiedjobtemplate', models.ForeignKey(orm['main.unifiedjobtemplate'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'unifiedjobtemplate_id'])

        # Adding M2M table for field unified_job on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_unified_job')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('unifiedjob', models.ForeignKey(orm['main.unifiedjob'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'unifiedjob_id'])

        # Adding M2M table for field new_inventory_source on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_inventory_source')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('inventorysourcenew', models.ForeignKey(orm['main.inventorysourcenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'inventorysourcenew_id'])

        # Adding M2M table for field new_inventory_update on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_inventory_update')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('inventoryupdatenew', models.ForeignKey(orm['main.inventoryupdatenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'inventoryupdatenew_id'])

        # Adding M2M table for field new_project on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_project')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('projectnew', models.ForeignKey(orm['main.projectnew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'projectnew_id'])

        # Adding M2M table for field new_project_update on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_project_update')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('projectupdatenew', models.ForeignKey(orm['main.projectupdatenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'projectupdatenew_id'])

        # Adding M2M table for field new_job_template on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_job_template')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('jobtemplatenew', models.ForeignKey(orm['main.jobtemplatenew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'jobtemplatenew_id'])

        # Adding M2M table for field new_job on 'ActivityStream'
        m2m_table_name = db.shorten_name(u'main_activitystream_new_job')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('activitystream', models.ForeignKey(orm['main.activitystream'], null=False)),
            ('jobnew', models.ForeignKey(orm['main.jobnew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['activitystream_id', 'jobnew_id'])

        # Adding M2M table for field new_projects on 'Team'
        m2m_table_name = db.shorten_name(u'main_team_new_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('projectnew', models.ForeignKey(orm['main.projectnew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['team_id', 'projectnew_id'])


        # Changing field 'Team.created'
        db.alter_column(u'main_team', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Team.modified'
        db.alter_column(u'main_team', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'Project.scm_update_cache_timeout'
        db.add_column(u'main_project', 'scm_update_cache_timeout',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


        # Changing field 'Project.created'
        db.alter_column(u'main_project', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Project.modified'
        db.alter_column(u'main_project', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding M2M table for field new_projects on 'Organization'
        m2m_table_name = db.shorten_name(u'main_organization_new_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('projectnew', models.ForeignKey(orm['main.projectnew'], null=False))
        ))
        db.create_unique(m2m_table_name, ['organization_id', 'projectnew_id'])


        # Changing field 'Organization.created'
        db.alter_column(u'main_organization', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Organization.modified'
        db.alter_column(u'main_organization', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'Permission.new_project'
        db.add_column(u'main_permission', 'new_project',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='permissions', null=True, on_delete=models.SET_NULL, to=orm['main.ProjectNew']),
                      keep_default=False)


        # Changing field 'Permission.created'
        db.alter_column(u'main_permission', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'Permission.modified'
        db.alter_column(u'main_permission', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Deleting field 'InventorySource.update_interval'
        db.delete_column(u'main_inventorysource', 'update_interval')

        # Adding field 'InventorySource.update_cache_timeout'
        db.add_column(u'main_inventorysource', 'update_cache_timeout',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


        # Changing field 'InventorySource.created'
        db.alter_column(u'main_inventorysource', 'created', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'InventorySource.modified'
        db.alter_column(u'main_inventorysource', 'modified', self.gf('django.db.models.fields.DateTimeField')())
        # Adding field 'JobEvent.role'
        db.add_column(u'main_jobevent', 'role',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'JobEvent.new_job'
        db.add_column(u'main_jobevent', 'new_job',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='new_job_events', null=True, to=orm['main.JobNew']),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'JobHostSummary', fields ['new_job', 'host']
        db.delete_unique(u'main_jobhostsummary', ['new_job_id', 'host_id'])

        # Removing unique constraint on 'UnifiedJobTemplate', fields ['polymorphic_ctype', 'name']
        db.delete_unique(u'main_unifiedjobtemplate', ['polymorphic_ctype_id', 'name'])

        # Deleting model 'InventoryUpdateNew'
        db.delete_table(u'main_inventoryupdatenew')

        # Deleting model 'JobNew'
        db.delete_table(u'main_jobnew')

        # Deleting model 'UnifiedJob'
        db.delete_table(u'main_unifiedjob')

        # Removing M2M table for field depends_on on 'UnifiedJob'
        db.delete_table(db.shorten_name(u'main_unifiedjob_depends_on'))

        # Deleting model 'Schedule'
        db.delete_table(u'main_schedule')

        # Deleting model 'InventorySourceNew'
        db.delete_table(u'main_inventorysourcenew')

        # Deleting model 'JobTemplateNew'
        db.delete_table('main_jobtemplatenew')

        # Deleting model 'ProjectNew'
        db.delete_table(u'main_projectnew')

        # Deleting model 'ProjectUpdateNew'
        db.delete_table(u'main_projectupdatenew')

        # Deleting model 'UnifiedJobTemplate'
        db.delete_table(u'main_unifiedjobtemplate')


        # Changing field 'Profile.created'
        db.alter_column(u'main_profile', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Profile.modified'
        db.alter_column(u'main_profile', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'ProjectUpdate.local_path'
        db.delete_column(u'main_projectupdate', 'local_path')

        # Deleting field 'ProjectUpdate.scm_type'
        db.delete_column(u'main_projectupdate', 'scm_type')

        # Deleting field 'ProjectUpdate.scm_url'
        db.delete_column(u'main_projectupdate', 'scm_url')

        # Deleting field 'ProjectUpdate.scm_branch'
        db.delete_column(u'main_projectupdate', 'scm_branch')

        # Deleting field 'ProjectUpdate.scm_clean'
        db.delete_column(u'main_projectupdate', 'scm_clean')

        # Deleting field 'ProjectUpdate.scm_delete_on_update'
        db.delete_column(u'main_projectupdate', 'scm_delete_on_update')

        # Deleting field 'ProjectUpdate.credential'
        db.delete_column(u'main_projectupdate', 'credential_id')


        # Changing field 'ProjectUpdate.created'
        db.alter_column(u'main_projectupdate', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ProjectUpdate.modified'
        db.alter_column(u'main_projectupdate', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Removing M2M table for field new_inventory_sources on 'Group'
        db.delete_table(db.shorten_name(u'main_group_new_inventory_sources'))


        # Changing field 'Group.created'
        db.alter_column(u'main_group', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Group.modified'
        db.alter_column(u'main_group', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Job.created'
        db.alter_column(u'main_job', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Job.modified'
        db.alter_column(u'main_job', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Inventory.created'
        db.alter_column(u'main_inventory', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Inventory.modified'
        db.alter_column(u'main_inventory', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'Host.new_last_job'
        db.delete_column(u'main_host', 'new_last_job_id')

        # Removing M2M table for field new_inventory_sources on 'Host'
        db.delete_table(db.shorten_name(u'main_host_new_inventory_sources'))


        # Changing field 'Host.created'
        db.alter_column(u'main_host', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Host.modified'
        db.alter_column(u'main_host', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'JobHostSummary.new_job'
        db.delete_column(u'main_jobhostsummary', 'new_job_id')


        # Changing field 'JobHostSummary.created'
        db.alter_column(u'main_jobhostsummary', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'JobHostSummary.modified'
        db.alter_column(u'main_jobhostsummary', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'InventoryUpdate.source'
        db.delete_column(u'main_inventoryupdate', 'source')

        # Deleting field 'InventoryUpdate.source_path'
        db.delete_column(u'main_inventoryupdate', 'source_path')

        # Deleting field 'InventoryUpdate.source_vars'
        db.delete_column(u'main_inventoryupdate', 'source_vars')

        # Deleting field 'InventoryUpdate.credential'
        db.delete_column(u'main_inventoryupdate', 'credential_id')

        # Deleting field 'InventoryUpdate.source_regions'
        db.delete_column(u'main_inventoryupdate', 'source_regions')

        # Deleting field 'InventoryUpdate.overwrite'
        db.delete_column(u'main_inventoryupdate', 'overwrite')

        # Deleting field 'InventoryUpdate.overwrite_vars'
        db.delete_column(u'main_inventoryupdate', 'overwrite_vars')


        # Changing field 'InventoryUpdate.created'
        db.alter_column(u'main_inventoryupdate', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'InventoryUpdate.modified'
        db.alter_column(u'main_inventoryupdate', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Credential.created'
        db.alter_column(u'main_credential', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Credential.modified'
        db.alter_column(u'main_credential', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'JobTemplate.created'
        db.alter_column(u'main_jobtemplate', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'JobTemplate.modified'
        db.alter_column(u'main_jobtemplate', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Removing M2M table for field unified_job_template on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_unified_job_template'))

        # Removing M2M table for field unified_job on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_unified_job'))

        # Removing M2M table for field new_inventory_source on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_inventory_source'))

        # Removing M2M table for field new_inventory_update on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_inventory_update'))

        # Removing M2M table for field new_project on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_project'))

        # Removing M2M table for field new_project_update on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_project_update'))

        # Removing M2M table for field new_job_template on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_job_template'))

        # Removing M2M table for field new_job on 'ActivityStream'
        db.delete_table(db.shorten_name(u'main_activitystream_new_job'))

        # Removing M2M table for field new_projects on 'Team'
        db.delete_table(db.shorten_name(u'main_team_new_projects'))


        # Changing field 'Team.created'
        db.alter_column(u'main_team', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Team.modified'
        db.alter_column(u'main_team', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'Project.scm_update_cache_timeout'
        db.delete_column(u'main_project', 'scm_update_cache_timeout')


        # Changing field 'Project.created'
        db.alter_column(u'main_project', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Project.modified'
        db.alter_column(u'main_project', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Removing M2M table for field new_projects on 'Organization'
        db.delete_table(db.shorten_name(u'main_organization_new_projects'))


        # Changing field 'Organization.created'
        db.alter_column(u'main_organization', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Organization.modified'
        db.alter_column(u'main_organization', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'Permission.new_project'
        db.delete_column(u'main_permission', 'new_project_id')


        # Changing field 'Permission.created'
        db.alter_column(u'main_permission', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Permission.modified'
        db.alter_column(u'main_permission', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Adding field 'InventorySource.update_interval'
        db.add_column(u'main_inventorysource', 'update_interval',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Deleting field 'InventorySource.update_cache_timeout'
        db.delete_column(u'main_inventorysource', 'update_cache_timeout')


        # Changing field 'InventorySource.created'
        db.alter_column(u'main_inventorysource', 'created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'InventorySource.modified'
        db.alter_column(u'main_inventorysource', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))
        # Deleting field 'JobEvent.role'
        db.delete_column(u'main_jobevent', 'role')

        # Deleting field 'JobEvent.new_job'
        db.delete_column(u'main_jobevent', 'new_job_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.activitystream': {
            'Meta': {'object_name': 'ActivityStream'},
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'activity_stream'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'changes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Credential']", 'symmetrical': 'False', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Host']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Inventory']", 'symmetrical': 'False', 'blank': 'True'}),
            'inventory_source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventorySource']", 'symmetrical': 'False', 'blank': 'True'}),
            'inventory_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventoryUpdate']", 'symmetrical': 'False', 'blank': 'True'}),
            'job': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Job']", 'symmetrical': 'False', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.JobTemplate']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_inventory_source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventorySourceNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_inventory_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventoryUpdateNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_job': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.JobNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_job_template': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.JobTemplateNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_project': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ProjectNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_project_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ProjectUpdateNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'object1': ('django.db.models.fields.TextField', [], {}),
            'object2': ('django.db.models.fields.TextField', [], {}),
            'object_relationship_type': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'operation': ('django.db.models.fields.CharField', [], {'max_length': '13'}),
            'organization': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Organization']", 'symmetrical': 'False', 'blank': 'True'}),
            'permission': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Project']", 'symmetrical': 'False', 'blank': 'True'}),
            'project_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ProjectUpdate']", 'symmetrical': 'False', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Team']", 'symmetrical': 'False', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unified_job': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'activity_stream_as_unified_job+'", 'blank': 'True', 'to': "orm['main.UnifiedJob']"}),
            'unified_job_template': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'activity_stream_as_unified_job_template+'", 'blank': 'True', 'to': "orm['main.UnifiedJobTemplate']"}),
            'user': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'main.authtoken': {
            'Meta': {'object_name': 'AuthToken'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'request_hash': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_tokens'", 'to': u"orm['auth.User']"})
        },
        'main.credential': {
            'Meta': {'unique_together': "[('user', 'team', 'kind', 'name')]", 'object_name': 'Credential'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cloud': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'credential\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'ssh'", 'max_length': '32'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'credential\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'credentials'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'credentials'", 'null': 'True', 'blank': 'True', 'to': u"orm['auth.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'})
        },
        'main.group': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Group'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'groups_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.Host']"}),
            'hosts_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Inventory']"}),
            'inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.InventorySource']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'new_inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.InventorySourceNew']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'children'", 'blank': 'True', 'to': "orm['main.Group']"}),
            'total_groups': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_hosts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'main.host': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'hosts'", 'blank': 'True', 'to': "orm['main.InventorySource']"}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Job']", 'blank': 'True', 'null': 'True'}),
            'last_job_host_summary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job_summary+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobHostSummary']", 'blank': 'True', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'new_inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'hosts'", 'blank': 'True', 'to': "orm['main.InventorySourceNew']"}),
            'new_last_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobNew']", 'blank': 'True', 'null': 'True'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'main.inventory': {
            'Meta': {'unique_together': "[('name', 'organization')]", 'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'groups_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hosts_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_sources_with_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'to': "orm['main.Organization']"}),
            'total_groups': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_hosts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_inventory_sources': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'main.inventorysource': {
            'Meta': {'object_name': 'InventorySource'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventorysources'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_current_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_last_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '32'}),
            'update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'main.inventorysourcenew': {
            'Meta': {'object_name': 'InventorySourceNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventorysourcenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'new_inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'unifiedjobtemplate_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJobTemplate']", 'unique': 'True', 'primary_key': 'True'}),
            'update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'main.inventoryupdate': {
            'Meta': {'object_name': 'InventoryUpdate'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventoryupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': "orm['main.InventorySource']"}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'license_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.inventoryupdatenew': {
            'Meta': {'object_name': 'InventoryUpdateNew', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventoryupdatenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': "orm['main.InventorySourceNew']"}),
            'license_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'unifiedjob_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJob']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.job': {
            'Meta': {'object_name': 'Job'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'blank': 'True', 'through': "orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobTemplate']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'launch_type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobevent': {
            'Meta': {'ordering': "('pk',)", 'object_name': 'JobEvent'},
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events_as_primary_host'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Host']", 'blank': 'True', 'null': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'job_events'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'new_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_job_events'", 'null': 'True', 'to': "orm['main.JobNew']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobEvent']", 'blank': 'True', 'null': 'True'}),
            'play': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'})
        },
        'main.jobhostsummary': {
            'Meta': {'ordering': "('-pk',)", 'unique_together': "[('job', 'host'), ('new_job', 'host')]", 'object_name': 'JobHostSummary'},
            'changed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'dark': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'new_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_job_host_summaries'", 'null': 'True', 'to': "orm['main.JobNew']"}),
            'ok': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skipped': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'main.jobnew': {
            'Meta': {'object_name': 'JobNew', '_ormbases': ['main.UnifiedJob']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobnews'", 'blank': 'True', 'through': "orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobTemplateNew']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
            u'unifiedjob_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJob']", 'unique': 'True', 'primary_key': 'True'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobtemplatenew': {
            'Meta': {'object_name': 'JobTemplateNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
            u'unifiedjobtemplate_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJobTemplate']", 'unique': 'True', 'primary_key': 'True'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'admin_of_organizations'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'new_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': "orm['main.ProjectNew']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': "orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'new_project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        'main.profile': {
            'Meta': {'object_name': 'Profile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ldap_dn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'user': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projects'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_current_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_last_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_next_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'scm_update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'ok'", 'max_length': '32', 'null': 'True'})
        },
        'main.projectnew': {
            'Meta': {'object_name': 'ProjectNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectnews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_next_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'scm_update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            u'unifiedjobtemplate_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJobTemplate']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.projectupdate': {
            'Meta': {'object_name': 'ProjectUpdate'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': "orm['main.Project']"}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.projectupdatenew': {
            'Meta': {'object_name': 'ProjectUpdateNew', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectupdatenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': "orm['main.ProjectNew']"}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            u'unifiedjob_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJob']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.schedule': {
            'Meta': {'object_name': 'Schedule'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'schedule\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'dtend': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'dtstart': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'schedules'", 'to': "orm['main.UnifiedJobTemplate']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'schedule\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'rrule': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.team': {
            'Meta': {'unique_together': "[('organization', 'name')]", 'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'new_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': "orm['main.ProjectNew']"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': "orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.unifiedjob': {
            'Meta': {'object_name': 'UnifiedJob'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'unifiedjob\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'depends_on': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'depends_on_rel_+'", 'to': "orm['main.UnifiedJob']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'elapsed': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '3'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'launch_type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'unifiedjob\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'old_pk': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polymorphic_main.unifiedjob_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_stdout_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'schedule': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['main.Schedule']", 'null': 'True'}),
            'start_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
            'unified_job_template': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'unifiedjob_unified_jobs'", 'null': 'True', 'to': "orm['main.UnifiedJobTemplate']"})
        },
        'main.unifiedjobtemplate': {
            'Meta': {'unique_together': "[('polymorphic_ctype', 'name')]", 'object_name': 'UnifiedJobTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'unifiedjobtemplate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'current_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'unifiedjobtemplate_as_current_job+'", 'null': 'True', 'to': "orm['main.UnifiedJob']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'has_schedules': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'unifiedjobtemplate_as_last_job+'", 'null': 'True', 'to': "orm['main.UnifiedJob']"}),
            'last_job_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_job_run': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'unifiedjobtemplate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'next_job_run': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'old_pk': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polymorphic_main.unifiedjobtemplate_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'ok'", 'max_length': '32'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['main']