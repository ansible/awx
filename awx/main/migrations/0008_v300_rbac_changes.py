# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import taggit.managers
import awx.main.fields

class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0007_v300_active_flag_removal'),
    ]

    operations = [
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
            field=models.ForeignKey(related_name='projects', to='main.Organization', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='deprecated_projects',
            field=models.ManyToManyField(related_name='deprecated_teams', to='main.Project', blank=True),
        ),

        migrations.CreateModel(
            name='RoleAncestorEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role_field', models.TextField()),
                ('content_type_id', models.PositiveIntegerField(null=False)),
                ('object_id', models.PositiveIntegerField(null=False)),
            ],
            options={
                'db_table': 'main_rbac_role_ancestors',
                'verbose_name_plural': 'role_ancestors',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('singleton_name', models.TextField(default=None, unique=True, null=True, db_index=True)),
                ('object_id', models.PositiveIntegerField(default=None, null=True)),
                ('ancestors', models.ManyToManyField(related_name='descendents', through='main.RoleAncestorEntry', to='main.Role')),
                ('content_type', models.ForeignKey(default=None, to='contenttypes.ContentType', null=True)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'role', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('members', models.ManyToManyField(related_name='roles', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'role', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('parents', models.ManyToManyField(related_name='children', to='main.Role')),
                ('implicit_parents', models.TextField(null=False, default=b'[]')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'db_table': 'main_rbac_roles',
                'verbose_name_plural': 'roles',
            },
        ),
        migrations.AddField(
            model_name='roleancestorentry',
            name='ancestor',
            field=models.ForeignKey(related_name='+', to='main.Role'),
        ),
        migrations.AddField(
            model_name='roleancestorentry',
            name='descendent',
            field=models.ForeignKey(related_name='+', to='main.Role'),
        ),
        migrations.AlterIndexTogether(
            name='roleancestorentry',
            index_together=set([('ancestor', 'content_type_id', 'object_id'), ('ancestor', 'content_type_id', 'role_field')]),
        ),

        migrations.AddField(
            model_name='credential',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Auditor of the credential', parent_role=[b'singleton:System Auditor'], to='main.Role', role_name=b'Credential Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='owner_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Owner of the credential', parent_role=[b'singleton:System Administrator'], to='main.Role', role_name=b'Credential Owner', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May use this credential, but not read sensitive portions or modify it', parent_role=None, to='main.Role', role_name=b'Credential User', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May manage this inventory', parent_role=b'organization.admin_role', to='main.Role', role_name=b'CustomInventory Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May view but not modify this inventory', parent_role=b'organization.auditor_role', to='main.Role', role_name=b'CustomInventory Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May view but not modify this inventory', parent_role=b'organization.member_role', to='main.Role', role_name=b'CustomInventory Member', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.admin_role', b'parents.admin_role'], to='main.Role', role_name=b'Inventory Group Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.auditor_role', b'parents.auditor_role'], to='main.Role', role_name=b'Inventory Group Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.execute_role', b'parents.executor_role'], to='main.Role', role_name=b'Inventory Group Executor', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.update_role', b'parents.updater_role'], to='main.Role', role_name=b'Inventory Group Updater', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May manage this inventory', parent_role=b'organization.admin_role', to='main.Role', role_name=b'Inventory Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May view but not modify this inventory', parent_role=b'organization.auditor_role', to='main.Role', role_name=b'Inventory Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May execute jobs against this inventory', parent_role=None, to='main.Role', role_name=b'Inventory Executor', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May update the inventory', parent_role=None, to='main.Role', role_name=b'Inventory Updater', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May use this inventory, but not read sensitive portions or modify it', parent_role=None, to='main.Role', role_name=b'Inventory User', null=b'True'),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Full access to all settings', parent_role=[(b'project.admin_role', b'inventory.admin_role')], to='main.Role', role_name=b'Job Template Administrator', null=b'True'),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Read-only access to all settings', parent_role=[(b'project.auditor_role', b'inventory.auditor_role')], to='main.Role', role_name=b'Job Template Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May run the job template', parent_role=None, to='main.Role', role_name=b'Job Template Runner', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May manage all aspects of this organization', parent_role=b'singleton:System Administrator', to='main.Role', role_name=b'Organization Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May read all settings associated with this organization', parent_role=b'singleton:System Auditor', to='main.Role', role_name=b'Organization Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'A member of this organization', parent_role=b'admin_role', to='main.Role', role_name=b'Organization Member', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May manage this project', parent_role=[b'organization.admin_role', b'singleton:System Administrator'], to='main.Role', role_name=b'Project Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May read all settings associated with this project', parent_role=[b'organization.auditor_role', b'singleton:System Auditor'], to='main.Role', role_name=b'Project Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Implies membership within this project', parent_role=None, to='main.Role', role_name=b'Project Member', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='scm_update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May update this project from the source control management system', parent_role=b'admin_role', to='main.Role', role_name=b'Project Updater', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May manage this team', parent_role=b'organization.admin_role', to='main.Role', role_name=b'Team Administrator', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May read all settings associated with this team', parent_role=b'organization.auditor_role', to='main.Role', role_name=b'Team Auditor', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'A member of this team', to='main.Role', role_name=b'Team Member', null=b'True'),
        ),

        migrations.AddField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May read this credential', parent_role=[b'use_role', b'auditor_role', b'owner_role'], to='main.Role', role_name=b'Credential REad', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May view but not modify this inventory', parent_role=[b'auditor_role', b'member_role', b'admin_role'], to='main.Role', role_name=b'CustomInventory Read', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May execute ad hoc commands against this inventory', parent_role=[b'inventory.adhoc_role', b'parents.adhoc_role', b'admin_role'], to='main.Role', role_name=b'Inventory Ad Hoc', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'execute_role', b'update_role', b'auditor_role', b'admin_role'], to='main.Role', role_name=b'Inventory Group Executor', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May execute ad hoc commands against this inventory', parent_role=[b'admin_role'], to='main.Role', role_name=b'Inventory Ad Hoc', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May view this inventory', parent_role=[b'auditor_role', b'execute_role', b'update_role', b'use_role', b'admin_role'], to='main.Role', role_name=b'Read', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May run the job template', parent_role=[b'execute_role', b'auditor_role', b'admin_role'], to='main.Role', role_name=b'Job Template Runner', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Read an organization', parent_role=[b'member_role', b'auditor_role'], to='main.Role', role_name=b'Organization Read Access', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Read access to this project', parent_role=[b'member_role', b'auditor_role', b'scm_update_role'], to='main.Role', role_name=b'Project Read Access', null=b'True'),
        ),
        migrations.AddField(
            model_name='role',
            name='role_field',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Can view this team', parent_role=[b'admin_role', b'auditor_role', b'member_role'], to='main.Role', role_name=b'Read', null=b'True'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May use this credential, but not read sensitive portions or modify it', parent_role=[b'owner_role'], to='main.Role', role_name=b'Credential User', null=b'True'),
        ),
        migrations.AlterField(
            model_name='group',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.execute_role', b'parents.execute_role', b'adhoc_role'], to='main.Role', role_name=b'Inventory Group Executor', null=b'True'),
        ),
        migrations.AlterField(
            model_name='group',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'', parent_role=[b'inventory.update_role', b'parents.update_role', b'admin_role'], to='main.Role', role_name=b'Inventory Group Updater', null=b'True'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May execute jobs against this inventory', parent_role=b'adhoc_role', to='main.Role', role_name=b'Inventory Executor', null=b'True'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May update the inventory', parent_role=[b'admin_role'], to='main.Role', role_name=b'Inventory Updater', null=b'True'),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May use this inventory, but not read sensitive portions or modify it', parent_role=[b'admin_role'], to='main.Role', role_name=b'Inventory User', null=b'True'),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'May run the job template', parent_role=[b'admin_role'], to='main.Role', role_name=b'Job Template Runner', null=b'True'),
        ),
        migrations.AlterField(
            model_name='project',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', role_description=b'Implies membership within this project', parent_role=b'admin_role', to='main.Role', role_name=b'Project Member', null=b'True'),
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
    ]
