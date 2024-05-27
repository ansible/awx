import json

from awxkit.api.pages import Credential, Organization, UnifiedJob, UnifiedJobTemplate
from awxkit.utils import filter_by_class, random_title, update_payload, set_payload_foreign_key_args, PseudoNamespace
from awxkit.api.mixins import HasCreate, HasNotifications, HasCopy, DSAdapter
from awxkit.api.resources import resources
from awxkit.config import config

from . import base
from . import page


class Project(HasCopy, HasCreate, HasNotifications, UnifiedJobTemplate):
    optional_dependencies = [Credential, Organization]
    optional_schedule_fields = tuple()
    NATURAL_KEY = ('organization', 'name')

    def payload(self, organization, scm_type='git', **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Project - {}'.format(random_title()),
            description=kwargs.get('description') or random_title(10),
            scm_type=scm_type,
            scm_url=kwargs.get('scm_url') or config.project_urls.get(scm_type, ''),
        )

        if organization is not None:
            payload.organization = organization.id

        if kwargs.get('credential'):
            payload.credential = kwargs.get('credential').id

        fields = (
            'scm_branch',
            'local_path',
            'scm_clean',
            'scm_delete_on_update',
            'scm_track_submodules',
            'scm_update_cache_timeout',
            'scm_update_on_launch',
            'scm_refspec',
            'allow_override',
            'signature_validation_credential',
        )
        update_payload(payload, fields, kwargs)

        payload = set_payload_foreign_key_args(payload, ('execution_environment', 'default_environment'), kwargs)

        return payload

    def create_payload(self, name='', description='', scm_type='git', scm_url='', scm_branch='', organization=Organization, credential=None, **kwargs):
        if credential:
            if isinstance(credential, Credential):
                if credential.ds.credential_type.namespace not in ('scm', 'insights'):
                    credential = None  # ignore incompatible credential from HasCreate dependency injection
            elif credential in (Credential,):
                credential = (Credential, dict(credential_type=(True, dict(kind='scm'))))
            elif credential is True:
                credential = (Credential, dict(credential_type=(True, dict(kind='scm'))))

        self.create_and_update_dependencies(*filter_by_class((credential, Credential), (organization, Organization)))

        credential = self.ds.credential if credential else None
        organization = self.ds.organization if organization else None

        payload = self.payload(
            organization=organization,
            scm_type=scm_type,
            name=name,
            description=description,
            scm_url=scm_url,
            scm_branch=scm_branch,
            credential=credential,
            **kwargs
        )
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', scm_type='git', scm_url='', scm_branch='', organization=Organization, credential=None, **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            scm_type=scm_type,
            scm_url=scm_url,
            scm_branch=scm_branch,
            organization=organization,
            credential=credential,
            **kwargs
        )
        self.update_identity(Projects(self.connection).post(payload))

        if kwargs.get('wait', True):
            update = self.related.current_update.get()
            update.wait_until_completed().assert_successful()
            return self.get()

        return self

    def update(self):
        """Update the project using related->update endpoint."""
        # get related->launch
        update_pg = self.get_related('update')

        # assert can_update == True
        assert update_pg.can_update, "The specified project (id:%s) is not able to update (can_update:%s)" % (self.id, update_pg.can_update)

        # start the update
        result = update_pg.post()

        # assert JSON response
        assert 'project_update' in result.json, "Unexpected JSON response when starting an project_update.\n%s" % json.dumps(result.json, indent=2)

        # locate and return the specific update
        jobs_pg = self.get_related('project_updates', id=result.json['project_update'])
        assert jobs_pg.count == 1, "An project_update started (id:%s) but job not found in response at %s/inventory_updates/" % (
            result.json['project_update'],
            self.url,
        )
        return jobs_pg.results[0]

    @property
    def is_successful(self):
        """An project is considered successful when:
        0) scm_type != ""
        1) unified_job_template.is_successful
        """
        return self.scm_type != "" and super(Project, self).is_successful


page.register_page([resources.project, (resources.projects, 'post'), (resources.project_copy, 'post')], Project)


class Projects(page.PageList, Project):
    pass


page.register_page([resources.projects, resources.related_projects], Projects)


class ProjectUpdate(UnifiedJob):
    pass


page.register_page(resources.project_update, ProjectUpdate)


class ProjectUpdates(page.PageList, ProjectUpdate):
    pass


page.register_page([resources.project_updates, resources.project_project_updates], ProjectUpdates)


class ProjectUpdateLaunch(base.Base):
    pass


page.register_page(resources.project_related_update, ProjectUpdateLaunch)


class ProjectUpdateCancel(base.Base):
    pass


page.register_page(resources.project_update_cancel, ProjectUpdateCancel)


class ProjectCopy(base.Base):
    pass


page.register_page(resources.project_copy, ProjectCopy)


class Playbooks(base.Base):
    pass


page.register_page(resources.project_playbooks, Playbooks)
