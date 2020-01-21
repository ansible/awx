import pytest
from unittest import mock

from awx.api.versioning import reverse
from awx.main.utils import decrypt_field
from awx.main.models.workflow import (
    WorkflowJobTemplate, WorkflowJobTemplateNode, WorkflowApprovalTemplate
)
from awx.main.models.jobs import JobTemplate
from awx.main.tasks import deep_copy_model_obj


@pytest.mark.django_db
def test_job_template_copy(post, get, project, inventory, machine_credential, vault_credential,
                           credential, alice, job_template_with_survey_passwords, admin):
    job_template_with_survey_passwords.project = project
    job_template_with_survey_passwords.inventory = inventory
    job_template_with_survey_passwords.save()
    job_template_with_survey_passwords.credentials.add(credential)
    job_template_with_survey_passwords.credentials.add(machine_credential)
    job_template_with_survey_passwords.credentials.add(vault_credential)
    job_template_with_survey_passwords.admin_role.members.add(alice)
    project.admin_role.members.add(alice)
    inventory.admin_role.members.add(alice)
    assert get(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        alice, expect=200
    ).data['can_copy'] is False
    assert get(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        admin, expect=200
    ).data['can_copy'] is True
    assert post(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        {'name': 'new jt name'}, alice, expect=403
    ).data['detail'] == 'Insufficient access to Job Template credentials.'
    jt_copy_pk = post(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        {'name': 'new jt name'}, admin, expect=201
    ).data['id']

    # give credential access to user 'alice'
    for c in (credential, machine_credential, vault_credential):
        c.use_role.members.add(alice)
        c.save()
    assert get(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        alice, expect=200
    ).data['can_copy'] is True
    jt_copy_pk_alice = post(
        reverse('api:job_template_copy', kwargs={'pk': job_template_with_survey_passwords.pk}),
        {'name': 'new jt name'}, alice, expect=201
    ).data['id']

    jt_copy_admin = type(job_template_with_survey_passwords).objects.get(pk=jt_copy_pk)
    jt_copy_alice = type(job_template_with_survey_passwords).objects.get(pk=jt_copy_pk_alice)

    assert jt_copy_admin.created_by == admin
    assert jt_copy_alice.created_by == alice

    for jt_copy in (jt_copy_admin, jt_copy_alice):
        assert jt_copy.name == 'new jt name'
        assert jt_copy.project == project
        assert jt_copy.inventory == inventory
        assert jt_copy.playbook == job_template_with_survey_passwords.playbook
        assert jt_copy.credentials.count() == 3
        assert credential in jt_copy.credentials.all()
        assert vault_credential in jt_copy.credentials.all()
        assert machine_credential in jt_copy.credentials.all()
        assert job_template_with_survey_passwords.survey_spec == jt_copy.survey_spec


@pytest.mark.django_db
def test_project_copy(post, get, project, organization, scm_credential, alice):
    project.credential = scm_credential
    project.save()
    project.admin_role.members.add(alice)
    assert get(
        reverse('api:project_copy', kwargs={'pk': project.pk}), alice, expect=200
    ).data['can_copy'] is False
    project.organization.admin_role.members.add(alice)
    scm_credential.use_role.members.add(alice)
    assert get(
        reverse('api:project_copy', kwargs={'pk': project.pk}), alice, expect=200
    ).data['can_copy'] is True
    project_copy_pk = post(
        reverse('api:project_copy', kwargs={'pk': project.pk}),
        {'name': 'copied project'}, alice, expect=201
    ).data['id']
    project_copy = type(project).objects.get(pk=project_copy_pk)
    assert project_copy.created_by == alice
    assert project_copy.name == 'copied project'
    assert project_copy.organization == organization
    assert project_copy.credential == scm_credential


