# Generated with Claude Opus 4.6
"""Tests that TaskPrepData.from_instance produces the correct credentials
for jobs created via the API, covering all credential-bearing job types.

All credential associations are done via the API to verify compatibility
between the API contract and the task prep data structure."""

import pytest
from unittest import mock

from awx.api.versioning import reverse
from awx.main.models import (
    Job,
    AdHocCommand,
    Credential,
    CredentialType,
    InventoryUpdate,
    InventorySource,
)
from awx.main.tasks.prep import TaskPrepData


@pytest.mark.django_db
class TestJobPrepCredentials:
    """Launch a Job via the API with credentials attached via API and verify
    prep picks up the M2M credentials."""

    def test_job_uses_m2m_credentials(
        self, post, admin, project, inventory, machine_credential, credential
    ):
        jt = project.jobtemplates.create(name="test-jt", inventory=inventory)

        # Attach credentials via the API
        creds_url = reverse("api:job_template_credentials_list", kwargs={"pk": jt.pk})
        post(creds_url, {"id": machine_credential.pk}, admin, expect=204)
        post(creds_url, {"id": credential.pk}, admin, expect=204)

        with mock.patch("awx.main.models.unified_jobs.UnifiedJob.signal_start"):
            response = post(
                reverse("api:job_template_launch", kwargs={"pk": jt.pk}),
                {},
                admin,
                expect=201,
            )

        job = Job.objects.get(pk=response.data["job"])
        prep = TaskPrepData.from_instance(job)

        assert len(prep.credentials) == 2
        prep_pks = {c.pk for c in prep.credentials}
        assert prep_pks == {machine_credential.pk, credential.pk}


@pytest.mark.django_db
class TestProjectUpdatePrepCredentials:
    """Set credential on project via API, sync, and verify prep picks it up."""

    def test_project_update_uses_fk_credential(
        self, patch, admin, project, scm_credential, execution_environment
    ):
        # Attach credential via the API
        patch(
            reverse("api:project_detail", kwargs={"pk": project.pk}),
            {"credential": scm_credential.pk},
            admin,
            expect=200,
        )

        project.refresh_from_db()
        pu = project.create_unified_job()
        prep = TaskPrepData.from_instance(pu)

        assert len(prep.credentials) == 1
        assert prep.credentials[0].pk == scm_credential.pk
        # FK credential is handled by build methods, not the generic injection loop
        assert prep.get_credentials_for_injection() == []

    def test_project_update_no_credential(
        self, patch, admin, project, execution_environment
    ):
        patch(
            reverse("api:project_detail", kwargs={"pk": project.pk}),
            {"credential": None},
            admin,
            expect=200,
        )

        project.refresh_from_db()
        pu = project.create_unified_job()
        prep = TaskPrepData.from_instance(pu)

        assert len(prep.credentials) == 0

    def test_project_update_galaxy_credentials(
        self, post, admin, project, organization, execution_environment
    ):
        galaxy_type = CredentialType.defaults["galaxy_api_token"]()
        galaxy_type.save()
        galaxy_cred = Credential.objects.create(
            credential_type=galaxy_type,
            name="galaxy-cred",
            organization=organization,
            inputs={"url": "https://galaxy.ansible.com/"},
        )

        # Attach galaxy credential to organization via the API
        post(
            reverse(
                "api:organization_galaxy_credentials_list",
                kwargs={"pk": organization.pk},
            ),
            {"associate": True, "id": galaxy_cred.pk},
            admin,
            expect=204,
        )

        pu = project.create_unified_job()
        prep = TaskPrepData.from_instance(pu)

        assert len(prep.galaxy_credentials) == 1
        assert prep.galaxy_credentials[0].pk == galaxy_cred.pk


@pytest.mark.django_db
class TestInventoryUpdatePrepCredentials:
    """Attach credential to inventory source via API, sync, and verify
    prep picks up the M2M credentials."""

    def test_inventory_update_uses_m2m_credentials(
        self, post, admin, inventory, credential
    ):
        inv_src = InventorySource.objects.create(
            name="ec2-src", inventory=inventory, source="ec2"
        )

        # Attach credential via the API
        post(
            reverse("api:inventory_source_credentials_list", kwargs={"pk": inv_src.pk}),
            {"id": credential.pk},
            admin,
            expect=204,
        )

        with mock.patch(
            "awx.main.tasks.system.update_inventory_computed_fields.apply_async"
        ):
            response = post(
                reverse("api:inventory_source_update_view", kwargs={"pk": inv_src.pk}),
                {},
                admin,
                expect=202,
            )

        iu = InventoryUpdate.objects.get(pk=response.data["inventory_update"])
        prep = TaskPrepData.from_instance(iu)

        assert len(prep.credentials) == 1
        assert prep.credentials[0].pk == credential.pk


@pytest.mark.django_db
class TestAdHocCommandPrepCredentials:
    """Create an AdHocCommand via the API and verify prep picks up the FK credential."""

    def test_adhoc_command_credential(self, post, admin, inventory, machine_credential):
        inventory.admin_role.members.add(admin)
        machine_credential.admin_role.members.add(admin)

        with mock.patch("awx.main.models.unified_jobs.UnifiedJob.signal_start"):
            response = post(
                reverse("api:ad_hoc_command_list"),
                {
                    "inventory": inventory.pk,
                    "credential": machine_credential.pk,
                    "module_name": "command",
                    "module_args": "uptime",
                },
                admin,
                expect=201,
            )

        adhoc = AdHocCommand.objects.get(pk=response.data["id"])
        prep = TaskPrepData.from_instance(adhoc)

        assert len(prep.credentials) == 1
        assert prep.credentials[0].pk == machine_credential.pk
        # FK credential is handled by build methods, not the generic injection loop
        assert prep.get_credentials_for_injection() == []
