from collections import namedtuple

import pytest
import requests

from awx.api.versioning import reverse


@pytest.mark.django_db
class TestHostInsights:
    def test_insights_bad_host(self, get, hosts, user, mocker):
        mocker.patch.object(requests.Session, 'get')

        host = hosts(host_count=1)[0]

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'] == 'This host is not recognized as an Insights host.'
        assert response.status_code == 404

    def test_insights_host_missing_from_insights(self, get, hosts, insights_credential, user, mocker):
        class Response:
            status_code = 200
            content = "{'results': []}"

            def json(self):
                return {'results': []}

        mocker.patch.object(requests.Session, 'get', return_value=Response())

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.inventory.insights_credential = insights_credential
        host.inventory.save()
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'] == (
            'Could not translate Insights system ID 123e4567-e89b-12d3-a456-426655440000'
            ' into an Insights platform ID.')
        assert response.status_code == 404

    def test_insights_no_credential(self, get, hosts, user, mocker):
        mocker.patch.object(requests.Session, 'get')

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'] == 'The Insights Credential for "test-inv" was not found.'
        assert response.status_code == 404

    @pytest.mark.parametrize("status_code, exception, error, message", [
        (502, requests.exceptions.SSLError, 'SSLError while trying to connect to https://myexample.com/whocares/me/', None,),
        (504, requests.exceptions.Timeout, 'Request to https://myexample.com/whocares/me/ timed out.', None,),
        (502, requests.exceptions.RequestException, 'booo!', 'Unknown exception booo! while trying to GET https://myexample.com/whocares/me/'),
    ])
    def test_insights_exception(self, get, hosts, insights_credential, user, mocker, status_code, exception, error, message):
        mocker.patch.object(requests.Session, 'get', side_effect=exception(error))

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.inventory.insights_credential = insights_credential
        host.inventory.save()
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'] == message or error
        assert response.status_code == status_code

    def test_insights_unauthorized(self, get, hosts, insights_credential, user, mocker):
        Response = namedtuple('Response', 'status_code content')
        mocker.patch.object(requests.Session, 'get', return_value=Response(401, 'mock 401 err msg'))

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.inventory.insights_credential = insights_credential
        host.inventory.save()
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'] == (
            "Unauthorized access. Please check your Insights Credential username and password.")
        assert response.status_code == 502

    def test_insights_bad_status(self, get, hosts, insights_credential, user, mocker):
        Response = namedtuple('Response', 'status_code content')
        mocker.patch.object(requests.Session, 'get', return_value=Response(500, 'mock 500 err msg'))

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.inventory.insights_credential = insights_credential
        host.inventory.save()
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'].startswith("Failed to access the Insights API at URL")
        assert "Server responded with 500 status code and message mock 500 err msg" in response.data['error']
        assert response.status_code == 502

    def test_insights_bad_json(self, get, hosts, insights_credential, user, mocker):
        class Response:
            status_code = 200
            content = 'booo!'

            def json(self):
                raise ValueError("we do not care what this is")

        mocker.patch.object(requests.Session, 'get', return_value=Response())

        host = hosts(host_count=1)[0]
        host.insights_system_id = '123e4567-e89b-12d3-a456-426655440000'
        host.inventory.insights_credential = insights_credential
        host.inventory.save()
        host.save()

        url = reverse('api:host_insights', kwargs={'pk': host.pk})
        response = get(url, user('admin', True))

        assert response.data['error'].startswith("Expected JSON response from Insights at URL")
        assert 'insights_id=123e4567-e89b-12d3-a456-426655440000' in response.data['error']
        assert response.data['error'].endswith("but instead got booo!")
        assert response.status_code == 502
