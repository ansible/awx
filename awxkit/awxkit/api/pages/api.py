import itertools
import logging

from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page
from .. import utils
from ..mixins import has_create

log = logging.getLogger(__name__)


EXPORTABLE_RESOURCES = [
    'users',
    'organizations',
    'teams',
    'credential_types',
    'credentials',
    'notification_templates',
    'projects',
    'inventory',
    'inventory_sources',
    'job_templates',
    'workflow_job_templates',
]


EXPORTABLE_RELATIONS = [
    'Roles',
    'NotificationTemplates',
    'WorkflowJobTemplateNodes',
    'Credentials',
    'Hosts',
    'Groups',
]


# These are special-case related objects, where we want only in this
# case to export a full object instead of a natural key reference.
DEPENDENT_EXPORT = [
    ('JobTemplate', 'labels'),
    ('JobTemplate', 'survey_spec'),
    ('JobTemplate', 'schedules'),
    ('WorkflowJobTemplate', 'labels'),
    ('WorkflowJobTemplate', 'survey_spec'),
    ('WorkflowJobTemplate', 'schedules'),
    ('WorkflowJobTemplate', 'workflow_nodes'),
    ('Project', 'schedules'),
    ('InventorySource', 'schedules'),
    ('Inventory', 'groups'),
    ('Inventory', 'hosts'),
]


# This is for related views where it is unneeded to export anything,
# such as because it is a calculated subset of objects covered by a
# different view.
DEPENDENT_NONEXPORT = [
    ('InventorySource', 'groups'),
    ('InventorySource', 'hosts'),
    ('Inventory', 'root_groups'),
    ('Group', 'all_hosts'),
    ('Group', 'potential_children'),
    ('Host', 'all_groups'),
]


class Api(base.Base):

    pass


page.register_page(resources.api, Api)


