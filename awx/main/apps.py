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

        dab_post_migrate.connect(self._add_member_org_to_child_admins, dispatch_uid='awx-add-member-org-perm')

        self.load_named_url_feature()
        pre_migrate.connect(self.check_db_requirement, sender=self)

    @staticmethod
    def _add_member_org_to_child_admins(sender, **kwargs):
        """Ensure Organization Child Admin roles include member_organization."""
        from ansible_base.rbac.models import RoleDefinition
        from ansible_base.lib.models import DABPermission

        member_perm = DABPermission.objects.filter(codename='member_organization').first()
        if not member_perm:
            return

        child_admin_roles = [
            'Organization Project Admin',
            'Organization Credential Admin',
            'Organization Inventory Admin',
            'Organization NotificationTemplate Admin',
            'Organization WorkflowJobTemplate Admin',
            'Organization ExecutionEnvironment Admin',
        ]
        for rd in RoleDefinition.objects.filter(name__in=child_admin_roles, managed=True):
            rd.permissions.add(member_perm)
