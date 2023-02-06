from contextlib import suppress
import json

from awxkit.utils import filter_by_class, not_provided, random_title, update_payload, set_payload_foreign_key_args, PseudoNamespace
from awxkit.api.pages import Credential, Inventory, Project, UnifiedJobTemplate
from awxkit.api.mixins import HasCreate, HasInstanceGroups, HasNotifications, HasSurvey, HasCopy, DSAdapter
from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page


class JobTemplate(HasCopy, HasCreate, HasInstanceGroups, HasNotifications, HasSurvey, UnifiedJobTemplate):
    optional_dependencies = [Inventory, Credential, Project]
    NATURAL_KEY = ('organization', 'name')

    def launch(self, payload={}):
        """Launch the job_template using related->launch endpoint."""
        # get related->launch
        launch_pg = self.get_related('launch')

        # launch the job_template
        result = launch_pg.post(payload)

        # return job
        if result.json['type'] == 'job':
            jobs_pg = self.get_related('jobs', id=result.json['job'])
            assert jobs_pg.count == 1, "job_template launched (id:%s) but job not found in response at %s/jobs/" % (result.json['job'], self.url)
            return jobs_pg.results[0]
        elif result.json['type'] == 'workflow_job':
            slice_workflow_jobs = self.get_related('slice_workflow_jobs', id=result.json['id'])
            assert slice_workflow_jobs.count == 1, "job_template launched sliced job (id:%s) but not found in related %s/slice_workflow_jobs/" % (
                result.json['id'],
                self.url,
            )
            return slice_workflow_jobs.results[0]
        else:
            raise RuntimeError('Unexpected type of job template spawned job.')

    def payload(self, job_type='run', playbook='ping.yml', **kwargs):
        name = kwargs.get('name') or 'JobTemplate - {}'.format(random_title())
        description = kwargs.get('description') or random_title(10)
        payload = PseudoNamespace(name=name, description=description, job_type=job_type)

        optional_fields = (
            'ask_scm_branch_on_launch',
            'ask_credential_on_launch',
            'ask_diff_mode_on_launch',
            'ask_inventory_on_launch',
            'ask_job_type_on_launch',
            'ask_limit_on_launch',
            'ask_skip_tags_on_launch',
            'ask_tags_on_launch',
            'ask_variables_on_launch',
            'ask_verbosity_on_launch',
            'ask_execution_environment_on_launch',
            'ask_labels_on_launch',
            'ask_forks_on_launch',
            'ask_job_slice_count_on_launch',
            'ask_timeout_on_launch',
            'ask_instance_groups_on_launch',
            'allow_simultaneous',
            'become_enabled',
            'diff_mode',
            'force_handlers',
            'forks',
            'host_config_key',
            'job_tags',
            'limit',
            'skip_tags',
            'start_at_task',
            'survey_enabled',
            'timeout',
            'use_fact_cache',
            'vault_credential',
            'verbosity',
            'job_slice_count',
            'webhook_service',
            'webhook_credential',
            'scm_branch',
            'prevent_instance_group_fallback',
        )

        update_payload(payload, optional_fields, kwargs)

        extra_vars = kwargs.get('extra_vars', not_provided)
        if extra_vars != not_provided:
            if isinstance(extra_vars, dict):
                extra_vars = json.dumps(extra_vars)
            payload.update(extra_vars=extra_vars)

        if kwargs.get('project'):
            payload.update(project=kwargs.get('project').id, playbook=playbook)

        payload = set_payload_foreign_key_args(payload, ('inventory', 'credential', 'webhook_credential', 'execution_environment'), kwargs)

        return payload

    def add_label(self, label):
        if isinstance(label, page.Page):
            label = label.json
        with suppress(exc.NoContent):
            self.related.labels.post(label)

    def create_payload(self, name='', description='', job_type='run', playbook='ping.yml', credential=Credential, inventory=Inventory, project=None, **kwargs):
        if not project:
            project = Project
        if not inventory and not kwargs.get('ask_inventory_on_launch', False):
            inventory = Inventory

        self.create_and_update_dependencies(*filter_by_class((credential, Credential), (inventory, Inventory), (project, Project)))
        project = self.ds.project if project else None
        inventory = self.ds.inventory if inventory else None
        credential = self.ds.credential if credential else None

        payload = self.payload(
            name=name, description=description, job_type=job_type, playbook=playbook, credential=credential, inventory=inventory, project=project, **kwargs
        )
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload, credential

    def create(self, name='', description='', job_type='run', playbook='ping.yml', credential=Credential, inventory=Inventory, project=None, **kwargs):
        payload, credential = self.create_payload(
            name=name, description=description, job_type=job_type, playbook=playbook, credential=credential, inventory=inventory, project=project, **kwargs
        )
        ret = self.update_identity(JobTemplates(self.connection).post(payload))
        if credential:
            with suppress(exc.NoContent):
                self.related.credentials.post(dict(id=credential.id))
        if 'vault_credential' in kwargs:
            with suppress(exc.NoContent):
                if not isinstance(kwargs['vault_credential'], int):
                    raise ValueError("Expected 'vault_credential' value to be an integer, the id of the desired vault credential")
                self.related.credentials.post(dict(id=kwargs['vault_credential']))
        return ret

    def add_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=credential.id, associate=True))

    def remove_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=credential.id, disassociate=True))

    def remove_all_credentials(self):
        for cred in self.related.credentials.get().results:
            with suppress(exc.NoContent):
                self.related.credentials.post(dict(id=cred.id, disassociate=True))


page.register_page([resources.job_template, (resources.job_templates, 'post'), (resources.job_template_copy, 'post')], JobTemplate)


class JobTemplates(page.PageList, JobTemplate):
    pass


page.register_page([resources.job_templates, resources.related_job_templates], JobTemplates)


class JobTemplateCallback(base.Base):
    pass


page.register_page(resources.job_template_callback, JobTemplateCallback)


class JobTemplateLaunch(base.Base):
    pass


page.register_page(resources.job_template_launch, JobTemplateLaunch)


class JobTemplateCopy(base.Base):
    pass


page.register_page([resources.job_template_copy], JobTemplateCopy)
