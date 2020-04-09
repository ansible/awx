import itertools
import logging
import re

from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page
from ..mixins import has_create

descRE = re.compile(r'^[*] `(\w+)`: [^(]*\((\w+), ([^)]+)\)')

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
]


EXPORTABLE_DEPENDENT_OBJECTS = [
    'Labels',
    'SurveySpec',
    'Schedules',
    # WFJT Nodes are a special case, we want full data for the create
    # view and natural keys for the attach views.
    'WorkflowJobTemplateNodes',
]


def freeze(key):
    if key is None:
        return None
    return frozenset((k, freeze(v) if isinstance(v, dict) else v) for k, v in key.items())


class Api(base.Base):

    pass


page.register_page(resources.api, Api)


def parse_description(desc):
    options = {}
    for line in desc[desc.index('POST'):].splitlines():
        match = descRE.match(line)
        if not match:
            continue
        options[match.group(1)] = {'type': match.group(2),
                                   'required': match.group(3) == 'required'}
    return options


def remove_encrypted(value):
    if value == '$encrypted$':
        return ''
    if isinstance(value, list):
        return [remove_encrypted(item) for item in value]
    if isinstance(value, dict):
        return {k: remove_encrypted(v) for k, v in value.items()}
    return value


class ApiV2(base.Base):

    # Common import/export methods

    def _get_options(self, _page):
        if getattr(self, '_options', None) is None:
            self._options = {}

        if isinstance(_page, page.TentativePage):
            url = str(_page)
        else:
            url = _page.url

        if url in self._options:
            return self._options[url]

        options = _page.options()
        warning = options.r.headers.get('Warning', '')
        if '299' in warning and 'deprecated' in warning:
            return self._options.setdefault(url, None)
        if 'POST' not in options.r.headers.get('Allow', ''):
            return self._options.setdefault(url, None)

        if 'POST' in options.json['actions']:
            return self._options.setdefault(url, options.json['actions']['POST'])
        else:
            return self._options.setdefault(url, parse_description(options.json['description']))

    # Export methods

    def _serialize_asset(self, asset, options):
        # Drop any (credential_type) assets that are being managed by the Tower instance.
        if asset.json.get('managed_by_tower'):
            return None
        if options is None:  # Deprecated endpoint or insufficient permissions
            return None

        # Note: doing asset[key] automatically parses json blob strings, which can be a problem.
        fields = {
            key: asset.json[key] for key in options
            if key in asset.json and key not in asset.related and key != 'id'
        }

        for key in options:
            if key not in asset.related:
                continue
            try:
                # FIXME: use caching by url
                natural_key = asset.related[key].get().get_natural_key()
            except exc.Forbidden:
                log.warning("This foreign key cannot be read: %s", asset.related[key])
                return None
            if natural_key is None:
                return None  # This is an unresolvable foreign key
            fields[key] = natural_key

        related = {}
        for key, related_endpoint in asset.related.items():
            if key in options or not related_endpoint:
                continue

            rel = related_endpoint._create()
            related_options = self._get_options(related_endpoint)
            if related_options is None:  # This is a read-only endpoint.
                continue
            is_attach = 'id' in related_options  # This is not a create-only endpoint.

            if rel.__class__.__name__ in EXPORTABLE_RELATIONS and is_attach:
                by_natural_key = True
            elif rel.__class__.__name__ in EXPORTABLE_DEPENDENT_OBJECTS:
                by_natural_key = False
            else:
                continue

            try:
                # FIXME: use caching by url
                data = rel.get(all_pages=True)
            except exc.Forbidden:
                log.warning("These related objects cannot be read: %s", related_endpoint)
                continue

            if 'results' in data:
                results = (
                    x.get_natural_key() if by_natural_key else self._serialize_asset(x, related_options)
                    for x in data.results
                )
                related[key] = [x for x in results if x is not None]
            else:
                related[key] = data.json

        if related:
            fields['related'] = related

        natural_key = asset.get_natural_key()
        if natural_key is None:
            return None
        fields['natural_key'] = natural_key

        return remove_encrypted(fields)

    def _get_assets(self, resource, value):
        endpoint = getattr(self, resource)
        options = self._get_options(endpoint)
        if options is None:
            return None

        if value:
            from awxkit.cli.options import pk_or_name

            pk = pk_or_name(self, resource, value)  # TODO: decide whether to support multiple
            results = endpoint.get(id=pk).results
        else:
            results = endpoint.get(all_pages=True).results

        assets = (self._serialize_asset(asset, options) for asset in results)
        return [asset for asset in assets if asset is not None]

    def export_assets(self, **kwargs):
        # If no resource kwargs are explicitly used, export everything.
        all_resources = all(kwargs.get(resource) is None for resource in EXPORTABLE_RESOURCES)

        data = {}
        for resource in EXPORTABLE_RESOURCES:
            value = kwargs.get(resource)
            if all_resources or value is not None:
                data[resource] = self._get_assets(resource, value)

        return data

    # Import methods

    def _dependent_resources(self, data):
        page_resource = {getattr(self, resource)._create().__item_class__: resource
                         for resource in self.json}
        data_pages = [getattr(self, resource)._create().__item_class__ for resource in data]

        for page_cls in itertools.chain(*has_create.page_creation_order(*data_pages)):
            yield page_resource[page_cls]

    def _register_page(self, page):
        natural_key = freeze(page.get_natural_key())
        # FIXME: we need to keep a reference for the case where we
        # don't have a natural key, so we can delete
        if natural_key is not None:
            if getattr(self, '_natural_key', None) is None:
                self._natural_key = {}

            self._natural_key[natural_key] = page

    def _register_existing_assets(self, resource):
        endpoint = getattr(self, resource)
        options = self._get_options(endpoint)
        if options is None:
            return

        results = endpoint.get(all_pages=True).results
        for pg in results:
            self._register_page(pg)

    def _get_by_natural_key(self, key, fetch=True):
        frozen_key = freeze(key)
        if frozen_key is not None and frozen_key not in self._natural_key and fetch:
            pass  # FIXME

        from awxkit.api.pages import projects

        _page = self._natural_key.get(frozen_key)
        if isinstance(_page, projects.Project) and not _page.is_completed:
            _page.wait_until_completed()
            _page = _page.get()
            self._natural_key[frozen_key] = _page
        return _page

    def _create_assets(self, data, resource):
        if resource not in data or resource not in EXPORTABLE_RESOURCES:
            return

        endpoint = getattr(self, resource)
        options = self._get_options(endpoint)
        assets = data[resource]
        for asset in assets:
            post_data = {}
            for field, value in asset.items():
                if field not in options:
                    continue
                if options[field]['type'] in ('id', 'integer') and isinstance(value, dict):
                    page = self._get_by_natural_key(value)
                    post_data[field] = page['id'] if page is not None else None
                else:
                    post_data[field] = value

            page = self._get_by_natural_key(asset['natural_key'], fetch=False)
            try:
                if page is None:
                    if resource == 'users':
                        # We should only impose a default password if the resource doesn't exist.
                        post_data.setdefault('password', 'abc123')
                    page = endpoint.post(post_data)
                else:
                    page = page.put(post_data)
            except exc.Common:
                log.exception("post_data: %r", post_data)
                raise

            self._register_page(page)

    def _assign_roles(self, page, roles):
        role_endpoint = page.json['related']['roles']
        for role in roles:
            if 'content_object' not in role:
                continue  # admin role
            obj_page = self._get_by_natural_key(role['content_object'])
            if obj_page is not None:
                role_page = obj_page.get_object_role(role['name'], by_name=True)
                try:
                    role_endpoint.post({'id': role_page['id']})
                except exc.NoContent:  # desired exception on successful (dis)association
                    pass
            else:
                pass  # admin role

    def _assign_related(self, page, name, related_set):
        endpoint = page.related[name]
        if isinstance(related_set, dict):  # Relateds that are just json blobs, e.g. survey_spec
            endpoint.post(related_set)
            return

        if 'natural_key' not in related_set[0]:  # It is an attach set
            for item in related_set:
                rel_page = self._get_by_natural_key(item)
                if rel_page is None:
                    continue  # FIXME
                endpoint.post({'id': rel_page['id']})
        else:  # It is a create set
            for item in related_set:
                data = {key: value for key, value in item.items()
                        if key not in ('natural_key', 'related')}
                endpoint.post(data)
                # FIXME: deal with objects that themselves have relateds, e.g. WFJT Nodes

        # FIXME: deal with pruning existing relations that do not match the import set

    def _assign_related_assets(self, resource, assets):
        for asset in assets:
            page = self._get_by_natural_key(asset['natural_key'])
            # FIXME: deal with `page is None` case
            for name, S in asset.get('related', {}).items():
                if not S:
                    continue
                if name == 'roles':
                    self._assign_roles(page, S)
                else:
                    self._assign_related(page, name, S)

    def import_assets(self, data):
        for resource in self._dependent_resources(data):
            self._register_existing_assets(resource)
            self._create_assets(data, resource)
            # FIXME: should we delete existing unpatched assets?

        for resource, assets in data.items():
            self._assign_related_assets(resource, assets)


page.register_page(resources.v2, ApiV2)
