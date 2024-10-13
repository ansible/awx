import functools
import logging

from awxkit import api
from awxkit.exceptions import NoContent


log = logging.getLogger(__name__)


# These were custom commands before the refactor to work via OPTIONS
# and custom commands have custom names, which we add for backward compat
OLD_ALIASES = {
    'notification_templates_started': 'start_notification',
    'notification_templates_error': 'error_notification',
    'notification_templates_success': 'success_notificaton',
    'notification_templates_approvals': 'approval_notification',
}


class AssociationParser(object):
    action = 'associate'

    def __init__(self, page, resource):
        self.page = page
        self.resource = resource

    def add_arguments(self, parser, related_associations):
        from .options import pk_or_name

        parser.choices[self.action].add_argument(
            'id',
            type=functools.partial(pk_or_name, None, self.resource, page=self.page),
            help=f'Primary object for the association, obtained from {self.resource} endpoint',
        )
        group = parser.choices[self.action].add_mutually_exclusive_group(required=True)
        for related_name, endpoint in related_associations:

            class related_page(object):
                def __init__(self, connection, resource):
                    self.conn = connection
                    self.resource = resource

                def get(self, **kwargs):
                    v2 = api.Api(connection=self.conn).get().current_version.get()
                    return getattr(v2, self.resource).get(**kwargs)

            arg_names = [f'--{related_name}']
            if related_name.endswith('s'):
                arg_names.append(f'--{related_name[:-1]}')
            if related_name in OLD_ALIASES:
                arg_names.append(f'--{OLD_ALIASES[related_name]}')

            group.add_argument(
                *arg_names,
                metavar='',
                type=functools.partial(pk_or_name, None, related_name, page=related_page(self.page.connection, endpoint)),
                help=f'The ID (or name) of the {related_name} to {self.action}',
            )

    def perform(self, **kwargs):
        for related_name, related_id in kwargs.items():
            self.page = self.page.get()
            related_page = getattr(self.page.related, related_name)
            try:
                payload = {'id': related_id, self.action: True}
                related_page.post(payload)
            except NoContent:
                # we expect to enter this block because these endpoints return
                # HTTP 204 on success
                log.debug(f'Related {related_name} id={related_id} is successfully {self.action}d with resource at url {self.page.endpoint}')
            return getattr(self.page.related, related_name).get()


class DisAssociationParser(AssociationParser):
    action = 'disassociate'
