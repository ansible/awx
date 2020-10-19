import pytest
import json

from awx.api.versioning import reverse

from awx.main.models.activity_stream import ActivityStream
from awx.main.models.jobs import JobTemplate
from awx.main.models.workflow import (
    WorkflowApproval,
    WorkflowApprovalTemplate,
    WorkflowJob,
    WorkflowJobTemplate,
    WorkflowJobTemplateNode,
)
from awx.main.models.credential import Credential
from awx.main.scheduler import TaskManager


@pytest.fixture
def job_template(inventory, project):
    # need related resources set for these tests
    return JobTemplate.objects.create(
        name='test-job_template',
        inventory=inventory,
        project=project
    )


@pytest.fixture
def node(workflow_job_template, admin_user, job_template):
    return WorkflowJobTemplateNode.objects.create(
        workflow_job_template=workflow_job_template,
        unified_job_template=job_template
    )


@pytest.fixture
def approval_node(workflow_job_template, admin_user):
    return WorkflowJobTemplateNode.objects.create(
        workflow_job_template=workflow_job_template
    )


@pytest.mark.django_db
def test_node_rejects_unprompted_fields(inventory, project, workflow_job_template, post, admin_user):
    job_template = JobTemplate.objects.create(
        inventory = inventory,
        project = project,
        playbook = 'helloworld.yml',
        ask_limit_on_launch = False
    )
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk})
    r = post(url, {'unified_job_template': job_template.pk, 'limit': 'webservers'},
             user=admin_user, expect=400)
    assert 'limit' in r.data
    assert 'not configured to prompt on launch' in r.data['limit'][0]


@pytest.mark.django_db
def test_node_accepts_prompted_fields(inventory, project, workflow_job_template, post, admin_user):
    job_template = JobTemplate.objects.create(
        inventory = inventory,
        project = project,
        playbook = 'helloworld.yml',
        ask_limit_on_launch = True
    )
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk})
    post(url, {'unified_job_template': job_template.pk, 'limit': 'webservers'},
         user=admin_user, expect=201)


@pytest.mark.django_db
@pytest.mark.parametrize("field_name, field_value", [
    ('all_parents_must_converge', True),
    ('all_parents_must_converge', False),
])
def test_create_node_with_field(field_name, field_value, workflow_job_template, post, admin_user):
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk})
    res = post(url, {field_name: field_value}, user=admin_user, expect=201)
    assert res.data[field_name] == field_value


