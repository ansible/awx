import logging
import json
import re

from awxkit.api.pages import (
    Credential,
    Organization,
    Project,
    UnifiedJob,
    UnifiedJobTemplate
)
from awxkit.utils import (
    filter_by_class,
    random_title,
    update_payload,
    suppress,
    not_provided,
    PseudoNamespace,
    poll_until,
    random_utf8
)
from awxkit.api.mixins import DSAdapter, HasCreate, HasInstanceGroups, HasNotifications, HasVariables, HasCopy
from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page


log = logging.getLogger(__name__)


class Inventory(HasCopy, HasCreate, HasInstanceGroups, HasVariables, base.Base):

    dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def print_ini(self):
        """Print an ini version of the inventory"""
        output = list()
        inv_dict = self.related.script.get(hostvars=1).json

        for group in inv_dict.keys():
            if group == '_meta':
                continue

            # output host groups
            output.append('[%s]' % group)
            for host in inv_dict[group].get('hosts', []):
                # FIXME ... include hostvars
                output.append(host)
            output.append('')  # newline

            # output child groups
            if inv_dict[group].get('children', []):
                output.append('[%s:children]' % group)
                for child in inv_dict[group].get('children', []):
                    output.append(child)
                output.append('')  # newline

            # output group vars
            if inv_dict[group].get('vars', {}).items():
                output.append('[%s:vars]' % group)
                for k, v in inv_dict[group].get('vars', {}).items():
                    output.append('%s=%s' % (k, v))
                output.append('')  # newline

        print('\n'.join(output))

    def payload(self, organization, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Inventory - {}'.format(
                random_title()),
            description=kwargs.get('description') or random_title(10),
            organization=organization.id)

        optional_fields = (
            'host_filter',
            'insights_credential',
            'kind',
            'variables')

        update_payload(payload, optional_fields, kwargs)

        if 'variables' in payload and isinstance(payload.variables, dict):
            payload.variables = json.dumps(payload.variables)
        if 'insights_credential' in payload and isinstance(
                payload.insights_credential, Credential):
            payload.insights_credential = payload.insights_credential.id

        return payload

    def create_payload(
            self,
            name='',
            description='',
            organization=Organization,
            **kwargs):
        self.create_and_update_dependencies(organization)
        payload = self.payload(
            name=name,
            description=description,
            organization=self.ds.organization,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(
            self,
            name='',
            description='',
            organization=Organization,
            **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            organization=organization,
            **kwargs)
        return self.update_identity(
            Inventories(
                self.connection).post(payload))

    def add_host(self, host=None):
        if host is None:
            return self.related.hosts.create(inventory=self)

        if isinstance(host, base.Base):
            host = host.json
        with suppress(exc.NoContent):
            self.related.hosts.post(host)
        return host

    def wait_until_deleted(self):
        def _wait():
            try:
                self.get()
            except exc.NotFound:
                return True
        poll_until(_wait, interval=1, timeout=60)

    def update_inventory_sources(self, wait=False):
        response = self.related.update_inventory_sources.post()
        source_ids = [entry['inventory_source']
                      for entry in response if entry['status'] == 'started']

        inv_updates = []
        for source_id in source_ids:
            inv_source = self.related.inventory_sources.get(
                id=source_id).results.pop()
            inv_updates.append(inv_source.related.current_job.get())

        if wait:
            for update in inv_updates:
                update.wait_until_completed()
        return inv_updates


page.register_page([resources.inventory,
                    (resources.inventories, 'post'),
                    (resources.inventory_copy, 'post')], Inventory)


class Inventories(page.PageList, Inventory):

    pass


page.register_page([resources.inventories,
                    resources.related_inventories], Inventories)


class InventoryScript(HasCopy, HasCreate, base.Base):

    dependencies = [Organization]

    def payload(self, organization, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Inventory Script - {}'.format(
                random_title()),
            description=kwargs.get('description') or random_title(10),
            organization=organization.id,
            script=kwargs.get('script') or self._generate_script())
        return payload

    def create_payload(
            self,
            name='',
            description='',
            organization=Organization,
            script='',
            **kwargs):
        self.create_and_update_dependencies(organization)
        payload = self.payload(
            name=name,
            description=description,
            organization=self.ds.organization,
            script=script,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(
            self,
            name='',
            description='',
            organization=Organization,
            script='',
            **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            organization=organization,
            script=script,
            **kwargs)
        return self.update_identity(
            InventoryScripts(
                self.connection).post(payload))

    def _generate_script(self):
        script = '\n'.join([
            '#!/usr/bin/env python',
            '# -*- coding: utf-8 -*-',
            'import json',
            'inventory = dict()',
            'inventory["{0}"] = dict()',
            'inventory["{0}"]["hosts"] = list()',
            'inventory["{0}"]["hosts"].append("{1}")',
            'inventory["{0}"]["hosts"].append("{2}")',
            'inventory["{0}"]["hosts"].append("{3}")',
            'inventory["{0}"]["hosts"].append("{4}")',
            'inventory["{0}"]["hosts"].append("{5}")',
            'inventory["{0}"]["vars"] = dict(ansible_host="127.0.0.1", ansible_connection="local")',
            'print(json.dumps(inventory))'
        ])
        group_name = re.sub(r"[\']", "", "group_{}".format(random_title(non_ascii=False)))
        host_names = [
            re.sub(
                r"[\':]",
                "",
                "host_{}".format(
                    random_utf8())) for _ in range(5)]

        return script.format(group_name, *host_names)


page.register_page([resources.inventory_script,
                    (resources.inventory_scripts, 'post'),
                    (resources.inventory_script_copy, 'post')], InventoryScript)


class InventoryScripts(page.PageList, InventoryScript):

    pass


page.register_page([resources.inventory_scripts], InventoryScripts)


class Group(HasCreate, HasVariables, base.Base):

    dependencies = [Inventory]
    optional_dependencies = [Credential, InventoryScript]
    NATURAL_KEY = ('name', 'inventory')

    @property
    def is_root_group(self):
        """Returns whether the current group is a top-level root group in the inventory"""
        return self.related.inventory.get().related.root_groups.get(id=self.id).count == 1

    def get_parents(self):
        """Inspects the API and returns all groups that include the current group as a child."""
        return Groups(self.connection).get(children=self.id).results

    def payload(self, inventory, credential=None, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Group{}'.format(
                random_title(
                    non_ascii=False)),
            description=kwargs.get('description') or random_title(10),
            inventory=inventory.id)

        if credential:
            payload.credential = credential.id

        update_payload(payload, ('variables',), kwargs)

        if 'variables' in payload and isinstance(payload.variables, dict):
            payload.variables = json.dumps(payload.variables)

        return payload

    def create_payload(
            self,
            name='',
            description='',
            inventory=Inventory,
            credential=None,
            source_script=None,
            **kwargs):
        credential, source_script = filter_by_class(
            (credential, Credential), (source_script, InventoryScript))
        self.create_and_update_dependencies(
            inventory, credential, source_script)
        credential = self.ds.credential if credential else None
        payload = self.payload(
            inventory=self.ds.inventory,
            credential=credential,
            name=name,
            description=description,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', inventory=Inventory, **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            inventory=inventory,
            **kwargs)

        parent = kwargs.get('parent', None)  # parent must be a Group instance
        resource = parent.related.children if parent else Groups(
            self.connection)
        return self.update_identity(resource.post(payload))

    def add_host(self, host=None):
        if host is None:
            host = self.related.hosts.create(inventory=self.ds.inventory)
            with suppress(exc.NoContent):
                host.related.groups.post(dict(id=self.id))
            return host

        if isinstance(host, base.Base):
            host = host.json
        with suppress(exc.NoContent):
            self.related.hosts.post(host)
        return host

    def add_group(self, group):
        if isinstance(group, page.Page):
            group = group.json
        with suppress(exc.NoContent):
            self.related.children.post(group)

    def remove_group(self, group):
        if isinstance(group, page.Page):
            group = group.json
        with suppress(exc.NoContent):
            self.related.children.post(dict(id=group.id, disassociate=True))


