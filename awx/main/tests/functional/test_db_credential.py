import pytest

from django.db import IntegrityError
from awx.main.models import Credential


@pytest.mark.django_db
def test_cred_unique_org_name_kind(organization_factory, credentialtype_ssh):
    objects = organization_factory("test")

    cred = Credential(name="test", credential_type=credentialtype_ssh, organization=objects.organization)
    cred.save()

    with pytest.raises(IntegrityError):
        cred = Credential(name="test", credential_type=credentialtype_ssh, organization=objects.organization)
        cred.save()
