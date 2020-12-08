import logging

from awxkit.api.mixins import DSAdapter, HasCreate
from awxkit.api.pages import (
    Credential,
    Organization,
)
from awxkit.api.resources import resources
from awxkit.utils import random_title, PseudoNamespace

from . import base
from . import page


log = logging.getLogger(__name__)


class ExecutionEnvironment(HasCreate, base.Base):

    dependencies = [Organization, Credential]
    NATURAL_KEY = ('name',)

    # fields are name, image, organization, managed_by_tower, credential
    def create(self, name='', image='quay.io/ansible/ansible-runner:devel', credential=None, **kwargs):
        # we do not want to make a credential by default
        payload = self.create_payload(name=name, image=image, credential=credential, **kwargs)
        ret = self.update_identity(ExecutionEnvironments(self.connection).post(payload))
        return ret

    def create_payload(self, name='', organization=Organization, **kwargs):
        self.create_and_update_dependencies(organization)
        payload = self.payload(name=name, organization=self.ds.organization, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def payload(self, name='', image=None, organization=None, credential=None, **kwargs):
        payload = PseudoNamespace(
            name=name or "EE - {}".format(random_title()),
            image=image or random_title(10),
            organization=organization.id if organization else None,
            credential=credential.id if credential else None,
            **kwargs
        )

        return payload


page.register_page([resources.execution_environment,
                    (resources.execution_environments, 'post'),
                    (resources.organization_execution_environments, 'post')], ExecutionEnvironment)


class ExecutionEnvironments(page.PageList, ExecutionEnvironment):
    pass


page.register_page([resources.execution_environments,
                    resources.organization_execution_environments], ExecutionEnvironments)
