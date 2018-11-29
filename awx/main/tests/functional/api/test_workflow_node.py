import pytest
import json

from awx.api.versioning import reverse

from awx.main.models.jobs import JobTemplate
from awx.main.models.workflow import WorkflowJobTemplateNode
from awx.main.models.credential import Credential


@pytest.fixture
def job_template(inventory, project):
    # need related resources set for these tests
    return JobTemplate.objects.create(
        name='test-job_template',
        inventory=inventory,
        project=project
    )


@pytest.fixture
def node(workflow_job_template, post, admin_user, job_template):
    return WorkflowJobTemplateNode.objects.create(
        workflow_job_template=workflow_job_template,
        unified_job_template=job_template
    )



@pytest.mark.django_db
def test_blank_UJT_unallowed(workflow_job_template, post, admin_user):
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk})
    r = post(url, {}, user=admin_user, expect=400)
    assert 'unified_job_template' in r.data


@pytest.mark.django_db
def test_cannot_remove_UJT(node, patch, admin_user):
    r = patch(
        node.get_absolute_url(),
        data={'unified_job_template': None},
        user=admin_user,
        expect=400
    )
    assert 'unified_job_template' in r.data


@pytest.mark.django_db
def test_node_rejects_unprompted_fields(inventory, project, workflow_job_template, post, admin_user):
    job_template = JobTemplate.objects.create(
        inventory = inventory,
        project = project,
        playbook = 'helloworld.yml',
        ask_limit_on_launch = False
    )
    url = reverse('api:workflow_job_template_workflow_nodes_list',
                  kwargs={'pk': workflow_job_template.pk, 'version': 'v1'})
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
                  kwargs={'pk': workflow_job_template.pk, 'version': 'v1'})
    post(url, {'unified_job_template': job_template.pk, 'limit': 'webservers'},
         user=admin_user, expect=201)


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


@pytest.mark.django_db
class TestOldCredentialField:
    '''
    The field `credential` on JTs & WFJT nodes is deprecated, but still supported

    TODO: remove tests when JT vault_credential / credential / other stuff
    is removed
    '''
    @pytest.fixture
    def job_template_ask(self, job_template):
        job_template.ask_credential_on_launch = True
        job_template.save()
        return job_template

    def test_credential_accepted_create(self, workflow_job_template, post, admin_user,
                                        job_template_ask, machine_credential):
        r = post(
            reverse(
                'api:workflow_job_template_workflow_nodes_list',
                kwargs = {'pk': workflow_job_template.pk}
            ),
            data = {'credential': machine_credential.pk, 'unified_job_template': job_template_ask.pk},
            user = admin_user,
            expect = 201
        )
        assert r.data['credential'] == machine_credential.pk
        node = WorkflowJobTemplateNode.objects.get(pk=r.data['id'])
        assert list(node.credentials.all()) == [machine_credential]

    @pytest.mark.parametrize('role,code', [
        ['use_role', 201],
        ['read_role', 403]
    ])
    def test_credential_rbac(self, role, code, workflow_job_template, post, rando,
                             job_template_ask, machine_credential):
        role_obj = getattr(machine_credential, role)
        role_obj.members.add(rando)
        job_template_ask.execute_role.members.add(rando)
        workflow_job_template.admin_role.members.add(rando)
        post(
            reverse(
                'api:workflow_job_template_workflow_nodes_list',
                kwargs = {'pk': workflow_job_template.pk}
            ),
            data = {'credential': machine_credential.pk, 'unified_job_template': job_template_ask.pk},
            user = rando,
            expect = code
        )

    def test_credential_add_remove(self, node, patch, machine_credential, admin_user):
        node.unified_job_template.ask_credential_on_launch = True
        node.unified_job_template.save()
        url = node.get_absolute_url()
        patch(
            url,
            data = {'credential': machine_credential.pk},
            user = admin_user,
            expect = 200
        )
        node.refresh_from_db()
        assert node.credential == machine_credential.pk

        patch(
            url,
            data = {'credential': None},
            user = admin_user,
            expect = 200
        )
        node.refresh_from_db()
        assert list(node.credentials.values_list('pk', flat=True)) == []

    def test_credential_replace(self, node, patch, credentialtype_ssh, admin_user):
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
        assert node.credential == cred1.pk
        url = node.get_absolute_url()
        patch(
            url,
            data = {'credential': cred2.pk},
            user = admin_user,
            expect = 200
        )
        assert node.credential == cred2.pk
