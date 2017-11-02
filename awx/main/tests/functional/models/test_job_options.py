import pytest

from awx.main.models import Credential


@pytest.mark.django_db
def test_clean_credential_with_ssh_type(credentialtype_ssh, job_template):
    credential = Credential(
        name='My Credential',
        credential_type=credentialtype_ssh
    )
    credential.save()

    job_template.credentials.add(credential)
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

    job_template.credentials.add(aws)
    job_template.credentials.add(net)
    job_template.full_clean()
