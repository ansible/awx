import json
import os
import stat
import tempfile

from django.conf import settings


def aws(cred, env, private_data_dir):
    env['AWS_ACCESS_KEY_ID'] = cred.get_input('username', default='')
    env['AWS_SECRET_ACCESS_KEY'] = cred.get_input('password', default='')

    if cred.has_input('security_token'):
        env['AWS_SECURITY_TOKEN'] = cred.get_input('security_token', default='')


def gce(cred, env, private_data_dir):
    project = cred.get_input('project', default='')
    username = cred.get_input('username', default='')

    env['GCE_EMAIL'] = username
    env['GCE_PROJECT'] = project
    json_cred = {
        'type': 'service_account',
        'private_key': cred.get_input('ssh_key_data', default=''),
        'client_email': username,
        'project_id': project,
        # need token uri for inventory plugins
        # should this really be hard coded? Good question.
        'token_uri': 'https://accounts.google.com/o/oauth2/token',
    }

    handle, path = tempfile.mkstemp(dir=private_data_dir)
    f = os.fdopen(handle, 'w')
    json.dump(json_cred, f, indent=2)
    f.close()
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    env['GCE_CREDENTIALS_FILE_PATH'] = path
    return path


def azure_rm(cred, env, private_data_dir):
    client = cred.get_input('client', default='')
    tenant = cred.get_input('tenant', default='')

    env['AZURE_SUBSCRIPTION_ID'] = cred.get_input('subscription', default='')

    if len(client) and len(tenant):
        env['AZURE_CLIENT_ID'] = client
        env['AZURE_TENANT'] = tenant
        env['AZURE_SECRET'] = cred.get_input('secret', default='')
    else:
        env['AZURE_AD_USER'] = cred.get_input('username', default='')
        env['AZURE_PASSWORD'] = cred.get_input('password', default='')

    if cred.has_input('cloud_environment'):
        env['AZURE_CLOUD_ENVIRONMENT'] = cred.get_input('cloud_environment')


def vmware(cred, env, private_data_dir):
    env['VMWARE_USER'] = cred.get_input('username', default='')
    env['VMWARE_PASSWORD'] = cred.get_input('password', default='')
    env['VMWARE_HOST'] = cred.get_input('host', default='')
    env['VMWARE_VALIDATE_CERTS'] = str(settings.VMWARE_VALIDATE_CERTS)
