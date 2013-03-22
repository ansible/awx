# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'User'
        db.delete_table(u'main_user')

        # Removing M2M table for field tags on 'User'
        db.delete_table('main_user_tags')

        # Removing M2M table for field audit_trail on 'User'
        db.delete_table('main_user_audit_trail')


        # Changing field 'Inventory.creation_date'
        db.alter_column(u'main_inventory', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'Inventory', fields ['name']
        db.create_unique(u'main_inventory', ['name'])


        # Changing field 'Host.creation_date'
        db.alter_column(u'main_host', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'Host', fields ['name']
        db.create_unique(u'main_host', ['name'])

        # Adding unique constraint on 'LaunchJob', fields ['name']
        db.create_unique(u'main_launchjob', ['name'])


        # Changing field 'LaunchJob.creation_date'
        db.alter_column(u'main_launchjob', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

        # Changing field 'LaunchJob.user'
        db.alter_column(u'main_launchjob', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['auth.User'], null=True))

        # Changing field 'Group.creation_date'
        db.alter_column(u'main_group', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'Group', fields ['name']
        db.create_unique(u'main_group', ['name'])

        # Adding unique constraint on 'Credential', fields ['name']
        db.create_unique(u'main_credential', ['name'])


        # Changing field 'Credential.creation_date'
        db.alter_column(u'main_credential', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

        # Changing field 'Credential.user'
        db.alter_column(u'main_credential', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['auth.User'], null=True))

        # Changing field 'AuditTrail.modified_by'
        db.alter_column(u'main_audittrail', 'modified_by_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, on_delete=models.SET_NULL))

        # Changing field 'AuditTrail.creation_date'
        db.alter_column(u'main_audittrail', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'AuditTrail', fields ['name']
        db.create_unique(u'main_audittrail', ['name'])

        # Adding unique constraint on 'Team', fields ['name']
        db.create_unique(u'main_team', ['name'])


        # Changing field 'Team.creation_date'
        db.alter_column(u'main_team', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'Project', fields ['name']
        db.create_unique(u'main_project', ['name'])


        # Changing field 'Project.creation_date'
        db.alter_column(u'main_project', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

        # Changing field 'Permission.creation_date'
        db.alter_column(u'main_permission', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

        # Changing field 'Permission.user'
        db.alter_column(u'main_permission', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['auth.User']))
        # Adding unique constraint on 'Permission', fields ['name']
        db.create_unique(u'main_permission', ['name'])


        # Changing field 'LaunchJobStatus.creation_date'
        db.alter_column(u'main_launchjobstatus', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'LaunchJobStatus', fields ['name']
        db.create_unique(u'main_launchjobstatus', ['name'])


        # Changing field 'VariableData.creation_date'
        db.alter_column(u'main_variabledata', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))
        # Adding unique constraint on 'VariableData', fields ['name']
        db.create_unique(u'main_variabledata', ['name'])

        # Adding unique constraint on 'Organization', fields ['name']
        db.create_unique(u'main_organization', ['name'])


        # Changing field 'Organization.creation_date'
        db.alter_column(u'main_organization', 'creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True))

    def backwards(self, orm):
        # Removing unique constraint on 'Organization', fields ['name']
        db.delete_unique(u'main_organization', ['name'])

        # Removing unique constraint on 'VariableData', fields ['name']
        db.delete_unique(u'main_variabledata', ['name'])

        # Removing unique constraint on 'LaunchJobStatus', fields ['name']
        db.delete_unique(u'main_launchjobstatus', ['name'])

        # Removing unique constraint on 'Permission', fields ['name']
        db.delete_unique(u'main_permission', ['name'])

        # Removing unique constraint on 'Project', fields ['name']
        db.delete_unique(u'main_project', ['name'])

        # Removing unique constraint on 'Team', fields ['name']
        db.delete_unique(u'main_team', ['name'])

        # Removing unique constraint on 'AuditTrail', fields ['name']
        db.delete_unique(u'main_audittrail', ['name'])

        # Removing unique constraint on 'Credential', fields ['name']
        db.delete_unique(u'main_credential', ['name'])

        # Removing unique constraint on 'Group', fields ['name']
        db.delete_unique(u'main_group', ['name'])

        # Removing unique constraint on 'LaunchJob', fields ['name']
        db.delete_unique(u'main_launchjob', ['name'])

        # Removing unique constraint on 'Host', fields ['name']
        db.delete_unique(u'main_host', ['name'])

        # Removing unique constraint on 'Inventory', fields ['name']
        db.delete_unique(u'main_inventory', ['name'])

        # Adding model 'User'
        db.create_table(u'main_user', (
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('auth_user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='application_user', unique=True, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['User'])

        # Adding M2M table for field tags on 'User'
        db.create_table(u'main_user_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['main.user'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_user_tags', ['user_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'User'
        db.create_table(u'main_user_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['main.user'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_user_audit_trail', ['user_id', 'audittrail_id'])


        # Changing field 'Inventory.creation_date'
        db.alter_column(u'main_inventory', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Host.creation_date'
        db.alter_column(u'main_host', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'LaunchJob.creation_date'
        db.alter_column(u'main_launchjob', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'LaunchJob.user'
        db.alter_column(u'main_launchjob', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.User'], null=True))

        # Changing field 'Group.creation_date'
        db.alter_column(u'main_group', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Credential.creation_date'
        db.alter_column(u'main_credential', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Credential.user'
        db.alter_column(u'main_credential', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.User'], null=True))

        # Changing field 'AuditTrail.modified_by'
        db.alter_column(u'main_audittrail', 'modified_by_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User'], null=True, on_delete=models.SET_NULL))

        # Changing field 'AuditTrail.creation_date'
        db.alter_column(u'main_audittrail', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Team.creation_date'
        db.alter_column(u'main_team', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Project.creation_date'
        db.alter_column(u'main_project', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Permission.creation_date'
        db.alter_column(u'main_permission', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Permission.user'
        db.alter_column(u'main_permission', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.User'], on_delete=models.SET_NULL))

        # Changing field 'LaunchJobStatus.creation_date'
        db.alter_column(u'main_launchjobstatus', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'VariableData.creation_date'
        db.alter_column(u'main_variabledata', 'creation_date', self.gf('django.db.models.fields.DateField')())

        # Changing field 'Organization.creation_date'
        db.alter_column(u'main_organization', 'creation_date', self.gf('django.db.models.fields.DateField')())

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
        'main.audittrail': {
            'Meta': {'object_name': 'AuditTrail'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'audittrail_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delta': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'detail': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Tag']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'audittrail_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.credential': {
            'Meta': {'object_name': 'Credential'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'credential_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4096', 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'credential_tags'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Team']", 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.group': {
            'Meta': {'object_name': 'Group'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'group_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents_rel_+'", 'blank': 'True', 'to': "orm['main.Group']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'group_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.host': {
            'Meta': {'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.inventory': {
            'Meta': {'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inventory_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inventory_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.launchjob': {
            'Meta': {'object_name': 'LaunchJob'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjob_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Inventory']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjob_tags'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.launchjobstatus': {
            'Meta': {'object_name': 'LaunchJobStatus'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjobstatus_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_statuses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.LaunchJob']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'result_data': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjobstatus_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'admin_of_organizations'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organization_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organization_tags'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'permission_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'permission_tags'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'project_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_playbook': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['main.Inventory']"}),
            'local_repository': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'project_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'main.team': {
            'Meta': {'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'team_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'team_tags'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.variabledata': {
            'Meta': {'object_name': 'VariableData'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'variabledata_audit_trails'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Group']"}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'variabledata_tags'", 'blank': 'True', 'to': "orm['main.Tag']"})
        }
    }

    complete_apps = ['main']