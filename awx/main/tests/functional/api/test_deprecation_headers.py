import pytest

from awx.api.versioning import reverse
from awx.main.models import Credential, CredentialType


@pytest.mark.django_db
class TestDeprecatedEndpointHeaders:
    """Test that deprecated endpoints emit both legacy and new deprecation headers."""

    def test_dashboard_returns_deprecation_headers(self, get, admin_user):
        response = get(reverse("api:dashboard_view"), user=admin_user, expect=200)
        assert response["Warning"] == '299 awx "This resource has been deprecated and will be removed in a future release."'
        assert response["X-API-Deprecated"] == "true"
        assert "X-API-Deprecated-Detail" in response

    def test_role_list_returns_deprecation_headers(self, get, admin_user):
        response = get(reverse("api:role_list"), user=admin_user, expect=200)
        assert response["X-API-Deprecated"] == "true"
        assert "deprecated" in response["X-API-Deprecated-Detail"].lower()

    def test_non_deprecated_endpoint_has_no_deprecation_headers(self, get, admin_user):
        response = get(reverse("api:project_list"), user=admin_user, expect=200)
        assert "X-API-Deprecated" not in response
        assert "X-API-Deprecated-Detail" not in response


@pytest.mark.django_db
class TestDeprecatedFieldHeaders:
    """Test that submitting deprecated fields emits deprecation headers."""

    def test_inventory_source_credential_field_deprecation_on_patch(self, patch, admin_user, inventory_source):
        url = reverse("api:inventory_source_detail", kwargs={"pk": inventory_source.pk})
        cred_type = CredentialType.defaults["aws"]()
        cred_type.save()
        cred = Credential.objects.create(
            name="test-aws-cred",
            credential_type=cred_type,
            inputs={"username": "bob", "password": "secret"},
        )
        response = patch(url, {"credential": cred.pk}, user=admin_user, expect=200)
        assert response["X-API-Deprecated"] == "true"
        assert "credential" in response["X-API-Deprecated-Detail"].lower()

    def test_inventory_source_no_deprecation_without_credential_field(self, patch, admin_user, inventory_source):
        url = reverse("api:inventory_source_detail", kwargs={"pk": inventory_source.pk})
        response = patch(url, {"name": "renamed-source"}, user=admin_user, expect=200)
        assert "X-API-Deprecated" not in response

    def test_inventory_source_get_no_field_deprecation(self, get, admin_user, inventory_source):
        url = reverse("api:inventory_source_detail", kwargs={"pk": inventory_source.pk})
        response = get(url, user=admin_user, expect=200)
        assert "X-API-Deprecated" not in response
