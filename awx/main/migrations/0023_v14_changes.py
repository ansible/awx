# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Credential.ssh_username'
        db.delete_column(u'main_credential', 'ssh_username')

        # Deleting field 'Credential.ssh_password'
        db.delete_column(u'main_credential', 'ssh_password')

        # Adding unique constraint on 'Credential', fields ['user', 'team', 'kind', 'name']
        db.create_unique(u'main_credential', ['user_id', 'team_id', 'kind', 'name'])

        # Deleting field 'Project.scm_password'
        db.delete_column(u'main_project', 'scm_password')

        # Deleting field 'Project.scm_key_unlock'
        db.delete_column(u'main_project', 'scm_key_unlock')

        # Deleting field 'Project.scm_key_data'
        db.delete_column(u'main_project', 'scm_key_data')

        # Deleting field 'Project.scm_username'
        db.delete_column(u'main_project', 'scm_username')

        # Deleting field 'InventorySource.source_tags'
        db.delete_column(u'main_inventorysource', 'source_tags')

        # Deleting field 'InventorySource.source_password'
        db.delete_column(u'main_inventorysource', 'source_password')

        # Deleting field 'InventorySource.source_username'
        db.delete_column(u'main_inventorysource', 'source_username')


    def backwards(self, orm):
        # Removing unique constraint on 'Credential', fields ['user', 'team', 'kind', 'name']
        db.delete_unique(u'main_credential', ['user_id', 'team_id', 'kind', 'name'])

        # Adding field 'Credential.ssh_username'
        db.add_column(u'main_credential', 'ssh_username',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'Credential.ssh_password'
        db.add_column(u'main_credential', 'ssh_password',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'Project.scm_password'
        db.add_column(u'main_project', 'scm_password',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Project.scm_key_unlock'
        db.add_column(u'main_project', 'scm_key_unlock',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Project.scm_key_data'
        db.add_column(u'main_project', 'scm_key_data',
                      self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True),
                      keep_default=False)

        # Adding field 'Project.scm_username'
        db.add_column(u'main_project', 'scm_username',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256, null=True, blank=True),
                      keep_default=False)

        # Adding field 'InventorySource.source_tags'
        db.add_column(u'main_inventorysource', 'source_tags',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'InventorySource.source_password'
        db.add_column(u'main_inventorysource', 'source_password',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)

        # Adding field 'InventorySource.source_username'
        db.add_column(u'main_inventorysource', 'source_username',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True),
                      keep_default=False)


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
        u'main.authtoken': {
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'credential\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'ssh'", 'max_length': '32'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'groups_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.Host']"}),
            'hosts_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Inventory']"}),
            'inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': u"orm['main.InventorySource']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'group\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'children'", 'blank': 'True', 'to': "orm['main.Group']"}),
            'total_groups': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_hosts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'main.host': {
            'Meta': {'unique_together': "(('name', 'inventory'),)", 'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'hosts'", 'blank': 'True', 'to': u"orm['main.InventorySource']"}),
            'last_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Job']", 'blank': 'True', 'null': 'True'}),
            'last_job_host_summary': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job_summary+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.JobHostSummary']", 'blank': 'True', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'main.inventory': {
            'Meta': {'unique_together': "(('name', 'organization'),)", 'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'groups_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'has_active_failures': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_inventory_sources': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hosts_with_active_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_sources_with_failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventory\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'to': "orm['main.Organization']"}),
            'total_groups': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_hosts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_inventory_sources': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'variables': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'})
        },
        u'main.inventorysource': {
            'Meta': {'object_name': 'InventorySource'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': u\'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_sources'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_current_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_last_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': u\'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '32', 'null': 'True'}),
            'update_interval': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'main.inventoryupdate': {
            'Meta': {'object_name': 'InventoryUpdate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': u"orm['main.InventorySource']"}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'license_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.job': {
            'Meta': {'object_name': 'Job'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'blank': 'True', 'through': u"orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
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
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'playbook': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobevent': {
            'Meta': {'ordering': "('pk',)", 'object_name': 'JobEvent'},
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'event_data': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events_as_primary_host'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Host']", 'blank': 'True', 'null': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'job_events'", 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_events'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobEvent']", 'blank': 'True', 'null': 'True'}),
            'play': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'})
        },
        u'main.jobhostsummary': {
            'Meta': {'ordering': "('-pk',)", 'unique_together': "[('job', 'host')]", 'object_name': 'JobHostSummary'},
            'changed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'dark': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'ok': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skipped': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'main.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
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
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'organization\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': u"orm['auth.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'permission\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['main.Project']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'main.profile': {
            'Meta': {'object_name': 'Profile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ldap_dn': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': u\'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projects'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_current_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_last_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': u\'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_next_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'scm_update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'ok'", 'max_length': '32', 'null': 'True'})
        },
        'main.projectupdate': {
            'Meta': {'object_name': 'ProjectUpdate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': u"orm['main.Project']"}),
            'result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.team': {
            'Meta': {'unique_together': "[('organization', 'name')]", 'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'team\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'teams'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['main.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': u"orm['auth.User']"})
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