@pytest.mark.django_db
def test_inventory_copy(inventory, group_factory, post, get, alice, organization):
    group_1_1 = group_factory('g_1_1')
    group_2_1 = group_factory('g_2_1')
    group_2_2 = group_factory('g_2_2')
    group_2_1.parents.add(group_1_1)
    group_2_2.parents.add(group_1_1)
    group_2_2.parents.add(group_2_1)
    host = group_1_1.hosts.create(name='host', inventory=inventory)
    group_2_1.hosts.add(host)
    inventory.admin_role.members.add(alice)
    assert get(
        reverse('api:inventory_copy', kwargs={'pk': inventory.pk}), alice, expect=200
    ).data['can_copy'] is False
    inventory.organization.admin_role.members.add(alice)
    assert get(
        reverse('api:inventory_copy', kwargs={'pk': inventory.pk}), alice, expect=200
    ).data['can_copy'] is True
    with mock.patch('awx.api.generics.trigger_delayed_deep_copy') as deep_copy_mock:
        inv_copy_pk = post(
            reverse('api:inventory_copy', kwargs={'pk': inventory.pk}),
            {'name': 'new inv name'}, alice, expect=201
        ).data['id']
        inventory_copy = type(inventory).objects.get(pk=inv_copy_pk)
        args, kwargs = deep_copy_mock.call_args
        deep_copy_model_obj(*args, **kwargs)
    group_1_1_copy = inventory_copy.groups.get(name='g_1_1')
    group_2_1_copy = inventory_copy.groups.get(name='g_2_1')
    group_2_2_copy = inventory_copy.groups.get(name='g_2_2')
    host_copy = inventory_copy.hosts.get(name='host')
    assert inventory_copy.organization == organization
    assert inventory_copy.created_by == alice
    assert inventory_copy.name == 'new inv name'
    assert set(group_1_1_copy.parents.all()) == set()
    assert set(group_2_1_copy.parents.all()) == set([group_1_1_copy])
    assert set(group_2_2_copy.parents.all()) == set([group_1_1_copy, group_2_1_copy])
    assert set(group_1_1_copy.hosts.all()) == set([host_copy])
    assert set(group_2_1_copy.hosts.all()) == set([host_copy])
    assert set(group_2_2_copy.hosts.all()) == set()


@pytest.mark.django_db
def test_workflow_job_template_copy(workflow_job_template, post, get, admin, organization):
    workflow_job_template.organization = organization
    workflow_job_template.save()
    jts = [JobTemplate.objects.create(name='test-jt-{}'.format(i)) for i in range(0, 5)]
    nodes = [
        WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template, unified_job_template=jts[i]
        ) for i in range(0, 5)
    ]
    nodes[0].success_nodes.add(nodes[1])
    nodes[1].success_nodes.add(nodes[2])
    nodes[0].failure_nodes.add(nodes[3])
    nodes[3].failure_nodes.add(nodes[4])
    with mock.patch('awx.api.generics.trigger_delayed_deep_copy') as deep_copy_mock:
        wfjt_copy_id = post(
            reverse('api:workflow_job_template_copy', kwargs={'pk': workflow_job_template.pk}),
            {'name': 'new wfjt name'}, admin, expect=201
        ).data['id']
        wfjt_copy = type(workflow_job_template).objects.get(pk=wfjt_copy_id)
        args, kwargs = deep_copy_mock.call_args
        deep_copy_model_obj(*args, **kwargs)
    assert wfjt_copy.organization == organization
    assert wfjt_copy.created_by == admin
    assert wfjt_copy.name == 'new wfjt name'
    copied_node_list = [x for x in wfjt_copy.workflow_job_template_nodes.all()]
    copied_node_list.sort(key=lambda x: int(x.unified_job_template.name[-1]))
    for node, success_count, failure_count, always_count in zip(
        copied_node_list,
        [1, 1, 0, 0, 0],
        [1, 0, 0, 1, 0],
        [0, 0, 0, 0, 0]
    ):
        assert node.success_nodes.count() == success_count
        assert node.failure_nodes.count() == failure_count
        assert node.always_nodes.count() == always_count
    assert copied_node_list[1] in copied_node_list[0].success_nodes.all()
    assert copied_node_list[2] in copied_node_list[1].success_nodes.all()
    assert copied_node_list[3] in copied_node_list[0].failure_nodes.all()
    assert copied_node_list[4] in copied_node_list[3].failure_nodes.all()


