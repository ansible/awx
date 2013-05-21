# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tag'
        db.create_table(u'main_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('main', ['Tag'])

        # Adding model 'AuditTrail'
        db.create_table(u'main_audittrail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('delta', self.gf('django.db.models.fields.TextField')()),
            ('detail', self.gf('django.db.models.fields.TextField')()),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Tag'], null=True, on_delete=models.SET_NULL, blank=True)),
        ))
        db.send_create_signal('main', ['AuditTrail'])

        # Adding model 'Organization'
        db.create_table(u'main_organization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'organization', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
        ))
        db.send_create_signal('main', ['Organization'])

        # Adding M2M table for field tags on 'Organization'
        db.create_table(u'main_organization_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_organization_tags', ['organization_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Organization'
        db.create_table(u'main_organization_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_organization_audit_trail', ['organization_id', 'audittrail_id'])

        # Adding M2M table for field users on 'Organization'
        db.create_table(u'main_organization_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'main_organization_users', ['organization_id', 'user_id'])

        # Adding M2M table for field admins on 'Organization'
        db.create_table(u'main_organization_admins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'main_organization_admins', ['organization_id', 'user_id'])

        # Adding M2M table for field projects on 'Organization'
        db.create_table(u'main_organization_projects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False))
        ))
        db.create_unique(u'main_organization_projects', ['organization_id', 'project_id'])

        # Adding model 'Inventory'
        db.create_table(u'main_inventory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'inventory', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='inventories', to=orm['main.Organization'])),
        ))
        db.send_create_signal('main', ['Inventory'])

        # Adding M2M table for field tags on 'Inventory'
        db.create_table(u'main_inventory_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_inventory_tags', ['inventory_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Inventory'
        db.create_table(u'main_inventory_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_inventory_audit_trail', ['inventory_id', 'audittrail_id'])

        # Adding model 'Host'
        db.create_table(u'main_host', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'host', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['main.Inventory'])),
        ))
        db.send_create_signal('main', ['Host'])

        # Adding M2M table for field tags on 'Host'
        db.create_table(u'main_host_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_host_tags', ['host_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Host'
        db.create_table(u'main_host_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_host_audit_trail', ['host_id', 'audittrail_id'])

        # Adding model 'Group'
        db.create_table(u'main_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'group', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups', to=orm['main.Inventory'])),
        ))
        db.send_create_signal('main', ['Group'])

        # Adding M2M table for field tags on 'Group'
        db.create_table(u'main_group_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_group_tags', ['group_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Group'
        db.create_table(u'main_group_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_group_audit_trail', ['group_id', 'audittrail_id'])

        # Adding M2M table for field parents on 'Group'
        db.create_table(u'main_group_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_group', models.ForeignKey(orm['main.group'], null=False)),
            ('to_group', models.ForeignKey(orm['main.group'], null=False))
        ))
        db.create_unique(u'main_group_parents', ['from_group_id', 'to_group_id'])

        # Adding M2M table for field hosts on 'Group'
        db.create_table(u'main_group_hosts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('host', models.ForeignKey(orm['main.host'], null=False))
        ))
        db.create_unique(u'main_group_hosts', ['group_id', 'host_id'])

        # Adding model 'VariableData'
        db.create_table(u'main_variabledata', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'variabledata', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variable_data', on_delete=models.SET_NULL, default=None, to=orm['main.Host'], blank=True, null=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variable_data', on_delete=models.SET_NULL, default=None, to=orm['main.Group'], blank=True, null=True)),
            ('data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['VariableData'])

        # Adding M2M table for field tags on 'VariableData'
        db.create_table(u'main_variabledata_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_variabledata_tags', ['variabledata_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'VariableData'
        db.create_table(u'main_variabledata_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_variabledata_audit_trail', ['variabledata_id', 'audittrail_id'])

        # Adding model 'Credential'
        db.create_table(u'main_credential', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'credential', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='credentials', on_delete=models.SET_NULL, default=None, to=orm['auth.User'], blank=True, null=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='credentials', on_delete=models.SET_NULL, default=None, to=orm['main.Project'], blank=True, null=True)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='credentials', on_delete=models.SET_NULL, default=None, to=orm['main.Team'], blank=True, null=True)),
            ('ssh_key_path', self.gf('django.db.models.fields.CharField')(default='', max_length=4096, blank=True)),
            ('ssh_key_data', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('ssh_key_unlock', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('ssh_password', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
            ('sudo_password', self.gf('django.db.models.fields.CharField')(default='', max_length=1024, blank=True)),
        ))
        db.send_create_signal('main', ['Credential'])

        # Adding M2M table for field tags on 'Credential'
        db.create_table(u'main_credential_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_credential_tags', ['credential_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Credential'
        db.create_table(u'main_credential_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_credential_audit_trail', ['credential_id', 'audittrail_id'])

        # Adding model 'Team'
        db.create_table(u'main_team', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'team', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
        ))
        db.send_create_signal('main', ['Team'])

        # Adding M2M table for field tags on 'Team'
        db.create_table(u'main_team_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_team_tags', ['team_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Team'
        db.create_table(u'main_team_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_team_audit_trail', ['team_id', 'audittrail_id'])

        # Adding M2M table for field projects on 'Team'
        db.create_table(u'main_team_projects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False))
        ))
        db.create_unique(u'main_team_projects', ['team_id', 'project_id'])

        # Adding M2M table for field users on 'Team'
        db.create_table(u'main_team_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'main_team_users', ['team_id', 'user_id'])

        # Adding M2M table for field organizations on 'Team'
        db.create_table(u'main_team_organizations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False))
        ))
        db.create_unique(u'main_team_organizations', ['team_id', 'organization_id'])

        # Adding model 'Project'
        db.create_table(u'main_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'project', 'app_label': u'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('local_repository', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('scm_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_playbook', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'main', ['Project'])

        # Adding M2M table for field tags on 'Project'
        db.create_table(u'main_project_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_project_tags', ['project_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Project'
        db.create_table(u'main_project_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_project_audit_trail', ['project_id', 'audittrail_id'])

        # Adding M2M table for field inventories on 'Project'
        db.create_table(u'main_project_inventories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'main.project'], null=False)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False))
        ))
        db.create_unique(u'main_project_inventories', ['project_id', 'inventory_id'])

        # Adding model 'Permission'
        db.create_table(u'main_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'permission', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='permissions', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='permissions', null=True, on_delete=models.SET_NULL, to=orm['main.Team'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='permissions', null=True, on_delete=models.SET_NULL, to=orm['main.Project'])),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', null=True, on_delete=models.SET_NULL, to=orm['main.Inventory'])),
            ('permission_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('main', ['Permission'])

        # Adding M2M table for field tags on 'Permission'
        db.create_table(u'main_permission_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_permission_tags', ['permission_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Permission'
        db.create_table(u'main_permission_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_permission_audit_trail', ['permission_id', 'audittrail_id'])

        # Adding model 'LaunchJob'
        db.create_table(u'main_launchjob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'launchjob', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_jobs', on_delete=models.SET_NULL, default=None, to=orm['main.Inventory'], blank=True, null=True)),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_jobs', on_delete=models.SET_NULL, default=None, to=orm['main.Credential'], blank=True, null=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_jobs', on_delete=models.SET_NULL, default=None, to=orm['main.Project'], blank=True, null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_jobs', on_delete=models.SET_NULL, default=None, to=orm['auth.User'], blank=True, null=True)),
            ('job_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('main', ['LaunchJob'])

        # Adding M2M table for field tags on 'LaunchJob'
        db.create_table(u'main_launchjob_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjob', models.ForeignKey(orm['main.launchjob'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_launchjob_tags', ['launchjob_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'LaunchJob'
        db.create_table(u'main_launchjob_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjob', models.ForeignKey(orm['main.launchjob'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_launchjob_audit_trail', ['launchjob_id', 'audittrail_id'])

        # Adding model 'LaunchJobStatus'
        db.create_table(u'main_launchjobstatus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name="{'class': 'launchjobstatus', 'app_label': 'main'}(class)s_created", null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('launch_job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_job_statuses', null=True, on_delete=models.SET_NULL, to=orm['main.LaunchJob'])),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('result_data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['LaunchJobStatus'])

        # Adding M2M table for field tags on 'LaunchJobStatus'
        db.create_table(u'main_launchjobstatus_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjobstatus', models.ForeignKey(orm['main.launchjobstatus'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique(u'main_launchjobstatus_tags', ['launchjobstatus_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'LaunchJobStatus'
        db.create_table(u'main_launchjobstatus_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjobstatus', models.ForeignKey(orm['main.launchjobstatus'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique(u'main_launchjobstatus_audit_trail', ['launchjobstatus_id', 'audittrail_id'])


    def backwards(self, orm):
        # Deleting model 'Tag'
        db.delete_table(u'main_tag')

        # Deleting model 'AuditTrail'
        db.delete_table(u'main_audittrail')

        # Deleting model 'Organization'
        db.delete_table(u'main_organization')

        # Removing M2M table for field tags on 'Organization'
        db.delete_table('main_organization_tags')

        # Removing M2M table for field audit_trail on 'Organization'
        db.delete_table('main_organization_audit_trail')

        # Removing M2M table for field users on 'Organization'
        db.delete_table('main_organization_users')

        # Removing M2M table for field admins on 'Organization'
        db.delete_table('main_organization_admins')

        # Removing M2M table for field projects on 'Organization'
        db.delete_table('main_organization_projects')

        # Deleting model 'Inventory'
        db.delete_table(u'main_inventory')

        # Removing M2M table for field tags on 'Inventory'
        db.delete_table('main_inventory_tags')

        # Removing M2M table for field audit_trail on 'Inventory'
        db.delete_table('main_inventory_audit_trail')

        # Deleting model 'Host'
        db.delete_table(u'main_host')

        # Removing M2M table for field tags on 'Host'
        db.delete_table('main_host_tags')

        # Removing M2M table for field audit_trail on 'Host'
        db.delete_table('main_host_audit_trail')

        # Deleting model 'Group'
        db.delete_table(u'main_group')

        # Removing M2M table for field tags on 'Group'
        db.delete_table('main_group_tags')

        # Removing M2M table for field audit_trail on 'Group'
        db.delete_table('main_group_audit_trail')

        # Removing M2M table for field parents on 'Group'
        db.delete_table('main_group_parents')

        # Removing M2M table for field hosts on 'Group'
        db.delete_table('main_group_hosts')

        # Deleting model 'VariableData'
        db.delete_table(u'main_variabledata')

        # Removing M2M table for field tags on 'VariableData'
        db.delete_table('main_variabledata_tags')

        # Removing M2M table for field audit_trail on 'VariableData'
        db.delete_table('main_variabledata_audit_trail')

        # Deleting model 'Credential'
        db.delete_table(u'main_credential')

        # Removing M2M table for field tags on 'Credential'
        db.delete_table('main_credential_tags')

        # Removing M2M table for field audit_trail on 'Credential'
        db.delete_table('main_credential_audit_trail')

        # Deleting model 'Team'
        db.delete_table(u'main_team')

        # Removing M2M table for field tags on 'Team'
        db.delete_table('main_team_tags')

        # Removing M2M table for field audit_trail on 'Team'
        db.delete_table('main_team_audit_trail')

        # Removing M2M table for field projects on 'Team'
        db.delete_table('main_team_projects')

        # Removing M2M table for field users on 'Team'
        db.delete_table('main_team_users')

        # Removing M2M table for field organizations on 'Team'
        db.delete_table('main_team_organizations')

        # Deleting model 'Project'
        db.delete_table(u'main_project')

        # Removing M2M table for field tags on 'Project'
        db.delete_table('main_project_tags')

        # Removing M2M table for field audit_trail on 'Project'
        db.delete_table('main_project_audit_trail')

        # Removing M2M table for field inventories on 'Project'
        db.delete_table('main_project_inventories')

        # Deleting model 'Permission'
        db.delete_table(u'main_permission')

        # Removing M2M table for field tags on 'Permission'
        db.delete_table('main_permission_tags')

        # Removing M2M table for field audit_trail on 'Permission'
        db.delete_table('main_permission_audit_trail')

        # Deleting model 'LaunchJob'
        db.delete_table(u'main_launchjob')

        # Removing M2M table for field tags on 'LaunchJob'
        db.delete_table('main_launchjob_tags')

        # Removing M2M table for field audit_trail on 'LaunchJob'
        db.delete_table('main_launchjob_audit_trail')

        # Deleting model 'LaunchJobStatus'
        db.delete_table(u'main_launchjobstatus')

        # Removing M2M table for field tags on 'LaunchJobStatus'
        db.delete_table('main_launchjobstatus_tags')

        # Removing M2M table for field audit_trail on 'LaunchJobStatus'
        db.delete_table('main_launchjobstatus_audit_trail')


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
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['main.Project']", 'blank': 'True', 'null': 'True'}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4096', 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'credential_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Team']", 'blank': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credentials'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['auth.User']", 'blank': 'True', 'null': 'True'})
        },
        'main.group': {
            'Meta': {'object_name': 'Group'},
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
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'group_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.host': {
            'Meta': {'object_name': 'Host'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_by_audit_trail'", 'blank': 'True', 'to': "orm['main.AuditTrail']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'host\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'host_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        },
        'main.inventory': {
            'Meta': {'object_name': 'Inventory'},
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
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': '"{\'class\': \'launchjobstatus\', \'app_label\': \'main\'}(class)s_created"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_statuses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.LaunchJob']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'result_data': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'launchjobstatus_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
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
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
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
            'inventories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects'", 'blank': 'True', 'to': "orm['main.Inventory']"}),
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
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Organization']"}),
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
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variable_data'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'null': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variable_data'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Host']", 'blank': 'True', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'variabledata_by_tag'", 'blank': 'True', 'to': "orm['main.Tag']"})
        }
    }

    complete_apps = ['main']