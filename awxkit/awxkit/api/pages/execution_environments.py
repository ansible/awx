import logging

from awxkit.api.mixins import HasCreate
from awxkit.api.pages import (
    Credential,
    Organization,
)
from awxkit.api.resources import resources

from . import base
from . import page


log = logging.getLogger(__name__)


class ExecutionEnvironment(HasCreate, base.Base):

    dependencies = [Organization, Credential]
    NATURAL_KEY = ('organization', 'image')


page.register_page([resources.execution_environment,
                    (resources.execution_environments, 'post'),
                    (resources.organization_execution_environments, 'post')], ExecutionEnvironment)


class ExecutionEnvironments(page.PageList, ExecutionEnvironment):
    pass


page.register_page([resources.execution_environments,
                    resources.organization_execution_environments], ExecutionEnvironments)
