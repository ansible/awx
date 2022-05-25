#!/usr/bin/python
from .awx_request import get_awx_resource_by_id

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
