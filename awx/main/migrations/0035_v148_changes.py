# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.utils.encoding import smart_text

class Migration(DataMigration):

    def _get_dict_from_primordial_model(self, instance):
        return {
            'description': instance.description,
            'created': instance.created,
            'modified': instance.modified,
            'created_by': instance.created_by,
            'modified_by': instance.modified_by,
            'active': instance.active,
            'old_pk': instance.pk,
        }

    def _get_dict_from_common_model(self, instance):
        d = self._get_dict_from_primordial_model(instance)
        if hasattr(instance, 'name'):
            d['name'] = instance.name
        else:
            d['name'] = u'%s-%s' % (instance._meta.verbose_name, instance.pk)
        return d

    def _get_dict_from_common_task_model(self, instance):
        d = self._get_dict_from_primordial_model(instance)
        td = instance.modified - instance.created
        elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / (10**6 * 1.0)
        d.update({
            'launch_type': getattr(instance, 'launch_type', 'manual'),
            'cancel_flag': instance.cancel_flag,
            'status': instance.status,
            'failed': instance.failed,
            'started': instance.created,
            'finished': instance.modified,
            'elapsed': elapsed,
            'job_args': instance.job_args,
            'job_env': instance.job_env,
            'result_stdout_text': instance._result_stdout,
            'result_stdout_file': instance.result_stdout_file,
            'result_traceback': instance.result_traceback,
            'celery_task_id': instance.celery_task_id,
        })
        return d

    def _get_content_type_for_model(self, orm, model):
        app_label = model._meta.app_label
        model_name = model._meta.module_name
        defaults = {'name': smart_text(model._meta.verbose_name_raw)}
        content_type, created = orm['contenttypes.ContentType'].objects.get_or_create(app_label=app_label, model=model_name, defaults=defaults)
        return content_type

    def forwards(self, orm):
        "Write your forwards methods here."

        # Copy Project old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.Project)
        for project in orm.Project.objects.order_by('pk'):
            d = self._get_dict_from_common_model(project)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'local_path': project.local_path,
                'scm_type': project.scm_type,
                'scm_url': project.scm_url,
                'scm_branch': project.scm_branch,
                'scm_clean': project.scm_clean,
                'scm_delete_on_update': project.scm_delete_on_update,
                'credential_id': project.credential_id,
                'scm_delete_on_next_update': project.scm_delete_on_next_update,
                'scm_update_on_launch': project.scm_update_on_launch,
            })
            new_project, created = orm.ProjectNew.objects.get_or_create(old_pk=project.pk, defaults=d)

        # Copy ProjectUpdate old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.ProjectUpdate)
        for project_update in orm.ProjectUpdate.objects.order_by('pk'):
            project = project_update.project
            d = self._get_dict_from_common_task_model(project_update)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'project_id': orm.ProjectNew.objects.get(old_pk=project_update.project_id).pk,
                'local_path': project.local_path,
                'scm_type': project.scm_type,
                'scm_url': project.scm_url,
                'scm_branch': project.scm_branch,
                'scm_clean': project.scm_clean,
                'scm_delete_on_update': project.scm_delete_on_update,
                'credential_id': project.credential_id,
            })
            new_project_update, created = orm.ProjectUpdateNew.objects.get_or_create(old_pk=project_update.pk, defaults=d)

        # Update Project last run.
        for project in orm.Project.objects.order_by('pk'):
            new_project = orm.ProjectNew.objects.get(old_pk=project.pk)
            if project.current_update:
                new_project.current_job = orm.ProjectUpdateNew.objects.get(old_pk=project.current_update_id)
            if project.last_update:
                new_project.last_job = orm.ProjectUpdateNew.objects.get(old_pk=project.last_update_id)
            new_project.last_job_failed = project.last_update_failed
            new_project.last_job_run = project.last_updated
            new_project.status = project.status
            new_project.save()

        # Update Organization projects.
        for organization in orm.Organization.objects.order_by('pk'):
            for project in organization.projects.order_by('pk'):
                new_project = orm.ProjectNew.objects.get(old_pk=project.pk)
                organization.new_projects.add(new_project)

        # Update Team projects.
        for team in orm.Team.objects.order_by('pk'):
            for project in team.projects.order_by('pk'):
                new_project = orm.ProjectNew.objects.get(old_pk=project.pk)
                team.new_projects.add(new_project)

        # Update Permission project.
        for permission in orm.Permission.objects.order_by('pk'):
            if not permission.project_id:
                continue
            new_project = orm.ProjectNew.objects.get(old_pk=permission.project_id)
            permission.new_project = new_project
            permission.save()

        # Copy InventorySource old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.InventorySource)
        for inventory_source in orm.InventorySource.objects.order_by('pk'):
            d = self._get_dict_from_common_model(inventory_source)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'source': inventory_source.source,
                'source_path': inventory_source.source_path,
                'source_vars': inventory_source.source_vars,
                'credential_id': inventory_source.credential_id,
                'source_regions': inventory_source.source_regions,
                'overwrite': inventory_source.overwrite,
                'overwrite_vars': inventory_source.overwrite_vars,
                'update_on_launch': inventory_source.update_on_launch,
                'inventory_id': inventory_source.inventory_id,
                'group_id': inventory_source.group_id,
            })
            new_inventory_source, created = orm.InventorySourceNew.objects.get_or_create(old_pk=inventory_source.pk, defaults=d)

        # Copy InventoryUpdate old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.InventoryUpdate)
        for inventory_update in orm.InventoryUpdate.objects.order_by('pk'):
            inventory_source = inventory_update.inventory_source
            d = self._get_dict_from_common_task_model(inventory_update)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'source': inventory_source.source,
                'source_path': inventory_source.source_path,
                'source_vars': inventory_source.source_vars,
                'credential_id': inventory_source.credential_id,
                'source_regions': inventory_source.source_regions,
                'overwrite': inventory_source.overwrite,
                'overwrite_vars': inventory_source.overwrite_vars,
                'inventory_source_id': orm.InventorySourceNew.objects.get(old_pk=inventory_update.inventory_source_id).pk,
                'license_error': inventory_update.license_error,
            })
            new_inventory_update, created = orm.InventoryUpdateNew.objects.get_or_create(old_pk=inventory_update.pk, defaults=d)

        # Update InventorySource last run.
        for inventory_source in orm.InventorySource.objects.order_by('pk'):
            new_inventory_source = orm.InventorySourceNew.objects.get(old_pk=inventory_source.pk)
            if inventory_source.current_update:
                new_inventory_source.current_job = orm.InventoryUpdateNew.objects.get(old_pk=inventory_source.current_update_id)
            if inventory_source.last_update:
                new_inventory_source.last_job = orm.InventoryUpdateNew.objects.get(old_pk=inventory_source.last_update_id)
            new_inventory_source.last_job_failed = inventory_source.last_update_failed
            new_inventory_source.last_job_run = inventory_source.last_updated
            new_inventory_source.status = inventory_source.status
            new_inventory_source.save()

        # Update Group inventory_sources.
        for group in orm.Group.objects.order_by('pk'):
            for inventory_source in group.inventory_sources.order_by('pk'):
                new_inventory_source = orm.InventorySourceNew.objects.get(old_pk=inventory_source.pk)
                group.new_inventory_sources.add(new_inventory_source)
        
        # Update Host inventory_sources.
        for host in orm.Host.objects.order_by('pk'):
            for inventory_source in host.inventory_sources.order_by('pk'):
                new_inventory_source = orm.InventorySourceNew.objects.get(old_pk=inventory_source.pk)
                host.new_inventory_sources.add(new_inventory_source)

        # Copy JobTemplate old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.JobTemplate)
        for job_template in orm.JobTemplate.objects.order_by('pk'):
            d = self._get_dict_from_common_model(job_template)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'job_type': job_template.job_type,
                'inventory_id': job_template.inventory_id,
                'playbook': job_template.playbook,
                'credential_id': job_template.credential_id,
                'cloud_credential_id': job_template.cloud_credential_id,
                'forks': job_template.forks,
                'limit': job_template.limit,
                'extra_vars': job_template.extra_vars,
                'job_tags': job_template.job_tags,
                'host_config_key': job_template.host_config_key,
            })
            if job_template.project:
                d['project_id'] = orm.ProjectNew.objects.get(old_pk=job_template.project_id).pk
            new_job_template, created = orm.JobTemplateNew.objects.get_or_create(old_pk=job_template.pk, defaults=d)

        # Copy Job old to new.
        new_ctype = self._get_content_type_for_model(orm, orm.Job)
        for job in orm.Job.objects.order_by('pk'):
            d = self._get_dict_from_common_task_model(job)
            d.update({
                'polymorphic_ctype_id': new_ctype.pk,
                'job_type': job_template.job_type,
                'inventory_id': job_template.inventory_id,
                'playbook': job_template.playbook,
                'credential_id': job_template.credential_id,
                'cloud_credential_id': job_template.cloud_credential_id,
                'forks': job_template.forks,
                'limit': job_template.limit,
                'extra_vars': job_template.extra_vars,
                'job_tags': job_template.job_tags,
            })
            if job.project:
                d['project_id'] = orm.ProjectNew.objects.get(old_pk=job.project_id).pk
            if job.job_template:
                d['job_template_id'] = orm.JobTemplateNew.objects.get(old_pk=job.job_template_id).pk
            new_job, created = orm.JobNew.objects.get_or_create(old_pk=job.pk, defaults=d)

        # Update JobTemplate last run.
        for new_job_template in orm.JobTemplateNew.objects.order_by('pk'):
            try:
                new_last_job = new_job_template.jobs.order_by('-pk')[0]
                new_job_template.last_job = new_last_job
                new_job_template.last_job_failed = new_last_job.failed
                new_job_template.last_job_run = new_last_job.finished
                new_job_template.status = 'failed' if new_last_job.failed else 'successful'
            except IndexError:
                new_job_template.status = 'never updated'
            new_inventory_source.save()

        # Update JobHostSummary job.
        for job_host_summary in orm.JobHostSummary.objects.order_by('pk'):
            new_job = orm.JobNew.objects.get(old_pk=job_host_summary.job_id)
            job_host_summary.new_job = new_job
            job_host_summary.save()

        # Update JobEvent job.
        for job_event in orm.JobEvent.objects.order_by('pk'):
            new_job = orm.JobNew.objects.get(old_pk=job_event.job_id)
            job_event.new_job = new_job
            job_event.save()

        # Update Host last_job.
        for host in orm.Host.objects.order_by('pk'):
            if not host.last_job:
                continue
            new_job = orm.JobNew.objects.get(old_pk=host.last_job_id)
            host.new_last_job = new_job
            host.save()

        # Update ActivityStream
        for a_s in orm.ActivityStream.objects.order_by('pk'):
            for project in a_s.project.all():
                new_project = orm.ProjectNew.objects.get(old_pk=project.pk)
                a_s.new_project.add(new_project)
            for project_update in a_s.project_update.all():
                new_project_update = orm.ProjectUpdateNew.objects.get(old_pk=project_update.pk)
                a_s.new_project_update.add(new_project_update)
            for inventory_source in a_s.inventory_source.all():
                new_inventory_source = orm.InventorySourceNew.objects.get(old_pk=inventory_source.pk)
                a_s.new_inventory_source.add(new_inventory_source)
            for inventory_update in a_s.inventory_update.all():
                new_inventory_update = orm.InventoryUpdateNew.objects.get(old_pk=inventory_update.pk)
                a_s.new_inventory_update.add(new_inventory_update)
            for job_template in a_s.job_template.all():
                new_job_template = orm.JobTemplateNew.objects.get(old_pk=job_template.pk)
                a_s.new_job_template.add(new_job_template)
            for job in a_s.job.all():
                new_job = orm.JobNew.objects.get(old_pk=job.pk)
                a_s.new_job.add(new_job)

    def backwards(self, orm):
        "Write your backwards methods here."
        
        # FIXME: Would like to have this, but not required.
        raise NotImplementedError()

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
            'new_inventory_source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventorySourceNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_inventory_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.InventoryUpdateNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_job': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.JobNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_job_template': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.JobTemplateNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_project': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ProjectNew']", 'symmetrical': 'False', 'blank': 'True'}),
            'new_project_update': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.ProjectUpdateNew']", 'symmetrical': 'False', 'blank': 'True'}),
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
            'new_inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['main.InventorySourceNew']"}),
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
            'new_inventory_sources': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'hosts'", 'blank': 'True', 'to': "orm['main.InventorySourceNew']"}),
            'new_last_job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts_as_last_job+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobNew']", 'blank': 'True', 'null': 'True'}),
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
            'Meta': {'object_name': 'InventorySource'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventorysources'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_current_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventory_source_as_last_update+'", 'null': 'True', 'to': "orm['main.InventoryUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventorysource\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '32'}),
            'update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'main.inventorysourcenew': {
            'Meta': {'object_name': 'InventorySourceNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventorysourcenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'group': ('awx.main.fields.AutoOneToOneField', [], {'related_name': "'new_inventory_source'", 'null': 'True', 'default': 'None', 'to': "orm['main.Group']", 'blank': 'True', 'unique': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_inventory_sources'", 'null': 'True', 'to': "orm['main.Inventory']"}),
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
            'Meta': {'object_name': 'InventoryUpdate'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventoryupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': "orm['main.InventorySource']"}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'license_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'inventoryupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'overwrite_vars': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'source_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_regions': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'source_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.inventoryupdatenew': {
            'Meta': {'object_name': 'InventoryUpdateNew', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'inventoryupdatenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'inventory_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inventory_updates'", 'to': "orm['main.InventorySourceNew']"}),
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
            'Meta': {'object_name': 'Job'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'blank': 'True', 'through': "orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
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
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'job\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'}),
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
            'new_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_job_events'", 'null': 'True', 'to': "orm['main.JobNew']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobEvent']", 'blank': 'True', 'null': 'True'}),
            'play': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'})
        },
        'main.jobhostsummary': {
            'Meta': {'ordering': "('-pk',)", 'unique_together': "[('job', 'host'), ('new_job', 'host')]", 'object_name': 'JobHostSummary'},
            'changed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'dark': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Host']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_host_summaries'", 'to': "orm['main.Job']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'new_job': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'new_job_host_summaries'", 'null': 'True', 'to': "orm['main.JobNew']"}),
            'ok': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'processed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skipped': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'main.jobnew': {
            'Meta': {'object_name': 'JobNew', '_ormbases': ['main.UnifiedJob']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'hosts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobnews'", 'blank': 'True', 'through': "orm['main.JobHostSummary']", 'to': "orm['main.Host']"}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobnews'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.JobTemplateNew']", 'blank': 'True', 'null': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
            u'unifiedjob_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.UnifiedJob']", 'unique': 'True', 'primary_key': 'True'}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'jobtemplate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Project']"}),
            'verbosity': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        'main.jobtemplatenew': {
            'Meta': {'object_name': 'JobTemplateNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'cloud_credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews_as_cloud_credential+'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['main.Credential']", 'blank': 'True', 'null': 'True'}),
            'extra_vars': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'forks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'host_config_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'inventory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobtemplatenews'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.Inventory']"}),
            'job_tags': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'limit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'playbook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'job_templates'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
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
            'new_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'organizations'", 'blank': 'True', 'to': "orm['main.ProjectNew']"}),
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
            'new_project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'permissions'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['main.ProjectNew']"}),
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
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projects'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'current_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_current_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'project_as_last_update+'", 'null': 'True', 'to': "orm['main.ProjectUpdate']"}),
            'last_update_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'project\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_next_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_update_cache_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'scm_update_on_launch': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'ok'", 'max_length': '32', 'null': 'True'})
        },
        'main.projectnew': {
            'Meta': {'object_name': 'ProjectNew', '_ormbases': ['main.UnifiedJobTemplate']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectnews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
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
            'Meta': {'object_name': 'ProjectUpdate'},
            '_result_stdout': ('django.db.models.fields.TextField', [], {'default': "''", 'db_column': "'result_stdout'", 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_created+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectupdates'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_args': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'job_cwd': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'job_env': ('jsonfield.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': '"{\'class\': \'projectupdate\', \'app_label\': \'main\'}(class)s_modified+"', 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': "orm['main.Project']"}),
            'result_stdout_file': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'result_traceback': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'scm_branch': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'scm_clean': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_delete_on_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scm_type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8', 'blank': 'True'}),
            'scm_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20'})
        },
        'main.projectupdatenew': {
            'Meta': {'object_name': 'ProjectUpdateNew', '_ormbases': ['main.UnifiedJob']},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'projectupdatenews'", 'null': 'True', 'blank': 'True', 'to': "orm['main.Credential']"}),
            'local_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_updates'", 'to': "orm['main.ProjectNew']"}),
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
            'new_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'teams'", 'blank': 'True', 'to': "orm['main.ProjectNew']"}),
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
    symmetrical = True