page.register_page([resources.group,
                    (resources.groups, 'post')], Group)


class Groups(page.PageList, Group):

    pass


page.register_page([resources.groups,
                    resources.host_groups,
                    resources.inventory_related_groups,
                    resources.inventory_related_root_groups,
                    resources.group_children,
                    resources.group_potential_children], Groups)


class Host(HasCreate, HasVariables, base.Base):

    dependencies = [Inventory]
    NATURAL_KEY = ('name', 'inventory')

    def payload(self, inventory, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Host{}'.format(
                random_title(
                    non_ascii=False)),
            description=kwargs.get('description') or random_title(10),
            inventory=inventory.id)

        optional_fields = ('enabled', 'instance_id')

        update_payload(payload, optional_fields, kwargs)

        variables = kwargs.get('variables', not_provided)

        if variables is None:
            variables = dict(
                ansible_host='127.0.0.1',
                ansible_connection='local')

        if variables != not_provided:
            if isinstance(variables, dict):
                variables = json.dumps(variables)
            payload.variables = variables

        return payload

    def create_payload(
            self,
            name='',
            description='',
            variables=None,
            inventory=Inventory,
            **kwargs):
        self.create_and_update_dependencies(
            *filter_by_class((inventory, Inventory)))
        payload = self.payload(
            inventory=self.ds.inventory,
            name=name,
            description=description,
            variables=variables,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(
            self,
            name='',
            description='',
            variables=None,
            inventory=Inventory,
            **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            variables=variables,
            inventory=inventory,
            **kwargs)
        return self.update_identity(Hosts(self.connection).post(payload))


page.register_page([resources.host,
                    (resources.hosts, 'post')], Host)


class Hosts(page.PageList, Host):

    pass


page.register_page([resources.hosts,
                    resources.group_related_hosts,
                    resources.inventory_related_hosts,
                    resources.inventory_sources_related_hosts], Hosts)


class FactVersion(base.Base):

    pass


page.register_page(resources.host_related_fact_version, FactVersion)


class FactVersions(page.PageList, FactVersion):

    @property
    def count(self):
        return len(self.results)


page.register_page(resources.host_related_fact_versions, FactVersions)


class FactView(base.Base):

    pass


page.register_page(resources.fact_view, FactView)


class InventorySource(HasCreate, HasNotifications, UnifiedJobTemplate):

    optional_schedule_fields = tuple()
    dependencies = [Inventory]
    optional_dependencies = [Credential, InventoryScript, Project]
    NATURAL_KEY = ('organization', 'name', 'inventory')

    def payload(
            self,
            inventory,
            source='custom',
            credential=None,
            source_script=None,
            project=None,
            **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'InventorySource - {}'.format(
                random_title()),
            description=kwargs.get('description') or random_title(10),
            inventory=inventory.id,
            source=source)

        if credential:
            payload.credential = credential.id
        if source_script:
            payload.source_script = source_script.id
        if project:
            payload.source_project = project.id

        optional_fields = (
            'source_path',
            'source_vars',
            'timeout',
            'overwrite',
            'overwrite_vars',
            'update_cache_timeout',
            'update_on_launch',
            'update_on_project_update',
            'verbosity')

        update_payload(payload, optional_fields, kwargs)

        return payload

    def create_payload(
            self,
            name='',
            description='',
            source='custom',
            inventory=Inventory,
            credential=None,
            source_script=InventoryScript,
            project=None,
            **kwargs):
        if source != 'custom' and source_script == InventoryScript:
            source_script = None
        if source == 'scm':
            kwargs.setdefault('overwrite_vars', True)
            if project is None:
                project = Project

        inventory, credential, source_script, project = filter_by_class((inventory, Inventory),
                                                                        (credential, Credential),
                                                                        (source_script, InventoryScript),
                                                                        (project, Project))
        self.create_and_update_dependencies(
            inventory, credential, source_script, project)

        if credential:
            credential = self.ds.credential
        if source_script:
            source_script = self.ds.inventory_script
        if project:
            project = self.ds.project

        payload = self.payload(
            inventory=self.ds.inventory,
            source=source,
            credential=credential,
            source_script=source_script,
            project=project,
            name=name,
            description=description,
            **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(
            self,
            name='',
            description='',
            source='custom',
            inventory=Inventory,
            credential=None,
            source_script=InventoryScript,
            project=None,
            **kwargs):
        payload = self.create_payload(
            name=name,
            description=description,
            source=source,
            inventory=inventory,
            credential=credential,
            source_script=source_script,
            project=project,
            **kwargs)
        return self.update_identity(
            InventorySources(
                self.connection).post(payload))

    def update(self):
        """Update the inventory_source using related->update endpoint"""
        # get related->launch
        update_pg = self.get_related('update')

        # assert can_update == True
        assert update_pg.can_update, \
            "The specified inventory_source (id:%s) is not able to update (can_update:%s)" % \
            (self.id, update_pg.can_update)

        # start the inventory_update
        result = update_pg.post()

        # assert JSON response
        assert 'inventory_update' in result.json, \
            "Unexpected JSON response when starting an inventory_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # locate and return the inventory_update
        jobs_pg = self.related.inventory_updates.get(
            id=result.json['inventory_update'])
        assert jobs_pg.count == 1, \
            "An inventory_update started (id:%s) but job not found in response at %s/inventory_updates/" % \
            (result.json['inventory_update'], self.url)
        return jobs_pg.results[0]

    @property
    def is_successful(self):
        """An inventory_source is considered successful when source != "" and super().is_successful ."""
        return self.source != "" and super(
            InventorySource, self).is_successful

    def add_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(
                dict(id=credential.id, associate=True))

    def remove_credential(self, credential):
        with suppress(exc.NoContent):
            self.related.credentials.post(
                dict(id=credential.id, disassociate=True))


page.register_page([resources.inventory_source,
                    (resources.inventory_sources, 'post')], InventorySource)


class InventorySources(page.PageList, InventorySource):

    pass


page.register_page([resources.inventory_sources,
                    resources.related_inventory_sources],
                   InventorySources)


class InventorySourceGroups(page.PageList, Group):

    pass


page.register_page(
    resources.inventory_sources_related_groups,
    InventorySourceGroups)


class InventorySourceUpdate(base.Base):

    pass


page.register_page([resources.inventory_sources_related_update,
                    resources.inventory_related_update_inventory_sources],
                   InventorySourceUpdate)


class InventoryUpdate(UnifiedJob):

    pass


page.register_page(resources.inventory_update, InventoryUpdate)


class InventoryUpdates(page.PageList, InventoryUpdate):

    pass


page.register_page([resources.inventory_updates,
                    resources.inventory_source_updates,
                    resources.project_update_scm_inventory_updates],
                   InventoryUpdates)


class InventoryUpdateCancel(base.Base):

    pass


page.register_page(resources.inventory_update_cancel, InventoryUpdateCancel)


class InventoryCopy(base.Base):

    pass


page.register_page(resources.inventory_copy, InventoryCopy)
