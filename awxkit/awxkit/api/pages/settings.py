from awxkit.api.resources import resources
from . import base
from . import page


class Setting(base.Base):
    pass


page.register_page(
    [
        resources.setting,
        resources.settings_all,
        resources.settings_authentication,
        resources.settings_changed,
        resources.settings_github,
        resources.settings_github_org,
        resources.settings_github_team,
        resources.settings_google_oauth2,
        resources.settings_jobs,
        resources.settings_ldap,
        resources.settings_radius,
        resources.settings_saml,
        resources.settings_system,
        resources.settings_tacacsplus,
        resources.settings_ui,
        resources.settings_user,
        resources.settings_user_defaults,
    ],
    Setting,
)


class Settings(page.PageList, Setting):
    def get_endpoint(self, endpoint):
        """Helper method used to navigate to a specific settings endpoint.
        (Pdb) settings_pg.get_endpoint('all')
        """
        base_url = '{0}{1}/'.format(self.endpoint, endpoint)
        return self.walk(base_url)

    get_setting = get_endpoint


page.register_page(resources.settings, Settings)
