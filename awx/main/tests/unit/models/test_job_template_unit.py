from awx.main.tests.factories import create_job_template


def test_missing_project_error():
    objects = create_job_template(
        'missing-project-jt',
        organization='org1',
        inventory='inventory1',
        credential='cred1',
        persisted=False)
    obj = objects.job_template
    assert 'project' in obj.resources_needed_to_start
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'project' in validation_errors

def test_inventory_credential_need_to_start():
    objects = create_job_template(
        'job-template-few-resources',
        project='project1',
        persisted=False)
    obj = objects.job_template
    assert 'inventory' in obj.resources_needed_to_start
    assert 'credential' in obj.resources_needed_to_start

def test_inventory_credential_contradictions():
    objects = create_job_template(
        'job-template-paradox',
        project='project1',
        persisted=False)
    obj = objects.job_template
    obj.ask_inventory_on_launch = False
    obj.ask_credential_on_launch = False
    validation_errors, resources_needed_to_start = obj.resource_validation_data()
    assert 'inventory' in validation_errors
    assert 'credential' in validation_errors
