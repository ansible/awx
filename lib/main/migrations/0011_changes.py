# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing M2M table for field inventories on 'Project'
        db.delete_table('main_project_inventories')


    def backwards(self, orm):
        # Adding M2M table for field inventories on 'Project'
        db.create_table(u'main_project_inventories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False))
        ))
        db.create_unique(u'main_project_inventories', ['project_id', 'inventory_id'])


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
            'comment': ('django.db.models.fields.TextField', [], {}),
            'delta': ('django.db.models.fields.TextField', [], {}),
            'detail': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Tag']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'main.credential': {
            'Meta': {'object_name': 'Credential'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'credential_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'credential\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'credential_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Team']", 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.group': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Group'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'group_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'children'", 'blank': 'True', 'to': "orm['main.Group']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'group_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'variable_data': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'group'", 'unique': 'True', 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.VariableData']", 'blank': 'True', 'null': 'True'})
        },
        'main.host': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'variable_data': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'host'", 'unique': 'True', 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.VariableData']", 'blank': 'True', 'null': 'True'})
        },
        'main.inventory': {
            'Meta': {'unique_together': "(('name', 'organization'),)", 'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inventory_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'to': "orm['main.Organization']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'inventory_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.launchjob': {
            'Meta': {'object_name': 'LaunchJob'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjob_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'launchjob\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Inventory']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjob_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.launchjobstatus': {
            'Meta': {'object_name': 'LaunchJobStatus'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjobstatus_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'launchjobstatus\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_statuses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.LaunchJob']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'result_stderr': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '20'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjobstatus_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.launchjobstatusevent': {
            'Meta': {'object_name': 'LaunchJobStatusEvent'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'default': "{}", 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_status_events'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Host']", 'blank': 'True', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job_status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_status_events'", 'to': "orm['main.LaunchJobStatus']"})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'admin_of_organizations'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organization_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organization_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'permission_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'permission_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'project_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'project\', \'app_label\': u\'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_playbook': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_repository': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'project_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'main.team': {
            'Meta': {'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'team_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'team_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.variabledata': {
            'Meta': {'object_name': 'VariableData'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'variabledata_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'variabledata\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'variabledata_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        }
    }

    complete_apps = ['main']
