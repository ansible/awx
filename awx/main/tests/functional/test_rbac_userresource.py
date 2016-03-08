import pytest

@pytest.mark.django_db
def test_user_org_admin(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    member.organizations.add(organization)
    assert not member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.add(admin)
    assert member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.remove(admin)
    assert not member.resource.accessible_by(admin, {'write':True})

@pytest.mark.django_db
def test_org_user_admin(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    organization.member_role.members.add(member)
    assert not member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.add(admin)
    assert member.resource.accessible_by(admin, {'write':True})

    organization.admin_role.members.remove(admin)
    assert not member.resource.accessible_by(admin, {'write':True})

@pytest.mark.django_db
def test_org_user_removed(user, organization):
    admin = user('orgadmin')
    member = user('orgmember')

    organization.admin_role.members.add(admin)
    organization.member_role.members.add(member)

    assert member.resource.accessible_by(admin, {'write':True})

    organization.member_role.members.remove(member)
    assert not member.resource.accessible_by(admin, {'write':True})
