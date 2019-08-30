import pytest

from awx.main.models import Organization


@pytest.mark.django_db
def test_create_organization(run_module, admin_user):

    module_args = {'name': 'foo', 'description': 'barfoo', 'state': 'present'}

    result = run_module('tower_organization', module_args, admin_user)

    org = Organization.objects.get(name='foo')

    assert result == {
        "organization": "foo",
        "state": "present",
        "id": org.id,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert org.description == 'barfoo'
