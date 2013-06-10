# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    '''
    Schema migration for AnsibleWorks 1.2-b2 release.
    - Adds variables field on Host and Group models.
    - Adds job_tags and host_config_key fields on JobTemplate.
    - Adds job_tags, job_args, job_cwd, job_env fields on Job.
    - Adds failed field on JobHostSummary.
    - Adds play, task, parent and hosts fields on JobEvent.

    NOTE: This migration has been manually edited!
    '''

    def forwards(self, orm):

        # Adding field 'Host.variables'
        db.add_column(u'main_host', 'variables',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True, null=True),
                      keep_default=False)

        # Adding field 'Group.variables'
        db.add_column(u'main_group', 'variables',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True, null=True),
                      keep_default=False)

        # Adding field 'JobTemplate.job_tags'
        db.add_column(u'main_jobtemplate', 'job_tags',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'JobTemplate.host_config_key'
        db.add_column(u'main_jobtemplate', 'host_config_key',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True, null=True),
                      keep_default=False)

        # Adding field 'Job.job_tags'
        db.add_column(u'main_job', 'job_tags',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Job.job_args'
        db.add_column(u'main_job', 'job_args',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Job.job_cwd'
        db.add_column(u'main_job', 'job_cwd',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Job.job_env'
        db.add_column(u'main_job', 'job_env',
                      self.gf('jsonfield.fields.JSONField')(default={}, null=True, blank=True),
                      keep_default=False)

        # Adding field 'JobHostSummary.failed'
        db.add_column(u'main_jobhostsummary', 'failed',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'JobEvent.play'
        db.add_column(u'main_jobevent', 'play',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True, null=True),
                      keep_default=False)

        # Adding field 'JobEvent.task'
        db.add_column(u'main_jobevent', 'task',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True, null=True),
                      keep_default=False)

        # Adding field 'JobEvent.parent'
        db.add_column(u'main_jobevent', 'parent',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', on_delete=models.SET_NULL, default=None, to=orm['main.JobEvent'], blank=True, null=True),
                      keep_default=False)

        # Adding M2M table for field hosts on 'JobEvent'
        m2m_table_name = db.shorten_name(u'main_jobevent_hosts')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('jobevent', models.ForeignKey(orm['main.jobevent'], null=False)),
            ('host', models.ForeignKey(orm['main.host'], null=False))
        ))
        db.create_unique(m2m_table_name, ['jobevent_id', 'host_id'])

        # Removing M2M table for field tags on 'Job'
        db.delete_table(db.shorten_name(u'main_job_tags'))

        # Removing M2M table for field audit_trail on 'Job'
        db.delete_table(db.shorten_name(u'main_job_audit_trail'))

        # Removing M2M table for field tags on 'Inventory'
        db.delete_table(db.shorten_name(u'main_inventory_tags'))

        # Removing M2M table for field audit_trail on 'Inventory'
        db.delete_table(db.shorten_name(u'main_inventory_audit_trail'))

        # Removing M2M table for field tags on 'Host'
        db.delete_table(db.shorten_name(u'main_host_tags'))

        # Removing M2M table for field audit_trail on 'Host'
        db.delete_table(db.shorten_name(u'main_host_audit_trail'))

        # Removing M2M table for field tags on 'Group'
        db.delete_table(db.shorten_name(u'main_group_tags'))

        # Removing M2M table for field audit_trail on 'Group'
        db.delete_table(db.shorten_name(u'main_group_audit_trail'))

        # Removing M2M table for field audit_trail on 'Credential'
        db.delete_table(db.shorten_name(u'main_credential_audit_trail'))

        # Removing M2M table for field tags on 'Credential'
        db.delete_table(db.shorten_name(u'main_credential_tags'))

        # Removing M2M table for field tags on 'JobTemplate'
        db.delete_table(db.shorten_name(u'main_jobtemplate_tags'))

        # Removing M2M table for field audit_trail on 'JobTemplate'
        db.delete_table(db.shorten_name(u'main_jobtemplate_audit_trail'))

        # Removing M2M table for field tags on 'Team'
        db.delete_table(db.shorten_name(u'main_team_tags'))

        # Removing M2M table for field audit_trail on 'Team'
        db.delete_table(db.shorten_name(u'main_team_audit_trail'))

        # Removing M2M table for field tags on 'Project'
        db.delete_table(db.shorten_name(u'main_project_tags'))

        # Removing M2M table for field audit_trail on 'Project'
        db.delete_table(db.shorten_name(u'main_project_audit_trail'))

        # Removing M2M table for field tags on 'Permission'
        db.delete_table(db.shorten_name(u'main_permission_tags'))

        # Removing M2M table for field audit_trail on 'Permission'
        db.delete_table(db.shorten_name(u'main_permission_audit_trail'))

        # Removing M2M table for field tags on 'VariableData'
        db.delete_table(db.shorten_name(u'main_variabledata_tags'))

        # Removing M2M table for field audit_trail on 'VariableData'
        db.delete_table(db.shorten_name(u'main_variabledata_audit_trail'))

        # Removing M2M table for field tags on 'Organization'
        db.delete_table(db.shorten_name(u'main_organization_tags'))

        # Removing M2M table for field audit_trail on 'Organization'
        db.delete_table(db.shorten_name(u'main_organization_audit_trail'))

        # Deleting model 'Tag'
        db.delete_table(u'main_tag')

        # Deleting model 'AuditTrail'
        db.delete_table(u'main_audittrail')

    def backwards(self, orm):

        # Deleting field 'Host.variables'
        db.delete_column(u'main_host', 'variables')

        # Deleting field 'Group.variables'
        db.delete_column(u'main_group', 'variables')

        # Deleting field 'JobTemplate.job_tags'
        db.delete_column(u'main_jobtemplate', 'job_tags')

        # Deleting field 'JobTemplate.host_config_key'
        db.delete_column(u'main_jobtemplate', 'host_config_key')

        # Deleting field 'Job.job_tags'
        db.delete_column(u'main_job', 'job_tags')

        # Deleting field 'Job.job_args'
        db.delete_column(u'main_job', 'job_args')

        # Deleting field 'Job.job_cwd'
        db.delete_column(u'main_job', 'job_cwd')

        # Deleting field 'Job.job_env'
        db.delete_column(u'main_job', 'job_env')

        # Deleting field 'JobHostSummary.failed'
        db.delete_column(u'main_jobhostsummary', 'failed')

        # Deleting field 'JobEvent.play'
        db.delete_column(u'main_jobevent', 'play')

        # Deleting field 'JobEvent.task'
        db.delete_column(u'main_jobevent', 'task')

        # Deleting field 'JobEvent.parent'
        db.delete_column(u'main_jobevent', 'parent_id')

        # Removing M2M table for field hosts on 'JobEvent'
        db.delete_table(db.shorten_name(u'main_jobevent_hosts'))

        # Adding model 'AuditTrail'
        db.create_table(u'main_audittrail', (
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('delta', self.gf('django.db.models.fields.TextField')()),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Tag'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('detail', self.gf('django.db.models.fields.TextField')()),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['AuditTrail'])

        # Adding model 'Tag'
        db.create_table(u'main_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('main', ['Tag'])

        # Adding M2M table for field tags on 'Job'
        m2m_table_name = db.shorten_name(u'main_job_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('job', models.ForeignKey(orm['main.job'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['job_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Job'
        m2m_table_name = db.shorten_name(u'main_job_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('job', models.ForeignKey(orm['main.job'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['job_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Inventory'
        m2m_table_name = db.shorten_name(u'main_inventory_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['inventory_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Inventory'
        m2m_table_name = db.shorten_name(u'main_inventory_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['inventory_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Host'
        m2m_table_name = db.shorten_name(u'main_host_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['host_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Host'
        m2m_table_name = db.shorten_name(u'main_host_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['host_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Group'
        m2m_table_name = db.shorten_name(u'main_group_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Group'
        m2m_table_name = db.shorten_name(u'main_group_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'audittrail_id'])

        # Adding M2M table for field audit_trail on 'Credential'
        m2m_table_name = db.shorten_name(u'main_credential_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['credential_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Credential'
        m2m_table_name = db.shorten_name(u'main_credential_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['credential_id', 'tag_id'])

        # Adding M2M table for field tags on 'JobTemplate'
        m2m_table_name = db.shorten_name(u'main_jobtemplate_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('jobtemplate', models.ForeignKey(orm['main.jobtemplate'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['jobtemplate_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'JobTemplate'
        m2m_table_name = db.shorten_name(u'main_jobtemplate_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('jobtemplate', models.ForeignKey(orm['main.jobtemplate'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['jobtemplate_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Team'
        m2m_table_name = db.shorten_name(u'main_team_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['team_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Team'
        m2m_table_name = db.shorten_name(u'main_team_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['team_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Project'
        m2m_table_name = db.shorten_name(u'main_project_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['project_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Project'
        m2m_table_name = db.shorten_name(u'main_project_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['project_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Permission'
        m2m_table_name = db.shorten_name(u'main_permission_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Permission'
        m2m_table_name = db.shorten_name(u'main_permission_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['permission_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'VariableData'
        m2m_table_name = db.shorten_name(u'main_variabledata_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['variabledata_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'VariableData'
        m2m_table_name = db.shorten_name(u'main_variabledata_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['variabledata_id', 'audittrail_id'])

        # Adding M2M table for field tags on 'Organization'
        m2m_table_name = db.shorten_name(u'main_organization_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['organization_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Organization'
        m2m_table_name = db.shorten_name(u'main_organization_audit_trail')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(m2m_table_name, ['organization_id', 'audittrail_id'])


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
        'main.credential': {
            'Meta': {'object_name': 'Credential'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'credential\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Team']", 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.group': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Group'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'children'", 'blank': 'True', 'to': "orm['main.Group']"}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True', 'null': 'True'}),
            'variable_data': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'group'", 'unique': 'True', 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.VariableData']", 'blank': 'True', 'null': 'True'})
        },
        'main.host': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Job']", 'blank': 'True', 'null': 'True'}),
            'last_job_host_summary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job_summary+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.JobHostSummary']", 'blank': 'True', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True', 'null': 'True'}),
            'variable_data': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'host'", 'unique': 'True', 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.VariableData']", 'blank': 'True', 'null': 'True'})
        },
        'main.inventory': {
            'Meta': {'unique_together': "(('name', 'organization'),)", 'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'to': "orm['main.Organization']"})
        },
        'main.job': {
            'Meta': {'object_name': 'Job'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'blank': 'True', 'through': u"orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_args': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'null': 'True', 'blank': 'True'}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobTemplate']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'playbook': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobevent': {
            'Meta': {'ordering': "('pk',)", 'object_name': 'JobEvent'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Host']", 'blank': 'True', 'null': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'job_events'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events'", 'to': "orm['main.Job']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobEvent']", 'blank': 'True', 'null': 'True'}),
            'play': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True', 'null': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True', 'null': 'True'})
        },
        u'main.jobhostsummary': {
            'Meta': {'ordering': "('-pk',)", 'unique_together': "[('job', 'host')]", 'object_name': 'JobHostSummary'},
            'changed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'dark': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Job']"}),
            'ok': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skipped': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'main.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'admin_of_organizations'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'project\', \'app_label\': u\'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'})
        },
        'main.team': {
            'Meta': {'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.variabledata': {
            'Meta': {'object_name': 'VariableData'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'variabledata\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'data': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'})
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