@pytest.mark.django_db
def test_workflow_approval_node_copy(workflow_job_template, post, get, admin, organization):
    workflow_job_template.organization = organization
    workflow_job_template.save()
    ajts = [
        WorkflowApprovalTemplate.objects.create(
            name='test-approval-{}'.format(i),
            description='description-{}'.format(i),
            timeout=30
        )
        for i in range(0, 5)
    ]
    nodes = [
        WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template, unified_job_template=ajts[i]
        ) for i in range(0, 5)
    ]
    nodes[0].success_nodes.add(nodes[1])
    nodes[1].success_nodes.add(nodes[2])
    nodes[0].failure_nodes.add(nodes[3])
    nodes[3].failure_nodes.add(nodes[4])
    assert WorkflowJobTemplate.objects.count() == 1
    assert WorkflowJobTemplateNode.objects.count() == 5
    assert WorkflowApprovalTemplate.objects.count() == 5

    with mock.patch('awx.api.generics.trigger_delayed_deep_copy') as deep_copy_mock:
        wfjt_copy_id = post(
            reverse('api:workflow_job_template_copy', kwargs={'pk': workflow_job_template.pk}),
            {'name': 'new wfjt name'}, admin, expect=201
        ).data['id']
        wfjt_copy = type(workflow_job_template).objects.get(pk=wfjt_copy_id)
        args, kwargs = deep_copy_mock.call_args
        deep_copy_model_obj(*args, **kwargs)
    assert wfjt_copy.organization == organization
    assert wfjt_copy.created_by == admin
    assert wfjt_copy.name == 'new wfjt name'

    assert WorkflowJobTemplate.objects.count() == 2
    assert WorkflowJobTemplateNode.objects.count() == 10
    assert WorkflowApprovalTemplate.objects.count() == 10
    original_templates = [
        x.unified_job_template for x in workflow_job_template.workflow_job_template_nodes.all()
    ]
    copied_templates = [
        x.unified_job_template for x in wfjt_copy.workflow_job_template_nodes.all()
    ]

    # make sure shallow fields like `timeout` are copied properly
    for i, t in enumerate(original_templates):
        assert t.timeout == 30
        assert t.description == 'description-{}'.format(i)

    for i, t in enumerate(copied_templates):
        assert t.timeout == 30
        assert t.description == 'description-{}'.format(i)

    # the Approval Template IDs on the *original* WFJT should not match *any*
    # of the Approval Template IDs on the *copied* WFJT
    assert not set([x.id for x in original_templates]).intersection(
        set([x.id for x in copied_templates])
    )

    # if you remove the " copy" suffix from the copied template names, they
    # should match the original templates
    assert (
        set([x.name for x in original_templates]) ==
        set([x.name.replace(' copy', '') for x in copied_templates])
    )


@pytest.mark.django_db
def test_credential_copy(post, get, machine_credential, credentialtype_ssh, admin):
    assert get(
        reverse('api:credential_copy', kwargs={'pk': machine_credential.pk}), admin, expect=200
    ).data['can_copy'] is True
    credential_copy_pk = post(
        reverse('api:credential_copy', kwargs={'pk': machine_credential.pk}),
        {'name': 'copied credential'}, admin, expect=201
    ).data['id']
    credential_copy = type(machine_credential).objects.get(pk=credential_copy_pk)
    assert credential_copy.created_by == admin
    assert credential_copy.name == 'copied credential'
    assert credential_copy.credential_type == credentialtype_ssh
    assert credential_copy.inputs['username'] == machine_credential.inputs['username']
    assert (decrypt_field(credential_copy, 'password') ==
            decrypt_field(machine_credential, 'password'))


@pytest.mark.django_db
def test_notification_template_copy(post, get, notification_template_with_encrypt,
                                    organization, alice):
    notification_template_with_encrypt.organization.auditor_role.members.add(alice)
    assert get(
        reverse(
            'api:notification_template_copy', kwargs={'pk': notification_template_with_encrypt.pk}
        ), alice, expect=200
    ).data['can_copy'] is False
    notification_template_with_encrypt.organization.admin_role.members.add(alice)
    assert get(
        reverse(
            'api:notification_template_copy', kwargs={'pk': notification_template_with_encrypt.pk}
        ), alice, expect=200
    ).data['can_copy'] is True
    nt_copy_pk = post(
        reverse(
            'api:notification_template_copy', kwargs={'pk': notification_template_with_encrypt.pk}
        ), {'name': 'copied nt'}, alice, expect=201
    ).data['id']
    notification_template_copy = type(notification_template_with_encrypt).objects.get(pk=nt_copy_pk)
    assert notification_template_copy.created_by == alice
    assert notification_template_copy.name == 'copied nt'
    assert notification_template_copy.organization == organization
    assert (decrypt_field(notification_template_with_encrypt, 'notification_configuration', 'token') ==
            decrypt_field(notification_template_copy, 'notification_configuration', 'token'))


@pytest.mark.django_db
def test_inventory_script_copy(post, get, inventory_script, organization, alice):
    inventory_script.organization.auditor_role.members.add(alice)
    assert get(
        reverse('api:inventory_script_copy', kwargs={'pk': inventory_script.pk}), alice, expect=200
    ).data['can_copy'] is False
    inventory_script.organization.admin_role.members.add(alice)
    assert get(
        reverse('api:inventory_script_copy', kwargs={'pk': inventory_script.pk}), alice, expect=200
    ).data['can_copy'] is True
    is_copy_pk = post(
        reverse('api:inventory_script_copy', kwargs={'pk': inventory_script.pk}),
        {'name': 'copied inv script'}, alice, expect=201
    ).data['id']
    inventory_script_copy = type(inventory_script).objects.get(pk=is_copy_pk)
    assert inventory_script_copy.created_by == alice
    assert inventory_script_copy.name == 'copied inv script'
    assert inventory_script_copy.organization == organization
