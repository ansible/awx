import os

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from awx.main.utils.common import bypass_in_test
from awx.main.utils.migration import is_database_synchronized
from awx.main.utils.named_url_graph import _customize_graph, generate_graph
from awx.conf import register, fields


class MainConfig(AppConfig):
    name = 'awx.main'
    verbose_name = _('Main')

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

    def _load_credential_types_feature(self):
        """
        Create CredentialType records for any discovered credentials.

        Note that Django docs advise _against_ interacting with the database using
        the ORM models in the ready() path. Specifically, during testing.
        However, we explicitly use the @bypass_in_test decorator to avoid calling this
        method during testing.

        Django also advises against running pattern because it runs everywhere i.e.
        every management command. We use an advisory lock to ensure correctness and
        we will deal performance if it becomes an issue.
        """
        from awx.main.models.credential import CredentialType

        if is_database_synchronized():
            CredentialType.setup_tower_managed_defaults(app_config=self)

    @bypass_in_test
    def load_credential_types_feature(self):
        return self._load_credential_types_feature()

    def ready(self):
        super().ready()

        """
        Credential loading triggers database operations. There are cases we want to call
        awx-manage collectstatic without a database. All management commands invoke the ready() code
        path. Using settings.AWX_SKIP_CREDENTIAL_TYPES_DISCOVER _could_ invoke a database operation.
        """
        if not os.environ.get('AWX_SKIP_CREDENTIAL_TYPES_DISCOVER', None):
            self.load_credential_types_feature()
        self.load_named_url_feature()