@pytest.mark.django_db
class TestApprovalNodes():
    def test_approval_node_creation(self, post, approval_node, admin_user):
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        post(url, {'name': 'Test', 'description': 'Approval Node', 'timeout': 0},
             user=admin_user, expect=201)

        approval_node = WorkflowJobTemplateNode.objects.get(pk=approval_node.pk)
        assert isinstance(approval_node.unified_job_template, WorkflowApprovalTemplate)
        assert approval_node.unified_job_template.name=='Test'
        assert approval_node.unified_job_template.description=='Approval Node'
        assert approval_node.unified_job_template.timeout==0

    def test_approval_node_creation_failure(self, post, approval_node, admin_user):
        # This test leaves off a required param to assert that user will get a 400.
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        r = post(url, {'name': '', 'description': 'Approval Node', 'timeout': 0},
                 user=admin_user, expect=400)
        approval_node = WorkflowJobTemplateNode.objects.get(pk=approval_node.pk)
        assert isinstance(approval_node.unified_job_template, WorkflowApprovalTemplate) is False
        assert {'name': ['This field may not be blank.']} == json.loads(r.content)

    @pytest.mark.parametrize("is_admin, is_org_admin, status", [
        [True, False, 201], # if they're a WFJT admin, they get a 201
        [False, False, 403], # if they're not a WFJT *nor* org admin, they get a 403
        [False, True, 201], # if they're an organization admin, they get a 201
    ])
    def test_approval_node_creation_rbac(self, post, approval_node, alice, is_admin, is_org_admin, status):
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        if is_admin is True:
            approval_node.workflow_job_template.admin_role.members.add(alice)
        if is_org_admin is True:
            approval_node.workflow_job_template.organization.admin_role.members.add(alice)
        post(url, {'name': 'Test', 'description': 'Approval Node', 'timeout': 0},
             user=alice, expect=status)

    @pytest.mark.django_db
    def test_approval_node_exists(self, post, admin_user, get):
        workflow_job_template = WorkflowJobTemplate.objects.create()
        approval_node = WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template
        )
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0},
             user=admin_user)
        get(url, admin_user, expect=200)

    @pytest.mark.django_db
    def test_activity_stream_create_wf_approval(self, post, admin_user, workflow_job_template):
        wfjn = WorkflowJobTemplateNode.objects.create(workflow_job_template=workflow_job_template)
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': wfjn.pk, 'version': 'v2'})
        post(url, {'name': 'Activity Stream Test', 'description': 'Approval Node', 'timeout': 0},
             user=admin_user)

        qs1 = ActivityStream.objects.filter(organization__isnull=False)
        assert qs1.count() == 1
        assert qs1[0].operation == 'create'

        qs2 = ActivityStream.objects.filter(organization__isnull=True)
        assert qs2.count() == 5
        assert list(qs2.values_list('operation', 'object1')) == [('create', 'user'),
                                                                 ('create', 'workflow_job_template'),
                                                                 ('create', 'workflow_job_template_node'),
                                                                 ('create', 'workflow_approval_template'),
                                                                 ('update', 'workflow_job_template_node'),
                                                                 ]

    @pytest.mark.django_db
    def test_approval_node_approve(self, post, admin_user, job_template):
        # This test ensures that a user (with permissions to do so) can APPROVE
        # workflow approvals.  Also asserts that trying to APPROVE approvals
        # that have already been dealt with will throw an error.
        wfjt = WorkflowJobTemplate.objects.create(name='foobar')
        node = wfjt.workflow_nodes.create(unified_job_template=job_template)
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': node.pk, 'version': 'v2'})
        post(url, {'name': 'Approve Test', 'description': '', 'timeout': 0},
             user=admin_user, expect=201)
        post(reverse('api:workflow_job_template_launch', kwargs={'pk': wfjt.pk}),
             user=admin_user, expect=201)
        wf_job = WorkflowJob.objects.first()
        TaskManager().schedule()
        TaskManager().schedule()
        wfj_node = wf_job.workflow_nodes.first()
        approval = wfj_node.job
        assert approval.name == 'Approve Test'
        post(reverse('api:workflow_approval_approve', kwargs={'pk': approval.pk}),
             user=admin_user, expect=204)
        # Test that there is an activity stream entry that was created for the "approve" action.
        qs = ActivityStream.objects.order_by('-timestamp').first()
        assert qs.object1 == 'workflow_approval'
        assert qs.changes == '{"status": ["pending", "successful"]}'
        assert WorkflowApproval.objects.get(pk=approval.pk).status == 'successful'
        assert qs.operation == 'update'
        post(reverse('api:workflow_approval_approve', kwargs={'pk': approval.pk}),
             user=admin_user, expect=400)

    @pytest.mark.django_db
    def test_approval_node_deny(self, post, admin_user, job_template):
        # This test ensures that a user (with permissions to do so) can DENY
        # workflow approvals.  Also asserts that trying to DENY approvals
        # that have already been dealt with will throw an error.
        wfjt = WorkflowJobTemplate.objects.create(name='foobar')
        node = wfjt.workflow_nodes.create(unified_job_template=job_template)
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': node.pk, 'version': 'v2'})
        post(url, {'name': 'Deny Test', 'description': '', 'timeout': 0},
             user=admin_user, expect=201)
        post(reverse('api:workflow_job_template_launch', kwargs={'pk': wfjt.pk}),
             user=admin_user, expect=201)
        wf_job = WorkflowJob.objects.first()
        TaskManager().schedule()
        TaskManager().schedule()
        wfj_node = wf_job.workflow_nodes.first()
        approval = wfj_node.job
        assert approval.name == 'Deny Test'
        post(reverse('api:workflow_approval_deny', kwargs={'pk': approval.pk}),
             user=admin_user, expect=204)
        # Test that there is an activity stream entry that was created for the "deny" action.
        qs = ActivityStream.objects.order_by('-timestamp').first()
        assert qs.object1 == 'workflow_approval'
        assert qs.changes == '{"status": ["pending", "failed"]}'
        assert WorkflowApproval.objects.get(pk=approval.pk).status == 'failed'
        assert qs.operation == 'update'
        post(reverse('api:workflow_approval_deny', kwargs={'pk': approval.pk}),
             user=admin_user, expect=400)

    def test_approval_node_cleanup(self, post, approval_node, admin_user, get):
        workflow_job_template = WorkflowJobTemplate.objects.create()
        approval_node = WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template
        )
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})

        post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0},
             user=admin_user)
        assert WorkflowApprovalTemplate.objects.count() == 1
        workflow_job_template.delete()
        assert WorkflowApprovalTemplate.objects.count() == 0
        get(url, admin_user, expect=404)

    def test_changed_approval_deletion(self, post, approval_node, admin_user, workflow_job_template, job_template):
        # This test verifies that when an approval node changes into something else
        # (in this case, a job template), then the previously-set WorkflowApprovalTemplate
        # is automatically deleted.
        workflow_job_template = WorkflowJobTemplate.objects.create()
        approval_node = WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template
        )
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0},
             user=admin_user)
        assert WorkflowApprovalTemplate.objects.count() == 1
        approval_node.unified_job_template = job_template
        approval_node.save()
        assert WorkflowApprovalTemplate.objects.count() == 0

    def test_deleted_approval_denial(self, post, approval_node, admin_user, workflow_job_template):
        # Verifying that when a WorkflowApprovalTemplate is deleted, any/all of
        # its pending approvals are auto-denied (vs left in 'pending' state).
        workflow_job_template = WorkflowJobTemplate.objects.create()
        approval_node = WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template
        )
        url = reverse('api:workflow_job_template_node_create_approval',
                      kwargs={'pk': approval_node.pk, 'version': 'v2'})
        post(url, {'name': 'URL Test', 'description': 'An approval', 'timeout': 0},
             user=admin_user)
        assert WorkflowApprovalTemplate.objects.count() == 1
        approval_template = WorkflowApprovalTemplate.objects.first()
        approval = approval_template.create_unified_job()
        approval.status = 'pending'
        approval.save()
        approval_template.delete()
        approval.refresh_from_db()
        assert approval.status == 'failed'


