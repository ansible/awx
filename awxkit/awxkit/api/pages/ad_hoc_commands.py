from awxkit.utils import update_payload, PseudoNamespace
from awxkit.api.pages import Inventory, Credential
from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.utils import not_provided as np
from awxkit.api.resources import resources

from .jobs import UnifiedJob
from . import page


class AdHocCommand(HasCreate, UnifiedJob):

    dependencies = [Inventory, Credential]

    def relaunch(self, payload={}):
        """Relaunch the command using the related->relaunch endpoint"""
        # navigate to relaunch_pg
        relaunch_pg = self.get_related('relaunch')

        # relaunch the command
        result = relaunch_pg.post(payload)

        # return the corresponding command_pg
        return self.walk(result.url)

    def payload(self, inventory, credential, module_name='ping', **kwargs):
        payload = PseudoNamespace(inventory=inventory.id, credential=credential.id, module_name=module_name)

        optional_fields = ('diff_mode', 'extra_vars', 'module_args', 'job_type', 'limit', 'forks', 'verbosity')
        return update_payload(payload, optional_fields, kwargs)

    def create_payload(self, module_name='ping', module_args=np, job_type=np, limit=np, verbosity=np, inventory=Inventory, credential=Credential, **kwargs):

        self.create_and_update_dependencies(inventory, credential)

        payload = self.payload(
            module_name=module_name,
            module_args=module_args,
            job_type=job_type,
            limit=limit,
            verbosity=verbosity,
            inventory=self.ds.inventory,
            credential=self.ds.credential,
            **kwargs
        )
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, module_name='ping', module_args=np, job_type=np, limit=np, verbosity=np, inventory=Inventory, credential=Credential, **kwargs):

        payload = self.create_payload(
            module_name=module_name,
            module_args=module_args,
            job_type=job_type,
            limit=limit,
            verbosity=verbosity,
            inventory=inventory,
            credential=credential,
            **kwargs
        )
        return self.update_identity(AdHocCommands(self.connection).post(payload))


page.register_page([resources.ad_hoc_command], AdHocCommand)


class AdHocCommands(page.PageList, AdHocCommand):

    pass


page.register_page(
    [resources.ad_hoc_commands, resources.inventory_related_ad_hoc_commands, resources.group_related_ad_hoc_commands, resources.host_related_ad_hoc_commands],
    AdHocCommands,
)
