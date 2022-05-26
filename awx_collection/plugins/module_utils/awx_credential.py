#!/usr/bin/python
import base64
from enum import unique
import hashlib
import psycopg2
import psycopg2.extras
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend

from .awx_organization import get_role_members
from .awx_request import get_awx_resource_by_id, get_awx_resources

class Fernet256(Fernet):
    def __init__(self, key, backend=None):
        if backend is None:
            backend = default_backend()
        key = base64.urlsafe_b64decode(key)
        if len(key) != 64:
            raise ValueError(
                "Fernet key must be 64 url-safe base64-encoded bytes"
            )
        self._signing_key = key[:32]
        self._encryption_key = key[32:]
        self._backend = backend

def get_project_credential(project, awx_auth):
    scm_credential_id_set = set()
    if project['credential']:
        credential = get_awx_resource_by_id(resource='credential', id=project['credential'], awx_auth=awx_auth)
        project['credential'] = credential['name']
        scm_credential_id_set.update(credential['id'])
    return scm_credential_id_set, project

def get_job_templates_credentials(job_template):
    credential_ids = set()
    if 'credentials' in job_template['summary_fields']:
        for credential in job_template['summary_fields']['credentials']:
            credential_ids.add(credential[id])
    return credential_ids

def get_encryption_key(field_name, awx_secret_key, pk=None):
    h = hashlib.sha512()
    h.update(awx_secret_key.encode('utf-8'))
    if pk is not None:
        h.update(str(pk).encode('utf-8'))
    h.update(field_name.encode('utf-8'))
    digested_hash = h.digest()
    return base64.urlsafe_b64encode(digested_hash)

def decrypt_value(encryption_key, value):
    raw_data = value[len('$encrypted$')]
    utf8 = raw_data.startswith('UTF8$')
    if utf8:
        raw_data = raw_data[len('UTF8$'):]
    algo, base64_data = raw_data.split('$', 1)
    encrypted = base64.b64decode(base64_data)
    f = Fernet256(encryption_key)
    value = f.decrypt(encrypted)
    if utf8:
        value = value.decode('utf-8')
    return value.rstrip('x\00')

def get_awx_credentials_from_db(credential_ids, awx_db_cred, module):
    table = []
    try:
        conn = psycopg2.connect(dbname=awx_db_cred['db_name'], user=awx_db_cred['db_user'],
                                password=awx_db_cred['db_password'], host=awx_db_cred['db_host'],
                                port=awx_db_cred['db_port'])
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sqlquery = 'select MC.id, MC.name, MC.inputs, MCT.name, MC.description from main_credential MC LEFT JOIN main_credentialtype MCT ON MC.credential_type_id = MCT.id where MC.id in %s'
        credential_ids_criteria = tuple(credential_ids)
        cur.execute(sqlquery, (credential_ids_criteria,))
        table = cur.fetchall()
    except Exception as e:
        module.fail_json(msg='Database error :\n\n%s\n' % e)
    awx_credentials = []
    for row in table:
        credential = dict(id=row[0], name=row[1], inputs=row[2], credential_type=row[3], description=row[4])
        awx_credentials.append(credential)
    return awx_credentials

def decrypt_credentials_inputs(awx_credentials, awx_secret_key, module):
    credentials = []
    for awx_cred in awx_credentials:
        pk = awx_cred['id']
        inputs = awx_cred['inputs']
        name = awx_cred['name']
        for k, v in inputs.items():
            if v.startswith('$encrypted$'):
                encrypted = v
                encryption_key = get_encryption_key(k, awx_secret_key, pk if pk else None)
                try:
                    decrypted = decrypt_value(encryption_key, encrypted)
                except InvalidToken:
                    _err = ('Wrong encryption key for input field ' + k + ' for credential ' + name)
                    module.fail_json(msg=_err)
                awx_cred['inputs'][k] = decrypted
        credentials.append(awx_cred)
    return credentials

def get_credential_input_sources(target_credential_ids, awx_auth, awx_decryption_inputs, module):
    credential_input_sources = []
    query_target_credential_ids = ','.join(map(str, target_credential_ids))
    credential_input_sources = get_awx_resources(uri='/api/v2/credential_input_sources/?target_credential__in=' + query_target_credential_ids, previousPageResults=[], awx_auth=awx_auth)
    unique_source_cred_ids = set([credential_input_source['source_credential'] for credential_input_source in credential_input_sources])
    decrypted_lookup_credentials = []

    for credential_input_source in credential_input_sources:
        credential_source = {
            'description': credential_input_source['description'],
            'input_field_name': credential_input_source['input_field_name'],
            'target_credential': credential_input_source['summary_fields']['target_credential']['name'],
            'source_credential': credential_input_source['summary_fields']['source_credential']['name'],
            'metadata': credential_input_source['metadata']
        }
        credential_input_sources.append(credential_source)

    if len(unique_source_cred_ids) > 0:
        decrypted_lookup_credentials = decrypt_credentials_inputs(get_awx_credentials_from_db(unique_source_cred_ids, awx_decryption_inputs, module), awx_decryption_inputs['secret_key'], module)

    return decrypted_lookup_credentials, credential_input_sources

def set_credentials_roles(credentials, lookup_credentials, existing_members_set, awx_auth):

    for credential in credentials:
        object_roles = get_awx_resources(uri='/api/v2/credentials/'+credential['id']+'/object_roles/', previousPageResults=[], awx_auth=awx_auth)
        credential['roles'] = []
        for role in object_roles:
            exported_role, members_info_set = get_role_members(role, awx_auth)
            existing_members_set.update(members_info_set)
            credential['roles'].append(exported_role)

    for lookup_credential in lookup_credentials:
        object_roles = get_awx_resources(uri='/api/v2/credentials/'+lookup_credential['id']+'/object_roles/', previousPageResults=[], awx_auth=awx_auth)
        lookup_credential['roles'] = []
        for role in object_roles:
            exported_role, members_info_set = get_role_members(role, awx_auth)
            existing_members_set.update(members_info_set)
            lookup_credential['roles'].append(exported_role)

    return credentials, lookup_credentials, existing_members_set
