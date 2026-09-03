import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
class TestApiV2PingView:
    """Verify the /api/v2/ping/ endpoint only exposes public fields.

    The ping endpoint is intentionally unauthenticated (AllowAny) and must
    NOT disclose internal mesh topology (instances, instance_groups),
    install_uuid, or active_node.  It should still return ``ha`` and
    ``version`` so that the installer process can use them.
    """

    def test_ping_does_not_disclose_topology(self, get):
        """Unauthenticated ping must not leak sensitive fields."""
        url = reverse('api:api_v2_ping_view')
        response = get(url, expect=200)

        assert 'instances' not in response.data
        assert 'instance_groups' not in response.data
        assert 'install_uuid' not in response.data
        assert 'active_node' not in response.data

    def test_ping_returns_public_fields(self, get):
        """Unauthenticated ping must still return ha and version."""
        url = reverse('api:api_v2_ping_view')
        response = get(url, expect=200)

        assert 'ha' in response.data
        assert 'version' in response.data
        assert isinstance(response.data['ha'], bool)
        assert isinstance(response.data['version'], str)
        assert len(response.data['version']) > 0
