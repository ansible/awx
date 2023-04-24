import functools

from awxkit import api
from awxkit.exceptions import NoContent


class AssociationParser(object):
    action = 'associate'

    def __init__(self, page, options_json, resource):
        self.page = page
        self.targets = {}
        for related_key, plural_name in options_json.get('related_associations', {}):
            self.targets[related_key] = plural_name
        self.resource = resource

    def add_arguments(self, parser, resource_options_parser):
        from .options import pk_or_name

        parser.choices[self.action].add_argument(
            'id',
            type=functools.partial(pk_or_name, None, self.resource, page=self.page),
            help=f'Primary object for the association, obtained from {self.resource} endpoint',
        )
        group = parser.choices[self.action].add_mutually_exclusive_group(required=True)
        for param, endpoint in self.targets.items():

            class related_page(object):
                def __init__(self, connection, resource):
                    self.conn = connection
                    self.resource = resource

                def get(self, **kwargs):
                    v2 = api.Api(connection=self.conn).get().current_version.get()
                    return getattr(v2, self.resource).get(**kwargs)

            group.add_argument(
                f'--{param}',
                metavar='',
                type=functools.partial(pk_or_name, None, param, page=related_page(self.page.connection, endpoint)),
                help=f'The ID (or name) of the {param} to {self.action}',
            )

    def perform(self, **kwargs):
        for k, v in kwargs.items():
            related_endpoint = self.page.endpoint + k + '/'  # there is probably a more awxkit-y way of doing this
            try:
                self.page.connection.post(related_endpoint, {'id': v, self.action: True})
            except NoContent:
                # we expect to enter this block because these endpoints return
                # HTTP 204 on success
                pass
            r = self.page.connection.get(related_endpoint)
            # import pdb; pdb.set_trace()
            return self.page.get().page_identity(r)
            # return self.page.get().related[endpoint].get()
