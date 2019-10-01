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
    def is_demo_license(self):
        return self.license_info.get('demo', False) or \
            self.license_info.get('key_present', False)

    @property
    def is_valid_license(self):
        return self.license_info.get('valid_key', False) and \
            'license_key' in self.license_info and \
            'instance_count' in self.license_info

    @property
    def is_trial_license(self):
        return self.is_valid_license and \
            self.license_info.get('trial', False)

    @property
    def is_awx_license(self):
        return self.license_info.get('license_type', None) == 'open'

    @property
    def is_legacy_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'legacy'

    @property
    def is_basic_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'basic'

    @property
    def is_enterprise_license(self):
        return self.is_valid_license and \
            self.license_info.get('license_type', None) == 'enterprise'

    @property
    def features(self):
        """returns a list of enabled license features"""
        return [k for k, v in self.license_info.get('features', {}).items() if v]


page.register_page(resources.config, Config)
