from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.utils import random_title, PseudoNamespace
from awxkit.api.resources import resources
from awxkit.config import config

from . import base
from . import page


class User(HasCreate, base.Base):
    NATURAL_KEY = ('username',)

    def payload(self, **kwargs):
        payload = PseudoNamespace(
            username=kwargs.get('username') or 'User-{}'.format(random_title(non_ascii=False)),
            password=kwargs.get('password') or config.credentials.default.password,
            is_superuser=kwargs.get('is_superuser', False),
            is_system_auditor=kwargs.get('is_system_auditor', False),
            first_name=kwargs.get('first_name', random_title()),
            last_name=kwargs.get('last_name', random_title()),
            email=kwargs.get('email', '{}@example.com'.format(random_title(5, non_ascii=False))),
        )
        return payload

    def create_payload(self, username='', password='', **kwargs):
        payload = self.payload(username=username, password=password, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, username='', password='', organization=None, **kwargs):
        payload = self.create_payload(username=username, password=password, **kwargs)
        self.password = payload.password

        ctrl_users_api = Users(self.connection)
        # Check if API base path is set to controller, then use gateway endpoint
        if config.get("api_base_path") == "/api/controller/":
            # Use gateway endpoint for user creation
            gw_users_api = Users(self.connection)
            gw_users_api.endpoint = "/api/gateway/v1/users/"
            # Cleanup controller attributes
            payload["is_platform_auditor"] = payload.get("is_system_auditor")
            payload.pop("is_system_auditor")
            # Create gw user
            gw_user = gw_users_api.post(payload)
            user = ctrl_users_api.get(username=gw_user.username).results.pop()
            user.json["password"] = payload.password
            self.update_identity(user)
        else:
            # Use default endpoint
            self.update_identity(ctrl_users_api.post(payload))

        if organization:
            organization.add_user(self)

        return self


page.register_page([resources.user, (resources.users, 'post')], User)


class Users(page.PageList, User):
    pass


page.register_page(
    [resources.users, resources.organization_admins, resources.related_users, resources.credential_owner_users, resources.user_admin_organizations], Users
)


class Me(Users):
    pass


page.register_page(resources.me, Me)
