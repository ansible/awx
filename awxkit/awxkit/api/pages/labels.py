from awxkit.utils import random_title, PseudoNamespace
from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.api.resources import resources
from awxkit.api.pages import Organization
from . import base
from . import page


class Label(HasCreate, base.Base):
    dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def silent_delete(self):
        """Label pages do not support DELETE requests. Here, we override the base page object
        silent_delete method to account for this.
        """
        pass

    def payload(self, organization, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Label - {}'.format(random_title()),
            description=kwargs.get('description') or random_title(10),
            organization=organization.id,
        )
        return payload

    def create_payload(self, name='', description='', organization=Organization, **kwargs):
        self.create_and_update_dependencies(organization)
        payload = self.payload(organization=self.ds.organization, name=name, description=description, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', organization=Organization, **kwargs):
        payload = self.create_payload(name=name, description=description, organization=organization, **kwargs)
        return self.update_identity(Labels(self.connection).post(payload))


page.register_page([resources.label, (resources.labels, 'post')], Label)


class Labels(page.PageList, Label):
    pass


page.register_page(
    [resources.labels, resources.inventory_labels, resources.job_labels, resources.job_template_labels, resources.workflow_job_template_labels], Labels
)
