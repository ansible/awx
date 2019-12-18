from django.apps import AppConfig
from django.db.models.signals import pre_migrate
from django.utils.translation import ugettext_lazy as _


def raise_migration_flag(**kwargs):
    from awx.main.tasks import set_migration_flag
    set_migration_flag.delay()


class MainConfig(AppConfig):

    name = 'awx.main'
    verbose_name = _('Main')

    def ready(self):
        pre_migrate.connect(raise_migration_flag, sender=self)