class ApiV2(base.Base):

    # Export methods

    def _export(self, _page, post_fields):
        # Drop any (credential_type) assets that are being managed by the Tower instance.
        if _page.json.get('managed_by_tower'):
            log.debug("%s is managed by Tower, skipping.", _page.endpoint)
            return None
        # Drop any hosts, groups, or inventories that were pulled in programmatically by an inventory source.
        if _page.json.get('has_inventory_sources'):
            return None
        if post_fields is None:  # Deprecated endpoint or insufficient permissions
            log.error("Object export failed: %s", _page.endpoint)
            return None

        # Note: doing _page[key] automatically parses json blob strings, which can be a problem.
        fields = {
            key: _page.json[key] for key in post_fields
            if key in _page.json and key not in _page.related and key != 'id'
        }

        for key in post_fields:
            if key in _page.related:
                related = _page.related[key]
            else:
                if post_fields[key]['type'] == 'id' and _page.json.get(key) is not None:
                    log.warning("Related link %r missing from %s, attempting to reconstruct endpoint.",
                                key, _page.endpoint)
                    resource = getattr(self, key, None)
                    if resource is None:
                        log.error("Unable to infer endpoint for %r on %s.", key, _page.endpoint)
                        continue
                    related = self._filtered_list(resource, _page.json[key]).results[0]
                else:
                    continue

            rel_endpoint = self._cache.get_page(related)
            if rel_endpoint is None:  # This foreign key is unreadable
                if post_fields[key].get('required'):
                    log.error("Foreign key %r export failed for object %s.", key, _page.endpoint)
                    return None
                log.warning("Foreign key %r export failed for object %s, setting to null", key, _page.endpoint)
                continue
            rel_natural_key = rel_endpoint.get_natural_key(self._cache)
            if rel_natural_key is None:
                log.error("Unable to construct a natural key for foreign key %r of object %s.",
                          key, _page.endpoint)
                return None  # This foreign key has unresolvable dependencies
            fields[key] = rel_natural_key

        related = {}
        for key, rel_endpoint in _page.related.items():
            if key in post_fields or not rel_endpoint:
                continue

            rel = rel_endpoint._create()
            is_relation = rel.__class__.__name__ in EXPORTABLE_RELATIONS
            is_dependent = (_page.__item_class__.__name__, key) in DEPENDENT_EXPORT
            is_blocked = (_page.__item_class__.__name__, key) in DEPENDENT_NONEXPORT
            if is_blocked or not (is_relation or is_dependent):
                continue

            rel_post_fields = utils.get_post_fields(rel_endpoint, self._cache)
            if rel_post_fields is None:
                log.debug("%s is a read-only endpoint.", rel_endpoint)
                continue
            is_attach = 'id' in rel_post_fields  # This is not a create-only endpoint.

            if is_dependent:
                by_natural_key = False
            elif is_relation and is_attach and not is_blocked:
                by_natural_key = True
            else:
                continue

            rel_page = self._cache.get_page(rel_endpoint)
            if rel_page is None:
                continue

            if 'results' in rel_page:
                results = (
                    x.get_natural_key(self._cache) if by_natural_key else self._export(x, rel_post_fields)
                    for x in rel_page.results
                )
                related[key] = [x for x in results if x is not None]
            else:
                related[key] = rel_page.json

        if related:
            fields['related'] = related

        natural_key = _page.get_natural_key(self._cache)
        if natural_key is None:
            log.error("Unable to construct a natural key for object %s.", _page.endpoint)
            return None
        fields['natural_key'] = natural_key

        return utils.remove_encrypted(fields)

    def _export_list(self, endpoint):
        post_fields = utils.get_post_fields(endpoint, self._cache)
        if post_fields is None:
            return None

        if isinstance(endpoint, page.TentativePage):
            endpoint = self._cache.get_page(endpoint)
            if endpoint is None:
                return None

        assets = (self._export(asset, post_fields) for asset in endpoint.results)
        return [asset for asset in assets if asset is not None]

    def _filtered_list(self, endpoint, value):
        if isinstance(value, int) or value.isdecimal():
            return endpoint.get(id=int(value))
        options = self._cache.get_options(endpoint)
        identifier = next(field for field in options['search_fields']
                          if field in ('name', 'username', 'hostname'))
        return endpoint.get(**{identifier: value})

    def export_assets(self, **kwargs):
        self._cache = page.PageCache()

        # If no resource kwargs are explicitly used, export everything.
        all_resources = all(kwargs.get(resource) is None for resource in EXPORTABLE_RESOURCES)

        data = {}
        for resource in EXPORTABLE_RESOURCES:
            value = kwargs.get(resource)
            if all_resources or value is not None:
                endpoint = getattr(self, resource)
                if value:
                    endpoint = self._filtered_list(endpoint, value)
                data[resource] = self._export_list(endpoint)

        return data

    # Import methods

    def _dependent_resources(self, data):
        page_resource = {getattr(self, resource)._create().__item_class__: resource
                         for resource in self.json}
        data_pages = [getattr(self, resource)._create().__item_class__ for resource in EXPORTABLE_RESOURCES]

        for page_cls in itertools.chain(*has_create.page_creation_order(*data_pages)):
            yield page_resource[page_cls]

    def _import_list(self, endpoint, assets):
        log.debug("_import_list -- endpoint: %s, assets: %s", endpoint.endpoint, repr(assets))
        post_fields = utils.get_post_fields(endpoint, self._cache)

        changed = False

        for asset in assets:
            post_data = {}
            for field, value in asset.items():
                if field not in post_fields:
                    continue
                if post_fields[field]['type'] in ('id', 'integer') and isinstance(value, dict):
                    _page = self._cache.get_by_natural_key(value)
                    post_data[field] = _page['id'] if _page is not None else None
                else:
                    post_data[field] = value

            _page = self._cache.get_by_natural_key(asset['natural_key'])
            try:
                if _page is None:
                    if asset['natural_key']['type'] == 'user':
                        # We should only impose a default password if the resource doesn't exist.
                        post_data.setdefault('password', 'abc123')
                    _page = endpoint.post(post_data)
                    changed = True
                    if asset['natural_key']['type'] == 'project':
                        # When creating a project, we need to wait for its
                        # first project update to finish so that associated
                        # JTs have valid options for playbook names
                        _page.wait_until_completed()
                else:
                    _page = _page.put(post_data)
                    changed = True
            except (exc.Common, AssertionError) as e:
                log.error("Object import failed: %s.", e)
                log.debug("post_data: %r", post_data)
                continue

            self._cache.set_page(_page)

            # Queue up everything related to be either created or assigned.
            for name, S in asset.get('related', {}).items():
                if not S:
                    continue
                if name == 'roles':
                    self._roles.append((_page, S))
                else:
                    self._related.append((_page, name, S))

        return changed

    def _assign_role(self, endpoint, role):
        if 'content_object' not in role:
            return
        obj_page = self._cache.get_by_natural_key(role['content_object'])
        if obj_page is None:
            return
        role_page = obj_page.get_object_role(role['name'], by_name=True)
        try:
            endpoint.post({'id': role_page['id']})
        except exc.NoContent:  # desired exception on successful (dis)association
            pass
        except exc.Common as e:
            log.error("Role assignment failed: %s.", e)
            log.debug("post_data: %r", {'id': role_page['id']})

    def _assign_membership(self):
        for _page, roles in self._roles:
            role_endpoint = _page.json['related']['roles']
            for role in roles:
                if role['name'] == 'Member':
                    self._assign_role(role_endpoint, role)

    def _assign_roles(self):
        for _page, roles in self._roles:
            role_endpoint = _page.json['related']['roles']
            for role in roles:
                if role['name'] != 'Member':
                    self._assign_role(role_endpoint, role)

    def _assign_related(self):
        for _page, name, related_set in self._related:
            endpoint = _page.related[name]
            if isinstance(related_set, dict):  # Related that are just json blobs, e.g. survey_spec
                endpoint.post(related_set)
                continue

            if 'natural_key' not in related_set[0]:  # It is an attach set
                # Try to impedance match
                related = endpoint.get(all_pages=True)
                existing = {rel['id'] for rel in related.results}
                for item in related_set:
                    rel_page = self._cache.get_by_natural_key(item)
                    if rel_page is None:
                        continue  # FIXME
                    if rel_page['id'] in existing:
                        continue
                    try:
                        post_data = {'id': rel_page['id']}
                        endpoint.post(post_data)
                        log.error("endpoint: %s, id: %s", endpoint.endpoint, rel_page['id'])
                    except exc.NoContent:  # desired exception on successful (dis)association
                        pass
                    except exc.Common as e:
                        log.error("Object association failed: %s.", e)
                        log.debug("post_data: %r", post_data)
            else:  # It is a create set
                self._cache.get_page(endpoint)
                self._import_list(endpoint, related_set)

            # FIXME: deal with pruning existing relations that do not match the import set

    def import_assets(self, data):
        self._cache = page.PageCache()
        self._related = []
        self._roles = []

        changed = False

        for resource in self._dependent_resources(data):
            endpoint = getattr(self, resource)
            # Load up existing objects, so that we can try to update or link to them
            self._cache.get_page(endpoint)
            imported = self._import_list(endpoint, data.get(resource) or [])
            changed = changed or imported
            # FIXME: should we delete existing unpatched assets?

        self._assign_related()
        self._assign_membership()
        self._assign_roles()

        return changed


page.register_page(resources.v2, ApiV2)
