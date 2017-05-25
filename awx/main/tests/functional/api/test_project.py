import pytest


@pytest.mark.django_db
class TestInsightsCredential:
    def test_insights_credential(self, patch, insights_project, admin_user, insights_credential):
        patch(insights_project.get_absolute_url(), 
              {'credential': insights_credential.id}, admin_user,
              expect=200)

    def test_non_insights_credential(self, patch, insights_project, admin_user, scm_credential):
        patch(insights_project.get_absolute_url(), 
              {'credential': scm_credential.id}, admin_user,
              expect=400)

