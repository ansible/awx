from awxkit.api.resources import resources
from . import base
from . import page


EXPORTABLE_RESOURCES = [
    'users',
    'organizations',
    'teams',
    'credential_types',
    'credentials',
    'notification_templates',
    # 'projects',
    # 'inventory',
    # 'job_templates',
    # 'workflow_job_templates',
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
}


def get_natural_key(page):
    natural_key = {'type': page['type']}
    lookup = NATURAL_KEYS.get(page['type'], ())

    for key in lookup or ():
        if key.startswith(':'):
            # treat it like a special-case related object
            related_objs = [
                related for name, related in page.related.items()
                if name not in ('users', 'teams')
            ]
            if related_objs:
                natural_key[key[1:]] = get_natural_key(related_objs[0].get())
        elif key in page.related:
            natural_key[key] = get_natural_key(page.related[key].get())
        elif key in page:
            natural_key[key] = page[key]

    if not natural_key:
        return None
    return natural_key


class Api(base.Base):

    pass


page.register_page(resources.api, Api)


class ApiV2(base.Base):

    def _get_options(self, endpoint):
        return endpoint.options().json['actions']['POST']

    def _serialize_asset(self, asset, options):
        # Drop any (credential_type) assets that are being managed by the Tower instance.
        if asset.json.get('managed_by_tower'):
            return None

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
            if k != 'roles':
                continue
            data = related_endpoint.get(all_pages=True)
            if 'results' in data:
                related[k] = [get_natural_key(x) for x in data.results]

        related_fields = {'related': related} if related else {}

        fields.update(fk_fields)
        fields.update(related_fields)
        return fields

    def _get_assets(self, resource, value):
        endpoint = getattr(self, resource)
        if value:
            from awxkit.cli.options import pk_or_name

            pk = pk_or_name(self, resource, value)
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

    def import_assets(self):
        pass


page.register_page(resources.v2, ApiV2)
