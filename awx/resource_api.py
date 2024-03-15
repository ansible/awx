from ansible_base.resource_registry.registry import ParentResource, ResourceConfig, ServiceAPIConfig, SharedResource
from ansible_base.resource_registry.shared_types import OrganizationType, TeamType, UserType

from awx.main import models


class APIConfig(ServiceAPIConfig):
    service_type = "awx"


RESOURCE_LIST = (
    ResourceConfig(
        models.Organization,
        shared_resource=SharedResource(serializer=OrganizationType, is_provider=False),
    ),
    ResourceConfig(models.User, shared_resource=SharedResource(serializer=UserType, is_provider=False), name_field="username"),
    ResourceConfig(
        models.Team,
        shared_resource=SharedResource(serializer=TeamType, is_provider=False),
        parent_resources=[ParentResource(model=models.Organization, field_name="organization")],
    ),
)
