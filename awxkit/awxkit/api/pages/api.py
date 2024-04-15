from collections import defaultdict
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
    'execution_environments',
    'applications',
    'schedules',
]


EXPORTABLE_RELATIONS = ['Roles', 'NotificationTemplates', 'WorkflowJobTemplateNodes', 'Credentials', 'Hosts', 'Groups', 'ExecutionEnvironments', 'Schedules']


# These are special-case related objects, where we want only in this
# case to export a full object instead of a natural key reference.
DEPENDENT_EXPORT = [
    ('JobTemplate', 'Label'),
    ('JobTemplate', 'SurveySpec'),
    ('JobTemplate', 'Schedule'),
    ('WorkflowJobTemplate', 'Label'),
    ('WorkflowJobTemplate', 'SurveySpec'),
    ('WorkflowJobTemplate', 'Schedule'),
    ('WorkflowJobTemplate', 'WorkflowJobTemplateNode'),
    ('InventorySource', 'Schedule'),
    ('Inventory', 'Group'),
    ('Inventory', 'Host'),
    ('Inventory', 'Label'),
    ('WorkflowJobTemplateNode', 'WorkflowApprovalTemplate'),
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
    ('WorkflowJobTemplateNode', 'create_approval_template'),
]


class Api(base.Base):
    pass


page.register_page(resources.api, Api)


