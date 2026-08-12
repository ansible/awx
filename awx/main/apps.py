from dispatcherd.config import setup as dispatcher_setup

from django.apps import AppConfig
from django.db import connection
from django.utils.translation import gettext_lazy as _
from django.core.management.base import CommandError
from django.db.models.signals import pre_migrate

from awx.main.utils.named_url_graph import _customize_graph, generate_graph
from awx.main.utils.db import db_requirement_violations
from awx.conf import register, fields


class MainConfig(AppConfig):
    name = 'awx.main'
    verbose_name = _('Main')

    def check_db_requirement(self, *args, **kwargs):
        violations = db_requirement_violations()
        if violations:
            raise CommandError(violations)

    def load_named_url_feature(self):
        models = [m for m in self.get_models() if hasattr(m, 'get_absolute_url')]
        generate_graph(models)
        _customize_graph()
        register(
            'NAMED_URL_FORMATS',
            field_class=fields.DictField,
            read_only=True,
            label=_('Formats of all available named urls'),
            help_text=_('Read-only list of key-value pairs that shows the standard format of all available named URLs.'),
            category=_('Named URL'),
            category_slug='named-url',
        )
        register(
            'NAMED_URL_GRAPH_NODES',
            field_class=fields.DictField,
            read_only=True,
            label=_('List of all named url graph nodes.'),
            help_text=_(
                'Read-only list of key-value pairs that exposes named URL graph topology.'
                ' Use this list to programmatically generate named URLs for resources'
            ),
            category=_('Named URL'),
            category_slug='named-url',
        )

    def configure_dispatcherd(self):
        """This implements the default configuration for dispatcherd

        If running the tasking service like awx-manage dispatcherd,
        some additional config will be applied on top of this.
        This configuration provides the minimum such that code can submit
        tasks to pg_notify to run those tasks.
        """
        from awx.main.dispatch.config import get_dispatcherd_config

        if connection.vendor != 'postgresql':
            config_dict = get_dispatcherd_config(mock_publish=True)
        else:
            config_dict = get_dispatcherd_config()

        dispatcher_setup(config_dict)

    def ready(self):
        super().ready()

        self.configure_dispatcherd()

        from ansible_base.rbac.triggers import dab_post_migrate

        dab_post_migrate.connect(self._sync_managed_role_definitions, dispatch_uid='awx-sync-managed-role-definitions')

        self.load_named_url_feature()
        pre_migrate.connect(self.check_db_requirement, sender=self)

    @staticmethod
    def _sync_managed_role_definitions(sender, **kwargs):
        from django.apps import apps as global_apps

        from ansible_base.resource_registry.signals.handlers import no_reverse_sync

        # NOTE: setup_managed_role_definitions lives in the migrations module because
        # it is also called from migration 0192. Ideally this would be extracted to a
        # shared non-migration module, but doing so requires updating the migration
        # import, which is a broader refactor (see also models/rbac.py imports).
        from awx.main.migrations._dab_rbac import setup_managed_role_definitions

        # During post-migrate the resource server (gateway) may not be ready
        # (e.g. migrate_service_data still holds a 423 lock).  Disable reverse
        # sync for this call — gateway reconciles via migrate_service_data.
        with no_reverse_sync():
            setup_managed_role_definitions(global_apps, None)