@pytest.mark.django_db
class TestExclusiveRelationshipEnforcement():
    @pytest.fixture
    def n1(self, workflow_job_template):
        return WorkflowJobTemplateNode.objects.create(workflow_job_template=workflow_job_template)

    @pytest.fixture
    def n2(self, workflow_job_template):
        return WorkflowJobTemplateNode.objects.create(workflow_job_template=workflow_job_template)

    def generate_url(self, relationship, id):
        return reverse('api:workflow_job_template_node_{}_nodes_list'.format(relationship),
                       kwargs={'pk': id})

    relationship_permutations = [
        ['success', 'failure', 'always'],
        ['success', 'always', 'failure'],
        ['failure', 'always', 'success'],
        ['failure', 'success', 'always'],
        ['always', 'success', 'failure'],
        ['always', 'failure', 'success'],
    ]

    @pytest.mark.parametrize("relationships", relationship_permutations, ids=["-".join(item) for item in relationship_permutations])
    def test_multi_connections_same_parent_disallowed(self, post, admin_user, n1, n2, relationships):
        for index, relationship in enumerate(relationships):
            r = post(self.generate_url(relationship, n1.id),
                     data={'associate': True, 'id': n2.id},
                     user=admin_user,
                     expect=204 if index == 0 else 400)

            if index != 0:
                assert {'Error': 'Relationship not allowed.'} == json.loads(r.content)

    @pytest.mark.parametrize("relationship", ['success', 'failure', 'always'])
    def test_existing_relationship_allowed(self, post, admin_user, n1, n2, relationship):
        post(self.generate_url(relationship, n1.id),
             data={'associate': True, 'id': n2.id},
             user=admin_user,
             expect=204)
        post(self.generate_url(relationship, n1.id),
             data={'associate': True, 'id': n2.id},
             user=admin_user,
             expect=204)


