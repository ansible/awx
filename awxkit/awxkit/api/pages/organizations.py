from awxkit.api.mixins import HasCreate, HasInstanceGroups, HasNotifications, DSAdapter
from awxkit.utils import random_title, suppress, PseudoNamespace
from awxkit.api.resources import resources
import awxkit.exceptions as exc
from . import base
from . import page


class Organization(HasCreate, HasInstanceGroups, HasNotifications, base.Base):

    NATURAL_KEY = ('name',)

    def add_admin(self, user):
        if isinstance(user, page.Page):
            user = user.json
        with suppress(exc.NoContent):
            self.related.admins.post(user)

    def add_user(self, user):
        if isinstance(user, page.Page):
            user = user.json
        with suppress(exc.NoContent):
            self.related.users.post(user)

    def payload(self, **kwargs):
        payload = PseudoNamespace(name=kwargs.get('name') or 'Organization - {}'.format(random_title()),
                                  description=kwargs.get('description') or random_title(10))
        return payload

    def create_payload(self, name='', description='', **kwargs):
        payload = self.payload(name=name, description=description, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', **kwargs):
        payload = self.create_payload(name=name, description=description, **kwargs)
        return self.update_identity(Organizations(self.connection).post(payload))


page.register_page([resources.organization,
                    (resources.organizations, 'post')], Organization)


class Organizations(page.PageList, Organization):

    pass


page.register_page([resources.organizations,
                    resources.user_organizations,
                    resources.project_organizations], Organizations)
