import pytest

@pytest.mark.django_db
def test_user_resource_org_admin(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    member.organizations.add(organization)
    assert not member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.add(admin)
    assert member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.remove(admin)
    assert not member.resource.accessible_by(admin, {'write':True})
