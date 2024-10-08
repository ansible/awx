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


class RoleTeamAssignment(base.Base):
    NATURAL_KEY = ('team', 'content_object', 'role_definition')


page.register_page(
    [resources.role_team_assignment, (resources.role_definition_team_assignments, 'post'), (resources.role_team_assignments, 'post')], RoleTeamAssignment
)


class RoleUserAssignment(base.Base):
    NATURAL_KEY = ('user', 'content_object', 'role_definition')


page.register_page(
    [resources.role_user_assignment, (resources.role_definition_user_assignments, 'post'), (resources.role_user_assignments, 'post')], RoleUserAssignment
)


class RoleTeamAssignments(page.PageList, RoleTeamAssignment):
    pass


page.register_page([resources.role_definition_team_assignments, resources.role_team_assignments], RoleTeamAssignments)


class RoleUserAssignments(page.PageList, RoleUserAssignment):
    pass


page.register_page([resources.role_definition_user_assignments, resources.role_user_assignments], RoleUserAssignments)
