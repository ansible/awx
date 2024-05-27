from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
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

    def ready(self):
        super().ready()

        self.load_named_url_feature()