@pytest.mark.django_db
class TestNodeCredentials:
    '''
    The supported way to provide credentials on launch is through a list
    under the "credentials" key - WFJT nodes have a many-to-many relationship
    corresponding to this, and it must follow rules consistent with other prompts
    '''
    @pytest.fixture
    def job_template_ask(self, job_template):
        job_template.ask_credential_on_launch = True
        job_template.save()
        return job_template

    def test_not_allows_non_job_models(self, post, admin_user, workflow_job_template,
                                       project, machine_credential):
        node = WorkflowJobTemplateNode.objects.create(
            workflow_job_template=workflow_job_template,
            unified_job_template=project
        )
        r = post(
            reverse(
                'api:workflow_job_template_node_credentials_list',
                kwargs = {'pk': node.pk}
            ),
            data = {'id': machine_credential.pk},
            user = admin_user,
            expect = 400
        )
        assert 'cannot accept credentials on launch' in str(r.data['msg'])

    def test_credential_accepted_create(self, workflow_job_template, post, admin_user,
                                        job_template_ask, machine_credential):
        r = post(
            reverse(
                'api:workflow_job_template_workflow_nodes_list',
                kwargs = {'pk': workflow_job_template.pk}
            ),
            data = {'unified_job_template': job_template_ask.pk},
            user = admin_user,
            expect = 201
        )
        node = WorkflowJobTemplateNode.objects.get(pk=r.data['id'])
        post(url=r.data['related']['credentials'], data={'id': machine_credential.pk}, user=admin_user, expect=204)
        assert list(node.credentials.all()) == [machine_credential]

    @pytest.mark.parametrize('role,code', [
        ['use_role', 204],
        ['read_role', 403]
    ])
    def test_credential_rbac(self, role, code, workflow_job_template, post, rando,
                             job_template_ask, machine_credential):
        role_obj = getattr(machine_credential, role)
        role_obj.members.add(rando)
        job_template_ask.execute_role.members.add(rando)
        workflow_job_template.admin_role.members.add(rando)
        r = post(
            reverse(
                'api:workflow_job_template_workflow_nodes_list',
                kwargs = {'pk': workflow_job_template.pk}
            ),
            data = {'unified_job_template': job_template_ask.pk},
            user = rando,
            expect = 201
        )
        creds_url = r.data['related']['credentials']
        post(url=creds_url, data={'id': machine_credential.pk}, user=rando, expect=code)

    def test_credential_add_remove(self, node, get, post, machine_credential, admin_user):
        node.unified_job_template.ask_credential_on_launch = True
        node.unified_job_template.save()
        url = node.get_absolute_url()
        r = get(url=url, user=admin_user, expect=200)
        post(
            url = r.data['related']['credentials'],
            data = {'id': machine_credential.pk},
            user = admin_user,
            expect = 204
        )
        node.refresh_from_db()

        post(
            url = r.data['related']['credentials'],
            data = {'id': machine_credential.pk, 'disassociate': True},
            user = admin_user,
            expect = 204
        )
        node.refresh_from_db()
        assert list(node.credentials.values_list('pk', flat=True)) == []

    def test_credential_replace(self, node, get, post, credentialtype_ssh, admin_user):
        node.unified_job_template.ask_credential_on_launch = True
        node.unified_job_template.save()
        cred1 = Credential.objects.create(
            credential_type=credentialtype_ssh,
            name='machine-cred1',
            inputs={'username': 'test_user', 'password': 'pas4word'})
        cred2 = Credential.objects.create(
            credential_type=credentialtype_ssh,
            name='machine-cred2',
            inputs={'username': 'test_user', 'password': 'pas4word'})
        node.credentials.add(cred1)
        url = node.get_absolute_url()
        r = get(url=url, user=admin_user, expect=200)
        creds_url = r.data['related']['credentials']
        # cannot do it this way
        r2 = post(url=creds_url, data={'id': cred2.pk}, user=admin_user, expect=400)
        assert 'This launch configuration already provides a Machine credential' in r2.data['msg']
        # guess I will remove that existing one
        post(url=creds_url, data={'id': cred1.pk, 'disassociate': True}, user=admin_user, expect=204)
        # okay, now I will add the new one
        post(url=creds_url, data={'id': cred2.pk}, user=admin_user, expect=204)
        assert list(node.credentials.values_list('id', flat=True)) == [cred2.pk]
