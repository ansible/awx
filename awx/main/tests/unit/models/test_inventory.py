import pytest
import mock
import json

from django.core.exceptions import ValidationError

from awx.main.models import (
    UnifiedJob,
    InventoryUpdate,
    Job,
    Inventory,
    Credential,
    CredentialType,
)


@pytest.fixture
def dependent_job(mocker):
    j = Job(id=3, name='I_am_a_job')
    j.cancel = mocker.MagicMock(return_value=True)
    return [j]


def test_cancel(mocker, dependent_job):
    with mock.patch.object(UnifiedJob, 'cancel', return_value=True) as parent_cancel:
        iu = InventoryUpdate()

        iu.get_dependent_jobs = mocker.MagicMock(return_value=dependent_job)
        iu.save = mocker.MagicMock()
        build_job_explanation_mock = mocker.MagicMock()
        iu._build_job_explanation = mocker.MagicMock(return_value=build_job_explanation_mock)

        iu.cancel()

        parent_cancel.assert_called_with(job_explanation=None)
        dependent_job[0].cancel.assert_called_with(job_explanation=build_job_explanation_mock)
        

def test__build_job_explanation():
    iu = InventoryUpdate(id=3, name='I_am_an_Inventory_Update')

    job_explanation = iu._build_job_explanation()

    assert job_explanation == 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % \
                              ('inventory_update', 'I_am_an_Inventory_Update', 3)


def test_valid_clean_insights_credential():
    cred_type = CredentialType.defaults['insights']()
    insights_cred = Credential(credential_type=cred_type)
    inv = Inventory(insights_credential=insights_cred)

    inv.clean_insights_credential()


def test_invalid_clean_insights_credential():
    cred_type = CredentialType.defaults['scm']()
    cred = Credential(credential_type=cred_type)
    inv = Inventory(insights_credential=cred)

    with pytest.raises(ValidationError) as e:
        inv.clean_insights_credential()

    assert json.dumps(str(e.value)) == json.dumps(str([u"Credential kind must be 'insights'."]))


def test_valid_kind_clean_insights_credential():
    inv = Inventory(kind='smart')

    inv.clean_insights_credential()


def test_invalid_kind_clean_insights_credential():
    cred_type = CredentialType.defaults['insights']()
    insights_cred = Credential(credential_type=cred_type)
    inv = Inventory(kind='smart', insights_credential=insights_cred)

    with pytest.raises(ValidationError) as e:
        inv.clean_insights_credential()

    assert json.dumps(str(e.value)) == json.dumps(str([u'Assignment not allowed for Smart Inventory']))
