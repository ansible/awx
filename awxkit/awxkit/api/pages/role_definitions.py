import logging

# from awxkit.api.mixins import DSAdapter, HasCreate, HasCopy
# from awxkit.api.pages import (
#     Credential,
#     Organization,
# )
from awxkit.api.resources import resources

# from awxkit.utils import random_title, PseudoNamespace, filter_by_class

from . import base
from . import page


log = logging.getLogger(__name__)


class RoleDefinition(base.Base):
    NATURAL_KEY = ('name',)


page.register_page([resources.role_definition, (resources.role_definitions, 'post')], RoleDefinition)


class RoleDefinitions(page.PageList, RoleDefinition):
    pass


page.register_page([resources.role_definitions], RoleDefinitions)
