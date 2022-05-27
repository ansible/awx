
import requests

from .awx_organization import get_resource_access_list

from .awx_notification import get_notifications_by_unified_job_template
from .export_tools import parse_extra_vars_to_json
from .awx_credential import get_job_templates_credentials
from .awx_request import get_awx_resources
from .awx_schedule import get_schedules


def get_job_templates_by_projects(project_ids, credential_ids, notification_templates, existing_members_set, awx_auth):
    exported_job_templates = []
    query_project_ids = ','.join(map(str, project_ids))
    job_templates = get_awx_resources(uri='/api/v2/job_templates?project__in=' + query_project_ids, previousPageResults=[], awx_auth=awx_auth)

    for job_template in job_templates:
        credential_ids.update(get_job_templates_credentials(job_template))
        job_template['survey_spec'] = requests.get(url='https://'+awx_auth['host']+'/api/v2/job_templates/' + str(job_template['id']) + '/survey_spec/', auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['validate_certs']).json()
        job_template['extra_vars'] = parse_extra_vars_to_json(job_template['extra_vars'])
        job_template['schedules'] = get_schedules(job_template)
        unified_job_template_type = 'job_templates'
        notification_templates, job_template['notification_templates_success'] = get_notifications_by_unified_job_template(unified_job_template_type, job_template['id'], 'notification_templates_success', notification_templates, awx_auth)
        notification_templates, job_template['notification_templates_started'] = get_notifications_by_unified_job_template(unified_job_template_type, job_template['id'], 'notification_templates_started', notification_templates, awx_auth)
        notification_templates, job_template['notification_templates_error'] = get_notifications_by_unified_job_template(unified_job_template_type, job_template['id'], 'notification_templates_error', notification_templates, awx_auth)
        
        job_template['roles'], existing_members_set = get_resource_access_list('job_templates', job_template['id'], existing_members_set, awx_auth)
        exported_job_templates.append(job_template)

    return exported_job_templates, credential_ids, notification_templates, existing_members_set