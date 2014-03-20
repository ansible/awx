# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    '''
    Rename tables/columns to be consistent with model/field names.
    '''

    def forwards(self, orm):
        db.rename_table(u'main_projectnew', 'main_project')
        db.rename_table(u'main_projectupdatenew', 'main_projectupdate')
        db.rename_table(u'main_inventorysourcenew', 'main_inventorysource')
        db.rename_table(u'main_inventoryupdatenew', 'main_inventoryupdate')
        db.rename_table(u'main_jobtemplatenew', 'main_jobtemplate')
        db.rename_table(u'main_jobnew', 'main_job')

        db.rename_table(db.shorten_name(u'main_team_new_projects'), db.shorten_name(u'main_team_projects'))
        db.rename_column(db.shorten_name(u'main_team_projects'), 'projectnew_id', 'project_id')
        db.rename_table(db.shorten_name(u'main_organization_new_projects'), db.shorten_name(u'main_organization_projects'))
        db.rename_column(db.shorten_name(u'main_organization_projects'), 'projectnew_id', 'project_id')
        db.rename_column(u'main_permission', 'new_project_id', 'project_id')

        db.rename_column(u'main_host', 'new_last_job_id', 'last_job_id')
        db.rename_table(db.shorten_name(u'main_host_new_inventory_sources'), db.shorten_name(u'main_host_inventory_sources'))
        db.rename_column(db.shorten_name(u'main_host_inventory_sources'), 'inventorysourcenew_id', 'inventorysource_id')
        db.rename_table(db.shorten_name(u'main_group_new_inventory_sources'), db.shorten_name(u'main_group_inventory_sources'))
        db.rename_column(db.shorten_name(u'main_group_inventory_sources'), 'inventorysourcenew_id', 'inventorysource_id')
        
        db.rename_column(u'main_jobhostsummary', 'new_job_id', 'job_id')
        db.rename_column(u'main_jobevent', 'new_job_id', 'job_id')

        db.rename_table(db.shorten_name(u'main_activitystream_new_project'), db.shorten_name(u'main_activitystream_project'))
        db.rename_column(db.shorten_name(u'main_activitystream_project'), 'projectnew_id', 'project_id')
        db.rename_table(db.shorten_name(u'main_activitystream_new_project_update'), db.shorten_name(u'main_activitystream_project_update'))
        db.rename_column(db.shorten_name(u'main_activitystream_project_update'), 'projectupdatenew_id', 'projectupdate_id')
        db.rename_table(db.shorten_name(u'main_activitystream_new_inventory_source'), db.shorten_name(u'main_activitystream_inventory_source'))
        db.rename_column(db.shorten_name(u'main_activitystream_inventory_source'), 'inventorysourcenew_id', 'inventorysource_id')
        db.rename_table(db.shorten_name(u'main_activitystream_new_inventory_update'), db.shorten_name(u'main_activitystream_inventory_update'))
        db.rename_column(db.shorten_name(u'main_activitystream_inventory_update'), 'inventoryupdatenew_id', 'inventoryupdate_id')
        db.rename_table(db.shorten_name(u'main_activitystream_new_job_template'), db.shorten_name(u'main_activitystream_job_template'))
        db.rename_column(db.shorten_name(u'main_activitystream_job_template'), 'jobtemplatenew_id', 'jobtemplate_id')
        db.rename_table(db.shorten_name(u'main_activitystream_new_job'), db.shorten_name(u'main_activitystream_job'))
        db.rename_column(db.shorten_name(u'main_activitystream_job'), 'jobnew_id', 'job_id')

    def backwards(self, orm):
        db.rename_column(db.shorten_name(u'main_activitystream_job'), 'job_id', 'jobnew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_job'), db.shorten_name(u'main_activitystream_new_job'))
        db.rename_column(db.shorten_name(u'main_activitystream_job_template'), 'jobtemplate_id', 'jobtemplatenew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_job_template'), db.shorten_name(u'main_activitystream_new_job_template'))
        db.rename_column(db.shorten_name(u'main_activitystream_inventory_update'), 'inventoryupdate_id', 'inventoryupdatenew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_inventory_update'), db.shorten_name(u'main_activitystream_new_inventory_update'))
        db.rename_column(db.shorten_name(u'main_activitystream_inventory_source'), 'inventorysource_id', 'inventorysourcenew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_inventory_source'), db.shorten_name(u'main_activitystream_new_inventory_source'))
        db.rename_column(db.shorten_name(u'main_activitystream_project_update'), 'projectupdate_id', 'projectupdatenew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_project_update'), db.shorten_name(u'main_activitystream_new_project_update'))
        db.rename_column(db.shorten_name(u'main_activitystream_project'), 'project_id', 'projectnew_id')
        db.rename_table(db.shorten_name(u'main_activitystream_project'), db.shorten_name(u'main_activitystream_new_project'))

        db.rename_column(u'main_jobevent', 'job_id', 'new_job_id')
        db.rename_column(u'main_jobhostsummary', 'job_id', 'new_job_id')

        db.rename_column(db.shorten_name(u'main_group_inventory_sources'), 'inventorysource_id', 'inventorysourcenew_id')
        db.rename_table(db.shorten_name(u'main_group_inventory_sources'), db.shorten_name(u'main_group_new_inventory_sources'))
        db.rename_column(db.shorten_name(u'main_host_inventory_sources'), 'inventorysource_id', 'inventorysourcenew_id')
        db.rename_table(db.shorten_name(u'main_host_inventory_sources'), db.shorten_name(u'main_host_new_inventory_sources'))
        db.rename_column(u'main_host', 'last_job_id', 'new_last_job_id')

        db.rename_column(u'main_permission', 'project_id', 'new_project_id')
        db.rename_column(db.shorten_name(u'main_organization_projects'), 'project_id', 'projectnew_id')
        db.rename_table(db.shorten_name(u'main_organization_projects'), db.shorten_name(u'main_organization_new_projects'))
        db.rename_column(db.shorten_name(u'main_team_projects'), 'project_id', 'projectnew_id')
        db.rename_table(db.shorten_name(u'main_team_projects'), db.shorten_name(u'main_team_new_projects'))
        
        db.rename_table(u'main_job', 'main_jobnew')
        db.rename_table(u'main_jobtemplate', 'main_jobtemplatenew')
        db.rename_table(u'main_inventoryupdate', 'main_inventoryupdatenew')
        db.rename_table(u'main_inventorysource', 'main_inventorysourcenew')
        db.rename_table(u'main_projectupdate', 'main_projectupdatenew')
        db.rename_table(u'main_project', 'main_projectnew')


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
            'Meta': {'object_name': 'InventorySource', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventorysources'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
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
            'Meta': {'object_name': 'InventoryUpdate', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventoryupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': "orm['main.InventorySource']"}),
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
            'Meta': {'object_name': 'Job', '_ormbases': ['main.UnifiedJob']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'blank': 'True', 'through': "orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobTemplate']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            u'unifiedjob_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJob']", 'unique': 'True', 'primary_key': 'True'}),
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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobEvent']", 'blank': 'True', 'null': 'True'}),
            'play': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'})
        },
        'main.jobhostsummary': {
            'Meta': {'ordering': "('-pk',)", 'unique_together': "[('job', 'host')]", 'object_name': 'JobHostSummary'},
            'changed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'dark': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'ok': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skipped': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'main.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate', '_ormbases': ['main.UnifiedJobTemplate']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
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
            'Meta': {'object_name': 'Project', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projects'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
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
            'Meta': {'object_name': 'ProjectUpdate', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': "orm['main.Project']"}),
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