class ApiV2(base.Base):
    # Export methods

    def _export(self, _page, post_fields):
        # Drop any (credential_type) assets that are being managed by the instance.
        if _page.json.get('managed'):
            log.debug("%s is managed, skipping.", _page.endpoint)
            return None
        if post_fields is None:  # Deprecated endpoint or insufficient permissions
            log.error("Object export failed: %s", _page.endpoint)
            self._has_error = True
            return None

        # Note: doing _page[key] automatically parses json blob strings, which can be a problem.
        fields = {key: _page.json[key] for key in post_fields if key in _page.json and key not in _page.related and key != 'id'}

        # iterate over direct fields in the object
        for key in post_fields:
            if key in _page.related:
                related = _page.related[key]
            else:
                if post_fields[key]['type'] == 'id' and _page.json.get(key) is not None:
                    log.warning("Related link %r missing from %s, attempting to reconstruct endpoint.", key, _page.endpoint)
                    res_pattern, resource = getattr(resources, key, None), None
                    if res_pattern:
                        try:
                            top_level = res_pattern.split('/')[3]
                            resource = getattr(self, top_level, None)
                        except IndexError:
                            pass
                    if resource is None:
                        log.error("Unable to infer endpoint for %r on %s.", key, _page.endpoint)
                        self._has_error = True
                        continue
                    related = self._filtered_list(resource, _page.json[key]).results[0]
                else:
                    continue

            rel_endpoint = self._cache.get_page(related)
            if rel_endpoint is None:  # This foreign key is unreadable
                if post_fields[key].get('required'):
                    log.error("Foreign key %r export failed for object %s.", key, _page.endpoint)
                    self._has_error = True
                    return None
                log.warning("Foreign key %r export failed for object %s, setting to null", key, _page.endpoint)
                continue

            # Workflow approval templates have a special creation endpoint,
            # therefore we are skipping the export via natural key.
            if rel_endpoint.__item_class__.__name__ == 'WorkflowApprovalTemplate':
                continue

            rel_natural_key = rel_endpoint.get_natural_key(self._cache)
            if rel_natural_key is None:
                log.error("Unable to construct a natural key for foreign key %r of object %s.", key, _page.endpoint)
                self._has_error = True
                return None  # This foreign key has unresolvable dependencies
            fields[key] = rel_natural_key

        # iterate over related fields in the object
        related = {}
        for key, rel_endpoint in _page.related.items():
            # skip if no endpoint for this related object
            if not rel_endpoint:
                continue

            rel = rel_endpoint._create()

            if rel.__item_class__.__name__ != 'WorkflowApprovalTemplate':
                if key in post_fields:
                    continue

            is_relation = rel.__class__.__name__ in EXPORTABLE_RELATIONS

            # determine if the parent object and the related object that we are processing through are related
            # if this tuple is in the DEPENDENT_EXPORT than we output the full object
            # else we output the natural key
            is_dependent = (_page.__item_class__.__name__, rel.__item_class__.__name__) in DEPENDENT_EXPORT

            is_blocked = (_page.__item_class__.__name__, key) in DEPENDENT_NONEXPORT
            if is_blocked or not (is_relation or is_dependent):
                continue

            # if the rel is of WorkflowApprovalTemplate type, get rel_post_fields from create_approval_template endpoint
            rel_option_endpoint = rel_endpoint
            export_key = key
            if rel.__item_class__.__name__ == 'WorkflowApprovalTemplate':
                export_key = 'create_approval_template'
                rel_option_endpoint = _page.related.get('create_approval_template')

            rel_post_fields = utils.get_post_fields(rel_option_endpoint, self._cache)
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
                results = (x.get_natural_key(self._cache) if by_natural_key else self._export(x, rel_post_fields) for x in rel_page.results)
                related[export_key] = [x for x in results if x is not None]
            elif rel.__item_class__.__name__ == 'WorkflowApprovalTemplate':
                related[export_key] = self._export(rel_page, rel_post_fields)
            else:
                related[export_key] = rel_page.json

        if related:
            fields['related'] = related

        if _page.__item_class__.__name__ != 'WorkflowApprovalTemplate':
            natural_key = _page.get_natural_key(self._cache)
            if natural_key is None:
                log.error("Unable to construct a natural key for object %s.", _page.endpoint)
                self._has_error = True
                return None
            fields['natural_key'] = natural_key

        return fields

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

    def _check_for_int(self, value):
        return isinstance(value, int) or (isinstance(value, str) and value.isdecimal())

    def _filtered_list(self, endpoint, value):
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if self._check_for_int(value):
            return endpoint.get(id=int(value))

        options = self._cache.get_options(endpoint)
        identifier = next(field for field in options['search_fields'] if field in ('name', 'username', 'hostname'))
        if isinstance(value, list):
            if all(self._check_for_int(item) for item in value):
                identifier = 'or__id'
            else:
                identifier = 'or__' + identifier

        return endpoint.get(**{identifier: value}, all_pages=True)

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

    def _dependent_resources(self):
        page_resource = {}
        for resource in self.json:
            # The /api/v2/constructed_inventories endpoint is for the UI but will register as an Inventory endpoint
            # We want to map the type to /api/v2/inventories/ which works for constructed too
            if resource == 'constructed_inventory':
                continue
            page_resource[getattr(self, resource)._create().__item_class__] = resource
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
                    post_data[field] = utils.remove_encrypted(value)

            _page = self._cache.get_by_natural_key(asset['natural_key'])
            try:
                if _page is None:
                    if asset['natural_key']['type'] == 'user':
                        # We should only impose a default password if the resource doesn't exist.
                        post_data.setdefault('password', 'abc123')
                    try:
                        _page = endpoint.post(post_data)
                    except exc.NoContent:
                        # desired exception under some circumstances, e.g. labels that already exist
                        if _page is None and 'name' in post_data:
                            results = endpoint.get(all_pages=True).results
                            for item in results:
                                if item['name'] == post_data['name']:
                                    _page = item.get()
                                    break
                            else:
                                raise
                    changed = True
                    if asset['natural_key']['type'] == 'project':
                        # When creating a project, we need to wait for its
                        # first project update to finish so that associated
                        # JTs have valid options for playbook names
                        try:
                            _page.wait_until_completed(timeout=300)
                        except AssertionError:
                            # If the project update times out, try to
                            # carry on in the hopes that it will
                            # finish before it is needed.
                            pass
                else:
                    # If we are an existing project and our scm_tpye is not changing don't try and import the local_path setting
                    if asset['natural_key']['type'] == 'project' and 'local_path' in post_data and _page['scm_type'] == post_data['scm_type']:
                        del post_data['local_path']

                    _page = _page.put(post_data)
                    changed = True
            except (exc.Common, AssertionError) as e:
                identifier = asset.get("name", None) or asset.get("username", None) or asset.get("hostname", None)
                log.error(f'{endpoint} "{identifier}": {e}.')
                self._has_error = True
                log.debug("post_data: %r", post_data)
                continue

            self._cache.set_page(_page)

            # Queue up everything related to be either created or assigned.
            for name, S in asset.get('related', {}).items():
                if not S:
                    continue
                if name == 'roles':
                    indexed_roles = defaultdict(list)
                    for role in S:
                        if 'content_object' not in role:
                            continue
                        indexed_roles[role['content_object']['type']].append(role)
                    self._roles.append((_page, indexed_roles))
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
            self._has_error = True
            log.debug("post_data: %r", {'id': role_page['id']})

    def _assign_membership(self):
        for _page, indexed_roles in self._roles:
            role_endpoint = _page.json['related']['roles']
            for content_type in ('organization', 'team'):
                for role in indexed_roles.get(content_type, []):
                    self._assign_role(role_endpoint, role)

    def _assign_roles(self):
        for _page, indexed_roles in self._roles:
            role_endpoint = _page.json['related']['roles']
            for content_type in set(indexed_roles) - {'organization', 'team'}:
                for role in indexed_roles.get(content_type, []):
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
                        log.error("Could not find matching object in Tower for imported relation, item: %r", item)
                        self._has_error = True
                        continue
                    if rel_page['id'] in existing:
                        continue
                    try:
                        post_data = {'id': rel_page['id']}
                        endpoint.post(post_data)
                        log.error("endpoint: %s, id: %s", endpoint.endpoint, rel_page['id'])
                        self._has_error = True
                    except exc.NoContent:  # desired exception on successful (dis)association
                        pass
                    except exc.Common as e:
                        log.error("Object association failed: %s.", e)
                        self._has_error = True
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

        for resource in self._dependent_resources():
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
