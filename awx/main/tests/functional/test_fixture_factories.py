import pytest

@pytest.mark.django_db
def test_org_factory(organization_factory):
    objects = organization_factory('organization1',
                                   teams=['team1'],
                                   superusers=['superuser'],
                                   users=['admin', 'alice', 'team1:bob'],
                                   projects=['proj1'])
    assert hasattr(objects.users, 'admin')
    assert hasattr(objects.users, 'alice')
    assert hasattr(objects.superusers, 'superuser')
    assert objects.users.bob in objects.teams.team1.member_role.members.all()
    assert objects.projects.proj1.organization == objects.organization

@pytest.mark.django_db
def test_job_template_factory(job_template_factory):
    jt_objects = job_template_factory('testJT', organization='org1',
                                      project='proj1', inventory='inventory1',
                                      credential='cred1')
    assert jt_objects.job_template.name == 'testJT'
    assert jt_objects.project.name == 'proj1'
    assert jt_objects.inventory.name == 'inventory1'
    assert jt_objects.credential.name == 'cred1'
    assert jt_objects.inventory.organization.name == 'org1'
