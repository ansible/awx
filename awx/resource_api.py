from ansible_base.resource_registry.registry import ParentResource, ResourceConfig, ServiceAPIConfig, SharedResource
from ansible_base.resource_registry.shared_types import OrganizationType, TeamType, UserType

from awx.main import models

from ansible_base.resource_registry.utils.resource_type_processor import ResourceTypeProcessor


class UserMapper:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class AwxUserProcessor(ResourceTypeProcessor):
    def pre_serialize_additional(self):

        # TODO: is there a better way to do this?
        user = UserMapper(
            username=self.instance.username,
            email=self.instance.email,
            first_name=self.instance.first_name,
            last_name=self.instance.last_name,
            is_superuser=self.instance.is_superuser,
            external_auth_provider=None,
            external_auth_uid=None,
            organizations=models.Organization.objects.filter(member_role__members=self.instance),
            teams=models.Team.objects.filter(member_role__members=self.instance),
            organizations_administered=models.Organization.objects.filter(admin_role__members=self.instance),
            teams_administered=models.Team.objects.filter(admin_role__members=self.instance),
        )

        return user


class APIConfig(ServiceAPIConfig):
    custom_resource_processors = {"shared.user": AwxUserProcessor}

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
