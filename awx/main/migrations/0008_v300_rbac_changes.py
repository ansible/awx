# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import awx.main.fields

class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0007_v300_active_flag_removal'),
    ]

    operations = [
        #
        # Patch up existing
        #
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


        #
        # New RBAC models and fields
        #
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role_field', models.TextField()),
                ('singleton_name', models.TextField(default=None, unique=True, null=True, db_index=True)),
                ('members', models.ManyToManyField(related_name='roles', to=settings.AUTH_USER_MODEL)),
                ('parents', models.ManyToManyField(related_name='children', to='main.Role')),
                ('implicit_parents', models.TextField(default=b'[]')),
                ('content_type', models.ForeignKey(default=None, to='contenttypes.ContentType', null=True)),
                ('object_id', models.PositiveIntegerField(default=None, null=True)),

            ],
            options={
                'db_table': 'main_rbac_roles',
                'verbose_name_plural': 'roles',
            },
        ),
        migrations.CreateModel(
            name='RoleAncestorEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role_field', models.TextField()),
                ('content_type_id', models.PositiveIntegerField()),
                ('object_id', models.PositiveIntegerField()),
                ('ancestor', models.ForeignKey(related_name='+', to='main.Role')),
                ('descendent', models.ForeignKey(related_name='+', to='main.Role')),
            ],
            options={
                'db_table': 'main_rbac_role_ancestors',
                'verbose_name_plural': 'role_ancestors',
            },
        ),
        migrations.AddField(
            model_name='role',
            name='ancestors',
            field=models.ManyToManyField(related_name='descendents', through='main.RoleAncestorEntry', to='main.Role'),
        ),
        migrations.AlterIndexTogether(
            name='role',
            index_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterIndexTogether(
            name='roleancestorentry',
            index_together=set([('ancestor', 'content_type_id', 'object_id'), ('ancestor', 'content_type_id', 'role_field'), ('ancestor', 'descendent')]),
        ),
        migrations.AddField(
            model_name='credential',
            name='owner_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_administrator'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'owner_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'use_role', b'owner_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='custominventoryscript',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'organization.member_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'inventory.admin_role', b'parents.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'inventory.adhoc_role', b'parents.adhoc_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'inventory.use_role', b'parents.use_role', b'adhoc_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'inventory.update_role', b'parents.update_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='group',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'inventory.read_role', b'parents.read_role', b'use_role', b'update_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='adhoc_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'adhoc_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='inventory',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role',  b'update_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'project.organization.admin_role', b'inventory.organization.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'project.organization.auditor_role', b'inventory.organization.auditor_role', b'execute_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'singleton:system_administrator', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'singleton:system_auditor', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='organization',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'member_role', b'auditor_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.admin_role', b'singleton:system_administrator'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='update_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='project',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'singleton:system_auditor', b'use_role', b'update_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=None, to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role', b'organization.auditor_role', b'member_role'], to='main.Role', null=b'True'),
        ),
    ]
