import pytest

from django.core.exceptions import ValidationError
from awx.main.models import Credential


@pytest.mark.django_db
def test_clean_credential_with_ssh_type(credentialtype_ssh, job_template):
    credential = Credential(
        name='My Credential',
        credential_type=credentialtype_ssh
    )
    credential.save()

    job_template.credential = credential
    job_template.full_clean()


@pytest.mark.django_db
def test_clean_credential_with_invalid_type_xfail(credentialtype_aws, job_template):
    credential = Credential(
        name='My Credential',
        credential_type=credentialtype_aws
    )
    credential.save()

    with pytest.raises(ValidationError):
        job_template.credential = credential
        job_template.full_clean()


@pytest.mark.django_db
def test_clean_credential_with_custom_types(credentialtype_aws, credentialtype_net, job_template):
    aws = Credential(
        name='AWS Credential',
        credential_type=credentialtype_aws
    )
    aws.save()
    net = Credential(
        name='Net Credential',
        credential_type=credentialtype_net
    )
    net.save()

    job_template.extra_credentials.add(aws)
    job_template.extra_credentials.add(net)
    job_template.full_clean()
