import json
import os
import stat
import tempfile

from awx.main.utils import decrypt_field
from django.conf import settings


def aws(cred, env, private_data_dir):
    env['AWS_ACCESS_KEY_ID'] = cred.username
    env['AWS_SECRET_ACCESS_KEY'] = decrypt_field(cred, 'password')
    if len(cred.security_token) > 0:
        env['AWS_SECURITY_TOKEN'] = decrypt_field(cred, 'security_token')


def gce(cred, env, private_data_dir):
    env['GCE_EMAIL'] = cred.username
    env['GCE_PROJECT'] = cred.project
    json_cred = {
        'type': 'service_account',
        'private_key': decrypt_field(cred, 'ssh_key_data'),
        'client_email': cred.username,
        'project_id': cred.project
    }
    handle, path = tempfile.mkstemp(dir=private_data_dir)
    f = os.fdopen(handle, 'w')
    json.dump(json_cred, f)
    f.close()
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    env['GCE_CREDENTIALS_FILE_PATH'] = path


def azure_rm(cred, env, private_data_dir):
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


def vmware(cred, env, private_data_dir):
    env['VMWARE_USER'] = cred.username
    env['VMWARE_PASSWORD'] = decrypt_field(cred, 'password')
    env['VMWARE_HOST'] = cred.host
    env['VMWARE_VALIDATE_CERTS'] = str(settings.VMWARE_VALIDATE_CERTS)
