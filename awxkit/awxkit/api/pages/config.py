from awxkit.api.resources import resources
from . import base
from . import page


class Config(base.Base):

    @property
    def is_aws_license(self):
        return self.license_info.get('is_aws', False) or \
            'ami-id' in self.license_info or \
            'instance-id' in self.license_info

    @property
    def is_valid_license(self):
        return self.license_info.get('valid_key', False) and \
            'instance_count' in self.license_info

    @property
    def is_trial_license(self):
        return self.is_valid_license and \
            self.license_info.get('trial', False)

    @property
    def is_awx_license(self):
        return self.license_info.get('license_type', None) == 'open'

    @property
    def is_enterprise_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'enterprise'

    @property
    def features(self):
        """returns a list of enabled license features"""
        return [k for k, v in self.license_info.get('features', {}).items() if v]


class ConfigAttach(page.Page):

    def attach(self, **kwargs):
        return self.post(json=kwargs).json


page.register_page(resources.config, Config)
page.register_page(resources.config_attach, ConfigAttach)
