from awxkit.utils import random_title, update_payload, filter_by_class, PseudoNamespace
from awxkit.api.resources import resources
from awxkit.api.pages import Organization
from awxkit.api.mixins import HasCreate, DSAdapter

from . import page
from . import base


class OAuth2Application(HasCreate, base.Base):

    dependencies = [Organization]
    NATURAL_KEY = ('organization', 'name')

    def payload(self, **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'OAuth2Application - {}'.format(random_title()),
            description=kwargs.get('description') or random_title(10),
            client_type=kwargs.get('client_type', 'public'),
            authorization_grant_type=kwargs.get('authorization_grant_type', 'password'),
        )
        if kwargs.get('organization'):
            payload.organization = kwargs['organization'].id

        optional_fields = ('redirect_uris', 'skip_authorization')
        update_payload(payload, optional_fields, kwargs)
        return payload

    def create_payload(self, organization=Organization, **kwargs):
        self.create_and_update_dependencies(*filter_by_class((organization, Organization)))
        organization = self.ds.organization if organization else None
        payload = self.payload(organization=organization, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, organization=Organization, **kwargs):
        payload = self.create_payload(organization=organization, **kwargs)
        return self.update_identity(OAuth2Applications(self.connection).post(payload))


page.register_page((resources.application, (resources.applications, 'post')), OAuth2Application)


class OAuth2Applications(page.PageList, OAuth2Application):
    pass


page.register_page(resources.applications, OAuth2Applications)


class OAuth2AccessToken(HasCreate, base.Base):

    optional_dependencies = [OAuth2Application]

    def payload(self, **kwargs):
        payload = PseudoNamespace(description=kwargs.get('description') or random_title(10), scope=kwargs.get('scope', 'write'))

        if kwargs.get('oauth_2_application'):
            payload.application = kwargs['oauth_2_application'].id

        optional_fields = ('expires',)
        update_payload(payload, optional_fields, kwargs)
        return payload

    def create_payload(self, oauth_2_application=None, **kwargs):
        self.create_and_update_dependencies(*filter_by_class((oauth_2_application, OAuth2Application)))
        oauth_2_application = self.ds.oauth_2_application if oauth_2_application else None
        payload = self.payload(oauth_2_application=oauth_2_application, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, oauth_2_application=None, **kwargs):
        payload = self.create_payload(oauth_2_application=oauth_2_application, **kwargs)
        return self.update_identity(OAuth2AccessTokens(self.connection).post(payload))


page.register_page((resources.token, (resources.tokens, 'post')), OAuth2AccessToken)


class OAuth2AccessTokens(page.PageList, OAuth2AccessToken):
    pass


page.register_page(resources.tokens, OAuth2AccessTokens)
