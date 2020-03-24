import itertools

from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page
from ..mixins import has_create


EXPORTABLE_RESOURCES = [
    'users',
    'organizations',
    'teams',
    'credential_types',
    'credentials',
    'notification_templates',
    'projects',
    'inventory',
    'job_templates',
    'workflow_job_templates',
]


EXPORTABLE_RELATIONS = [
    'Roles',
    'NotificationTemplates',
    'Labels',
    'SurveySpec',
    'WorkflowJobTemplateNodes',
]


NATURAL_KEYS = {
    'user': ('username',),
    'organization': ('name',),
    'team': ('organization', 'name'),
    'credential_type': ('name', 'kind'),
    'credential': ('organization', 'name', 'credential_type'),
    'notification_template': ('organization', 'name'),
    'project': ('organization', 'name'),
    'inventory': ('organization', 'name'),
    'job_template': ('organization', 'name'),
    'workflow_job_template': ('organization', 'name'),

    # related resources
    'role': ('name', ':content_object'),
    'notification_template': ('organization', 'name'),
    'label': ('organization', 'name'),  # FIXME: label will need to be fully constructed from this
    'workflow_job_template_node': ('workflow_job_template', 'identifier'),
}


def get_natural_key(pg):
    natural_key = {'type': pg['type']}
    lookup = NATURAL_KEYS.get(pg['type'], ())

    for key in lookup or ():
        if key.startswith(':'):
            # treat it like a special-case related object
            related_objs = [
                related for name, related in pg.related.items()
                if name not in ('users', 'teams')
            ]
            if related_objs:
                natural_key[key[1:]] = get_natural_key(related_objs[0].get())
        elif key in pg.related:
            natural_key[key] = get_natural_key(pg.related[key].get())
        elif key in pg:
            natural_key[key] = pg[key]

    if not natural_key:
        return None
    return natural_key


def freeze(key):
    if key is None:
        return None
    return frozenset((k, freeze(v) if isinstance(v, dict) else v) for k, v in key.items())


class Api(base.Base):

    pass


page.register_page(resources.api, Api)


class ApiV2(base.Base):

    # Common import/export methods

    def _get_options(self, endpoint):
        return endpoint.options().json['actions'].get('POST', {})

    # Export methods

    def _serialize_asset(self, asset, options):
        # Drop any (credential_type) assets that are being managed by the Tower instance.
        if asset.json.get('managed_by_tower'):
            return None

        try:
            fields = {
                key: asset[key] for key in options
                if key in asset.json and key not in asset.related
            }
            fields['natural_key'] = get_natural_key(asset)

            fk_fields = {
                key: get_natural_key(asset.related[key].get()) for key in options
                if key in asset.related
            }

            related = {}
            for k, related_endpoint in asset.related.items():
                if not related_endpoint:
                    continue
                if k == 'object_roles':
                    continue
                rel = related_endpoint._create()
                if rel.__class__.__name__ not in EXPORTABLE_RELATIONS:
                    continue
                data = related_endpoint.get(all_pages=True)
                if 'results' in data:
                    related[k] = [get_natural_key(x) for x in data.results]
                else:
                    related[k] = data.json
        except exc.Forbidden:
            return None

        related_fields = {'related': related} if related else {}

        fields.update(fk_fields)
        fields.update(related_fields)
        return fields

    def _get_assets(self, resource, value):
        endpoint = getattr(self, resource)
        if value:
            from awxkit.cli.options import pk_or_name

            pk = pk_or_name(self, resource, value)  # TODO: decide whether to support multiple
            results = endpoint.get(id=pk).results
        else:
            results = endpoint.get(all_pages=True).results

        options = self._get_options(endpoint)
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
        natural_key = freeze(get_natural_key(page))
        # FIXME: we need to keep a reference for the case where we
        # don't have a natural key, so we can delete
        if natural_key is not None:
            if getattr(self, '_natural_key', None) is None:
                self._natural_key = {}

            self._natural_key[natural_key] = page

    def _register_existing_assets(self, resource):
        endpoint = getattr(self, resource)
        options = self._get_options(endpoint)
        if getattr(self, '_options', None) is None:
            self._options = {}
        self._options[resource] = options

        results = endpoint.get(all_pages=True).results
        for pg in results:
            self._register_page(pg)

    def _get_by_natural_key(self, key, fetch=True):
        frozen_key = freeze(key)
        if frozen_key is not None and frozen_key not in self._natural_key and fetch:
            pass  # FIXME

        return self._natural_key.get(frozen_key)

    def _create_assets(self, data, resource):
        if resource not in data or resource not in EXPORTABLE_RESOURCES:
            return

        endpoint = getattr(self, resource)
        options = self._options[resource]
        assets = data[resource]
        for asset in assets:
            post_data = {}
            for field, value in asset.items():
                if field not in options:
                    continue
                if options[field]['type'] == 'id':
                    page = self._get_by_natural_key(value)
                    post_data[field] = page['id'] if page is not None else None
                else:
                    post_data[field] = value

            page = self._get_by_natural_key(asset['natural_key'], fetch=False)
            if page is None:
                if resource == 'users':
                    # We should only impose a default password if the resource doesn't exist.
                    post_data.setdefault('password', 'abc123')
                page = endpoint.post(post_data)
            else:
                page = page.put(post_data)

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
        pass  # FIXME

    def _assign_related_assets(self, resource, assets):
        for asset in assets:
            page = self._get_by_natural_key(asset['natural_key'])
            # FIXME: deal with `page is None` case
            for name, S in asset.get('related', {}).items():
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
