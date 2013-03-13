# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.active'
        db.add_column(u'main_user', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Inventory.active'
        db.add_column(u'main_inventory', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Inventory.organization'
        db.alter_column(u'main_inventory', 'organization_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.Organization']))
        # Adding field 'Host.active'
        db.add_column(u'main_host', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Host.inventory'
        db.alter_column(u'main_host', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.Inventory']))
        # Adding field 'LaunchJob.active'
        db.add_column(u'main_launchjob', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'LaunchJob.credential'
        db.alter_column(u'main_launchjob', 'credential_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.Credential'], null=True))

        # Changing field 'LaunchJob.project'
        db.alter_column(u'main_launchjob', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.Project'], null=True))

        # Changing field 'LaunchJob.inventory'
        db.alter_column(u'main_launchjob', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.Inventory'], null=True))

        # Changing field 'LaunchJob.user'
        db.alter_column(u'main_launchjob', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.User'], null=True))
        # Adding field 'Group.active'
        db.add_column(u'main_group', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Group.inventory'
        db.alter_column(u'main_group', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.Inventory']))
        # Adding field 'Credential.active'
        db.add_column(u'main_credential', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Credential.team'
        db.alter_column(u'main_credential', 'team_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.Team'], null=True))

        # Changing field 'Credential.project'
        db.alter_column(u'main_credential', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.Project'], null=True))

        # Changing field 'Credential.user'
        db.alter_column(u'main_credential', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.SET_NULL, to=orm['main.User'], null=True))
        # Adding field 'AuditTrail.active'
        db.add_column(u'main_audittrail', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'AuditTrail.modified_by'
        db.alter_column(u'main_audittrail', 'modified_by_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User'], null=True, on_delete=models.SET_NULL))

        # Changing field 'AuditTrail.tag'
        db.alter_column(u'main_audittrail', 'tag_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Tag'], null=True, on_delete=models.SET_NULL))
        # Adding field 'Team.active'
        db.add_column(u'main_team', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Project.active'
        db.add_column(u'main_project', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Permission.active'
        db.add_column(u'main_permission', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Permission.project'
        db.alter_column(u'main_permission', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.Project']))

        # Changing field 'Permission.user'
        db.alter_column(u'main_permission', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.User']))

        # Changing field 'Permission.team'
        db.alter_column(u'main_permission', 'team_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.Team']))
        # Adding field 'LaunchJobStatus.active'
        db.add_column(u'main_launchjobstatus', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'LaunchJobStatus.launch_job'
        db.alter_column(u'main_launchjobstatus', 'launch_job_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['main.LaunchJob']))
        # Adding field 'VariableData.active'
        db.add_column(u'main_variabledata', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Organization.active'
        db.add_column(u'main_organization', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.active'
        db.delete_column(u'main_user', 'active')

        # Deleting field 'Inventory.active'
        db.delete_column(u'main_inventory', 'active')


        # Changing field 'Inventory.organization'
        db.alter_column(u'main_inventory', 'organization_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Organization']))
        # Deleting field 'Host.active'
        db.delete_column(u'main_host', 'active')


        # Changing field 'Host.inventory'
        db.alter_column(u'main_host', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Inventory']))
        # Deleting field 'LaunchJob.active'
        db.delete_column(u'main_launchjob', 'active')


        # Changing field 'LaunchJob.credential'
        db.alter_column(u'main_launchjob', 'credential_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.Credential']))

        # Changing field 'LaunchJob.project'
        db.alter_column(u'main_launchjob', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.Project']))

        # Changing field 'LaunchJob.inventory'
        db.alter_column(u'main_launchjob', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.Inventory']))

        # Changing field 'LaunchJob.user'
        db.alter_column(u'main_launchjob', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.User']))
        # Deleting field 'Group.active'
        db.delete_column(u'main_group', 'active')


        # Changing field 'Group.inventory'
        db.alter_column(u'main_group', 'inventory_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Inventory']))
        # Deleting field 'Credential.active'
        db.delete_column(u'main_credential', 'active')


        # Changing field 'Credential.team'
        db.alter_column(u'main_credential', 'team_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.Team']))

        # Changing field 'Credential.project'
        db.alter_column(u'main_credential', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.Project']))

        # Changing field 'Credential.user'
        db.alter_column(u'main_credential', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['main.User']))
        # Deleting field 'AuditTrail.active'
        db.delete_column(u'main_audittrail', 'active')


        # Changing field 'AuditTrail.modified_by'
        db.alter_column(u'main_audittrail', 'modified_by_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.User']))

        # Changing field 'AuditTrail.tag'
        db.alter_column(u'main_audittrail', 'tag_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Tag']))
        # Deleting field 'Team.active'
        db.delete_column(u'main_team', 'active')

        # Deleting field 'Project.active'
        db.delete_column(u'main_project', 'active')

        # Deleting field 'Permission.active'
        db.delete_column(u'main_permission', 'active')


        # Changing field 'Permission.project'
        db.alter_column(u'main_permission', 'project_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Project']))

        # Changing field 'Permission.user'
        db.alter_column(u'main_permission', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.User']))

        # Changing field 'Permission.team'
        db.alter_column(u'main_permission', 'team_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.Team']))
        # Deleting field 'LaunchJobStatus.active'
        db.delete_column(u'main_launchjobstatus', 'active')


        # Changing field 'LaunchJobStatus.launch_job'
        db.alter_column(u'main_launchjobstatus', 'launch_job_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['main.LaunchJob']))
        # Deleting field 'VariableData.active'
        db.delete_column(u'main_variabledata', 'active')

        # Deleting field 'Organization.active'
        db.delete_column(u'main_organization', 'active')


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
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'audittrail_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'delta': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'detail': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'resource_type': ('django.db.models.fields.TextField', [], {}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Tag']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'audittrail_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.credential': {
            'Meta': {'object_name': 'Credential'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_path': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Team']", 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.group': {
            'Meta': {'object_name': 'Group'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'group_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents_rel_+'", 'to': "orm['main.Group']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'group_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.host': {
            'Meta': {'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'host_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'host_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.inventory': {
            'Meta': {'object_name': 'Inventory'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inventory_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Organization']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inventory_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.launchjob': {
            'Meta': {'object_name': 'LaunchJob'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjob_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Inventory']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjob_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.launchjobstatus': {
            'Meta': {'object_name': 'LaunchJobStatus'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjobstatus_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_statuses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.LaunchJob']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'result_data': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjobstatus_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admin_of_organizations'", 'symmetrical': 'False', 'to': "orm['main.User']"}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organization_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organization_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['main.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_type': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.User']"})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'project_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'default_playbook': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'to': "orm['main.Inventory']"}),
            'local_repository': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'scm_type': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'project_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'main.team': {
            'Meta': {'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organization': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.User']"})
        },
        'main.user': {
            'Meta': {'object_name': 'User'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'auth_user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'application_user'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.variabledata': {
            'Meta': {'object_name': 'VariableData'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'variabledata_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Group']"}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'variabledata_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        }
    }

    complete_apps = ['main']