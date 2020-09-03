from awxkit.api.mixins import HasCreate, DSAdapter
from awxkit.utils import suppress, random_title, PseudoNamespace
from awxkit.api.resources import resources
from awxkit.api.pages import Organization
from awxkit.exceptions import NoContent

from . import base
from . import page


class Team(HasCreate, base.Base):

    dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def add_user(self, user):
        if isinstance(user, page.Page):
            user = user.json
        with suppress(NoContent):
            self.related.users.post(user)

    def payload(self, organization, **kwargs):
        payload = PseudoNamespace(name=kwargs.get('name') or 'Team - {}'.format(random_title()),
                                  description=kwargs.get('description') or random_title(10),
                                  organization=organization.id)
        return payload

    def create_payload(self, name='', description='', organization=Organization, **kwargs):
        self.create_and_update_dependencies(organization)
        payload = self.payload(organization=self.ds.organization, name=name, description=description, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, name='', description='', organization=Organization, **kwargs):
        payload = self.create_payload(name=name, description=description, organization=organization, **kwargs)
        return self.update_identity(Teams(self.connection).post(payload))


page.register_page([resources.team,
                    (resources.teams, 'post')], Team)


class Teams(page.PageList, Team):

    pass


page.register_page([resources.teams,
                    resources.credential_owner_teams,
                    resources.related_teams], Teams)
