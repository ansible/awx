from awx.main.utils import decrypt_field
from django.conf import settings


def aws(cred, env):
    env['AWS_ACCESS_KEY_ID'] = cred.username
    env['AWS_SECRET_ACCESS_KEY'] = decrypt_field(cred, 'password')
    if len(cred.security_token) > 0:
        env['AWS_SECURITY_TOKEN'] = decrypt_field(cred, 'security_token')


def gce(cred, env):
    env['GCE_EMAIL'] = cred.username
    env['GCE_PROJECT'] = cred.project


def azure_rm(cred, env):
    if len(cred.client) and len(cred.tenant):
        env['AZURE_CLIENT_ID'] = cred.client
        env['AZURE_SECRET'] = decrypt_field(cred, 'secret')
        env['AZURE_TENANT'] = cred.tenant
        env['AZURE_SUBSCRIPTION_ID'] = cred.subscription
    else:
        env['AZURE_SUBSCRIPTION_ID'] = cred.subscription
        env['AZURE_AD_USER'] = cred.username
        env['AZURE_PASSWORD'] = decrypt_field(cred, 'password')
    if cred.inputs.get('cloud_environment', None):
        env['AZURE_CLOUD_ENVIRONMENT'] = cred.inputs['cloud_environment']


def vmware(cred, env):
    env['VMWARE_USER'] = cred.username
    env['VMWARE_PASSWORD'] = decrypt_field(cred, 'password')
    env['VMWARE_HOST'] = cred.host
    env['VMWARE_VALIDATE_CERTS'] = str(settings.VMWARE_VALIDATE_CERTS)
