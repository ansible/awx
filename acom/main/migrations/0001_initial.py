# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tag'
        db.create_table('main_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['Tag'])

        # Adding model 'AuditTrail'
        db.create_table('main_audittrail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('resource_type', self.gf('django.db.models.fields.TextField')()),
            ('modified_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User'])),
            ('delta', self.gf('django.db.models.fields.TextField')()),
            ('detail', self.gf('django.db.models.fields.TextField')()),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Tag'])),
        ))
        db.send_create_signal('main', ['AuditTrail'])

        # Adding M2M table for field tags on 'AuditTrail'
        db.create_table('main_audittrail_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_audittrail_tags', ['audittrail_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'AuditTrail'
        db.create_table('main_audittrail_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_audittrail', models.ForeignKey(orm['main.audittrail'], null=False)),
            ('to_audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_audittrail_audit_trail', ['from_audittrail_id', 'to_audittrail_id'])

        # Adding model 'Organization'
        db.create_table('main_organization', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('main', ['Organization'])

        # Adding M2M table for field tags on 'Organization'
        db.create_table('main_organization_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_organization_tags', ['organization_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Organization'
        db.create_table('main_organization_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_organization_audit_trail', ['organization_id', 'audittrail_id'])

        # Adding M2M table for field users on 'Organization'
        db.create_table('main_organization_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('user', models.ForeignKey(orm['main.user'], null=False))
        ))
        db.create_unique('main_organization_users', ['organization_id', 'user_id'])

        # Adding M2M table for field admins on 'Organization'
        db.create_table('main_organization_admins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('user', models.ForeignKey(orm['main.user'], null=False))
        ))
        db.create_unique('main_organization_admins', ['organization_id', 'user_id'])

        # Adding M2M table for field projects on 'Organization'
        db.create_table('main_organization_projects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False)),
            ('project', models.ForeignKey(orm['main.project'], null=False))
        ))
        db.create_unique('main_organization_projects', ['organization_id', 'project_id'])

        # Adding model 'Inventory'
        db.create_table('main_inventory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='inventories', to=orm['main.Organization'])),
        ))
        db.send_create_signal('main', ['Inventory'])

        # Adding M2M table for field tags on 'Inventory'
        db.create_table('main_inventory_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_inventory_tags', ['inventory_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Inventory'
        db.create_table('main_inventory_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_inventory_audit_trail', ['inventory_id', 'audittrail_id'])

        # Adding model 'Host'
        db.create_table('main_host', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['main.Inventory'])),
        ))
        db.send_create_signal('main', ['Host'])

        # Adding M2M table for field tags on 'Host'
        db.create_table('main_host_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_host_tags', ['host_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Host'
        db.create_table('main_host_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm['main.host'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_host_audit_trail', ['host_id', 'audittrail_id'])

        # Adding model 'Group'
        db.create_table('main_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups', to=orm['main.Inventory'])),
        ))
        db.send_create_signal('main', ['Group'])

        # Adding M2M table for field tags on 'Group'
        db.create_table('main_group_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_group_tags', ['group_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Group'
        db.create_table('main_group_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['main.group'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_group_audit_trail', ['group_id', 'audittrail_id'])

        # Adding M2M table for field parents on 'Group'
        db.create_table('main_group_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_group', models.ForeignKey(orm['main.group'], null=False)),
            ('to_group', models.ForeignKey(orm['main.group'], null=False))
        ))
        db.create_unique('main_group_parents', ['from_group_id', 'to_group_id'])

        # Adding model 'VariableData'
        db.create_table('main_variabledata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='variable_data', null=True, blank=True, to=orm['main.Host'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='variable_data', null=True, blank=True, to=orm['main.Group'])),
            ('data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['VariableData'])

        # Adding M2M table for field tags on 'VariableData'
        db.create_table('main_variabledata_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_variabledata_tags', ['variabledata_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'VariableData'
        db.create_table('main_variabledata_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('variabledata', models.ForeignKey(orm['main.variabledata'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_variabledata_audit_trail', ['variabledata_id', 'audittrail_id'])

        # Adding model 'User'
        db.create_table('main_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('auth_user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='application_user', unique=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('main', ['User'])

        # Adding M2M table for field tags on 'User'
        db.create_table('main_user_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['main.user'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_user_tags', ['user_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'User'
        db.create_table('main_user_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['main.user'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_user_audit_trail', ['user_id', 'audittrail_id'])

        # Adding model 'Credential'
        db.create_table('main_credential', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='credentials', null=True, blank=True, to=orm['main.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='credentials', null=True, blank=True, to=orm['main.Project'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='credentials', null=True, blank=True, to=orm['main.Team'])),
            ('ssh_key_path', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('ssh_key_data', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('ssh_key_unlock', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('ssh_password', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('sudo_password', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('main', ['Credential'])

        # Adding M2M table for field tags on 'Credential'
        db.create_table('main_credential_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_credential_tags', ['credential_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Credential'
        db.create_table('main_credential_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('credential', models.ForeignKey(orm['main.credential'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_credential_audit_trail', ['credential_id', 'audittrail_id'])

        # Adding model 'Team'
        db.create_table('main_team', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('main', ['Team'])

        # Adding M2M table for field tags on 'Team'
        db.create_table('main_team_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_team_tags', ['team_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Team'
        db.create_table('main_team_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_team_audit_trail', ['team_id', 'audittrail_id'])

        # Adding M2M table for field projects on 'Team'
        db.create_table('main_team_projects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('project', models.ForeignKey(orm['main.project'], null=False))
        ))
        db.create_unique('main_team_projects', ['team_id', 'project_id'])

        # Adding M2M table for field users on 'Team'
        db.create_table('main_team_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('user', models.ForeignKey(orm['main.user'], null=False))
        ))
        db.create_unique('main_team_users', ['team_id', 'user_id'])

        # Adding M2M table for field organization on 'Team'
        db.create_table('main_team_organization', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm['main.team'], null=False)),
            ('organization', models.ForeignKey(orm['main.organization'], null=False))
        ))
        db.create_unique('main_team_organization', ['team_id', 'organization_id'])

        # Adding model 'Project'
        db.create_table('main_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('local_repository', self.gf('django.db.models.fields.TextField')()),
            ('scm_type', self.gf('django.db.models.fields.TextField')()),
            ('default_playbook', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['Project'])

        # Adding M2M table for field tags on 'Project'
        db.create_table('main_project_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['main.project'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_project_tags', ['project_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Project'
        db.create_table('main_project_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['main.project'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_project_audit_trail', ['project_id', 'audittrail_id'])

        # Adding M2M table for field inventories on 'Project'
        db.create_table('main_project_inventories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['main.project'], null=False)),
            ('inventory', models.ForeignKey(orm['main.inventory'], null=False))
        ))
        db.create_unique('main_project_inventories', ['project_id', 'inventory_id'])

        # Adding model 'Permission'
        db.create_table('main_permission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['main.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['main.Project'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['main.Team'])),
            ('job_type', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['Permission'])

        # Adding M2M table for field tags on 'Permission'
        db.create_table('main_permission_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_permission_tags', ['permission_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'Permission'
        db.create_table('main_permission_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permission', models.ForeignKey(orm['main.permission'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_permission_audit_trail', ['permission_id', 'audittrail_id'])

        # Adding model 'LaunchJob'
        db.create_table('main_launchjob', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('inventory', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='launch_jobs', null=True, blank=True, to=orm['main.Inventory'])),
            ('credential', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='launch_jobs', null=True, blank=True, to=orm['main.Credential'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='launch_jobs', null=True, blank=True, to=orm['main.Project'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='launch_jobs', null=True, blank=True, to=orm['main.User'])),
            ('job_type', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['LaunchJob'])

        # Adding M2M table for field tags on 'LaunchJob'
        db.create_table('main_launchjob_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjob', models.ForeignKey(orm['main.launchjob'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_launchjob_tags', ['launchjob_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'LaunchJob'
        db.create_table('main_launchjob_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjob', models.ForeignKey(orm['main.launchjob'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_launchjob_audit_trail', ['launchjob_id', 'audittrail_id'])

        # Adding model 'LaunchJobStatus'
        db.create_table('main_launchjobstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('launch_job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='launch_job_statuses', to=orm['main.LaunchJob'])),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('result_data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['LaunchJobStatus'])

        # Adding M2M table for field tags on 'LaunchJobStatus'
        db.create_table('main_launchjobstatus_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjobstatus', models.ForeignKey(orm['main.launchjobstatus'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('main_launchjobstatus_tags', ['launchjobstatus_id', 'tag_id'])

        # Adding M2M table for field audit_trail on 'LaunchJobStatus'
        db.create_table('main_launchjobstatus_audit_trail', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('launchjobstatus', models.ForeignKey(orm['main.launchjobstatus'], null=False)),
            ('audittrail', models.ForeignKey(orm['main.audittrail'], null=False))
        ))
        db.create_unique('main_launchjobstatus_audit_trail', ['launchjobstatus_id', 'audittrail_id'])


    def backwards(self, orm):
        # Deleting model 'Tag'
        db.delete_table('main_tag')

        # Deleting model 'AuditTrail'
        db.delete_table('main_audittrail')

        # Removing M2M table for field tags on 'AuditTrail'
        db.delete_table('main_audittrail_tags')

        # Removing M2M table for field audit_trail on 'AuditTrail'
        db.delete_table('main_audittrail_audit_trail')

        # Deleting model 'Organization'
        db.delete_table('main_organization')

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
        db.delete_table('main_inventory')

        # Removing M2M table for field tags on 'Inventory'
        db.delete_table('main_inventory_tags')

        # Removing M2M table for field audit_trail on 'Inventory'
        db.delete_table('main_inventory_audit_trail')

        # Deleting model 'Host'
        db.delete_table('main_host')

        # Removing M2M table for field tags on 'Host'
        db.delete_table('main_host_tags')

        # Removing M2M table for field audit_trail on 'Host'
        db.delete_table('main_host_audit_trail')

        # Deleting model 'Group'
        db.delete_table('main_group')

        # Removing M2M table for field tags on 'Group'
        db.delete_table('main_group_tags')

        # Removing M2M table for field audit_trail on 'Group'
        db.delete_table('main_group_audit_trail')

        # Removing M2M table for field parents on 'Group'
        db.delete_table('main_group_parents')

        # Deleting model 'VariableData'
        db.delete_table('main_variabledata')

        # Removing M2M table for field tags on 'VariableData'
        db.delete_table('main_variabledata_tags')

        # Removing M2M table for field audit_trail on 'VariableData'
        db.delete_table('main_variabledata_audit_trail')

        # Deleting model 'User'
        db.delete_table('main_user')

        # Removing M2M table for field tags on 'User'
        db.delete_table('main_user_tags')

        # Removing M2M table for field audit_trail on 'User'
        db.delete_table('main_user_audit_trail')

        # Deleting model 'Credential'
        db.delete_table('main_credential')

        # Removing M2M table for field tags on 'Credential'
        db.delete_table('main_credential_tags')

        # Removing M2M table for field audit_trail on 'Credential'
        db.delete_table('main_credential_audit_trail')

        # Deleting model 'Team'
        db.delete_table('main_team')

        # Removing M2M table for field tags on 'Team'
        db.delete_table('main_team_tags')

        # Removing M2M table for field audit_trail on 'Team'
        db.delete_table('main_team_audit_trail')

        # Removing M2M table for field projects on 'Team'
        db.delete_table('main_team_projects')

        # Removing M2M table for field users on 'Team'
        db.delete_table('main_team_users')

        # Removing M2M table for field organization on 'Team'
        db.delete_table('main_team_organization')

        # Deleting model 'Project'
        db.delete_table('main_project')

        # Removing M2M table for field tags on 'Project'
        db.delete_table('main_project_tags')

        # Removing M2M table for field audit_trail on 'Project'
        db.delete_table('main_project_audit_trail')

        # Removing M2M table for field inventories on 'Project'
        db.delete_table('main_project_inventories')

        # Deleting model 'Permission'
        db.delete_table('main_permission')

        # Removing M2M table for field tags on 'Permission'
        db.delete_table('main_permission_tags')

        # Removing M2M table for field audit_trail on 'Permission'
        db.delete_table('main_permission_audit_trail')

        # Deleting model 'LaunchJob'
        db.delete_table('main_launchjob')

        # Removing M2M table for field tags on 'LaunchJob'
        db.delete_table('main_launchjob_tags')

        # Removing M2M table for field audit_trail on 'LaunchJob'
        db.delete_table('main_launchjob_audit_trail')

        # Deleting model 'LaunchJobStatus'
        db.delete_table('main_launchjobstatus')

        # Removing M2M table for field tags on 'LaunchJobStatus'
        db.delete_table('main_launchjobstatus_tags')

        # Removing M2M table for field audit_trail on 'LaunchJobStatus'
        db.delete_table('main_launchjobstatus_audit_trail')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.audittrail': {
            'Meta': {'object_name': 'AuditTrail'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'audittrail_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'delta': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'detail': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.User']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'resource_type': ('django.db.models.fields.TextField', [], {}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Tag']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'audittrail_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.credential': {
            'Meta': {'object_name': 'Credential'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'credentials'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Project']"}),
            'ssh_key_data': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_path': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_key_unlock': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'ssh_password': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'sudo_password': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'credential_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'credentials'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'credentials'", 'null': 'True', 'blank': 'True', 'to': "orm['main.User']"})
        },
        'main.group': {
            'Meta': {'object_name': 'Group'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'group_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents_rel_+'", 'to': "orm['main.Group']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'group_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.host': {
            'Meta': {'object_name': 'Host'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'host_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': "orm['main.Inventory']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'host_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.inventory': {
            'Meta': {'object_name': 'Inventory'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inventory_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventories'", 'to': "orm['main.Organization']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'inventory_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.launchjob': {
            'Meta': {'object_name': 'LaunchJob'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjob_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'launch_jobs'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'launch_jobs'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Inventory']"}),
            'job_type': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'launch_jobs'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjob_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'launch_jobs'", 'null': 'True', 'blank': 'True', 'to': "orm['main.User']"})
        },
        'main.launchjobstatus': {
            'Meta': {'object_name': 'LaunchJobStatus'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjobstatus_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launch_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'launch_job_statuses'", 'to': "orm['main.LaunchJob']"}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'result_data': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'launchjobstatus_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.organization': {
            'Meta': {'object_name': 'Organization'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admin_of_organizations'", 'symmetrical': 'False', 'to': "orm['main.User']"}),
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organization_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organization_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['main.User']"})
        },
        'main.permission': {
            'Meta': {'object_name': 'Permission'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_type': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['main.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['main.User']"})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'project_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'default_playbook': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'to': "orm['main.Inventory']"}),
            'local_repository': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'scm_type': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'project_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'main.team': {
            'Meta': {'object_name': 'Team'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'organization': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Organization']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.Project']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'team_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'to': "orm['main.User']"})
        },
        'main.user': {
            'Meta': {'object_name': 'User'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'auth_user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'application_user'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        },
        'main.variabledata': {
            'Meta': {'object_name': 'VariableData'},
            'audit_trail': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'variabledata_audit_trails'", 'symmetrical': 'False', 'to': "orm['main.AuditTrail']"}),
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Group']"}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'variable_data'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'variabledata_tags'", 'symmetrical': 'False', 'to': "orm['main.Tag']"})
        }
    }

    complete_apps = ['main']