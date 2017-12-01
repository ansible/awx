import mock
import pytest
import requests
from copy import deepcopy

from collections import namedtuple

from awx.api.views import (
    ApiVersionRootView,
    JobTemplateLabelList,
    InventoryInventorySourcesUpdate,
    InventoryHostsList,
    HostInsights,
    JobTemplateSurveySpec
)

from awx.main.models import (
    Host,
    JobTemplate,
    User
)

from awx.main.managers import HostManager

from rest_framework.test import APIRequestFactory


@pytest.fixture
def mock_response_new(mocker):
    m = mocker.patch('awx.api.views.Response.__new__')
    m.return_value = m
    return m


class TestApiRootView:
    def test_get_endpoints(self, mocker, mock_response_new):
        endpoints = [
            'authtoken',
            'ping',
            'config',
            #'settings',
            'me',
            'dashboard',
            'organizations',
            'users',
            'projects',
            'teams',
            'credentials',
            'inventory',
            'inventory_scripts',
            'inventory_sources',
            'groups',
            'hosts',
            'job_templates',
            'jobs',
            'ad_hoc_commands',
            'system_job_templates',
            'system_jobs',
            'schedules',
            'notification_templates',
            'notifications',
            'labels',
            'unified_job_templates',
            'unified_jobs',
            'activity_stream',
            'workflow_job_templates',
            'workflow_jobs',
        ]
        view = ApiVersionRootView()
        ret = view.get(mocker.MagicMock())

        assert ret == mock_response_new
        data_arg = mock_response_new.mock_calls[0][1][1]
        for endpoint in endpoints:
            assert endpoint in data_arg


class TestJobTemplateLabelList:
    def test_inherited_mixin_unattach(self):
        with mock.patch('awx.api.generics.DeleteLastUnattachLabelMixin.unattach') as mixin_unattach:
            view = JobTemplateLabelList()
            mock_request = mock.MagicMock()

            super(JobTemplateLabelList, view).unattach(mock_request, None, None)
            assert mixin_unattach.called_with(mock_request, None, None)


class TestInventoryInventorySourcesUpdate:

    @pytest.mark.parametrize("can_update, can_access, is_source, is_up_on_proj, expected", [
        (True, True, "ec2", False, [{'status': 'started', 'inventory_update': 1, 'inventory_source': 1}]),
        (False, True, "gce", False, [{'status': 'Could not start because `can_update` returned False', 'inventory_source': 1}]),
        (True, False, "scm", True, [{'status': 'started', 'inventory_update': 1, 'inventory_source': 1}]),
    ])
    def test_post(self, mocker, can_update, can_access, is_source, is_up_on_proj, expected):
        class InventoryUpdate:
            id = 1

        class Project:
            name = 'project'

        InventorySource = namedtuple('InventorySource', ['source', 'update_on_project_update', 'pk', 'can_update',
                                                         'update', 'source_project'])

        class InventorySources(object):
            def all(self):
                return [InventorySource(pk=1, source=is_source, source_project=Project,
                                        update_on_project_update=is_up_on_proj,
                                        can_update=can_update, update=lambda:InventoryUpdate)]

            def exclude(self, **kwargs):
                return self.all()

        Inventory = namedtuple('Inventory', ['inventory_sources', 'kind'])
        obj = Inventory(inventory_sources=InventorySources(), kind='')

        mock_request = mocker.MagicMock()
        mock_request.user.can_access.return_value = can_access

        with mocker.patch.object(InventoryInventorySourcesUpdate, 'get_object', return_value=obj):
            view = InventoryInventorySourcesUpdate()
            response = view.post(mock_request)
            assert response.data == expected


class TestHostInsights():

    @pytest.fixture
    def patch_parent(self, mocker):
        mocker.patch('awx.api.generics.GenericAPIView')

    @pytest.mark.parametrize("status_code, exception, error, message", [
        (502, requests.exceptions.SSLError, 'SSLError while trying to connect to https://myexample.com/whocares/me/', None,),
        (504, requests.exceptions.Timeout, 'Request to https://myexample.com/whocares/me/ timed out.', None,),
        (502, requests.exceptions.RequestException, 'booo!', 'Unkown exception booo! while trying to GET https://myexample.com/whocares/me/'),
    ])
    def test_get_insights_request_exception(self, patch_parent, mocker, status_code, exception, error, message):
        view = HostInsights()
        mocker.patch.object(view, '_get_insights', side_effect=exception(error))

        (msg, code) = view.get_insights('https://myexample.com/whocares/me/', 'ignore', 'ignore')
        assert code == status_code
        assert msg['error'] == message or error

    def test_get_insights_non_200(self, patch_parent, mocker):
        view = HostInsights()
        Response = namedtuple('Response', 'status_code content')
        mocker.patch.object(view, '_get_insights', return_value=Response(500, 'mock 500 err msg'))

        (msg, code) = view.get_insights('https://myexample.com/whocares/me/', 'ignore', 'ignore')
        assert msg['error'] == 'Failed to gather reports and maintenance plans from Insights API at URL https://myexample.com/whocares/me/. Server responded with 500 status code and message mock 500 err msg'

    def test_get_insights_401(self, patch_parent, mocker):
        view = HostInsights()
        Response = namedtuple('Response', 'status_code content')
        mocker.patch.object(view, '_get_insights', return_value=Response(401, ''))

        (msg, code) = view.get_insights('https://myexample.com/whocares/me/', 'ignore', 'ignore')
        assert msg['error'] == 'Unauthorized access. Please check your Insights Credential username and password.'

    def test_get_insights_malformed_json_content(self, patch_parent, mocker):
        view = HostInsights()

        class Response():
            status_code = 200
            content = 'booo!'

            def json(self):
                raise ValueError('we do not care what this is')

        mocker.patch.object(view, '_get_insights', return_value=Response())

        (msg, code) = view.get_insights('https://myexample.com/whocares/me/', 'ignore', 'ignore')
        assert msg['error'] == 'Expected JSON response from Insights but instead got booo!'
        assert code == 502

    #def test_get_not_insights_host(self, patch_parent, mocker, mock_response_new):
    #def test_get_not_insights_host(self, patch_parent, mocker):
    def test_get_not_insights_host(self, mocker):

        view = HostInsights()

        host = Host()
        host.insights_system_id = None

        mocker.patch.object(view, 'get_object', return_value=host)

        resp = view.get(None)

        assert resp.data['error'] == 'This host is not recognized as an Insights host.'
        assert resp.status_code == 404

    def test_get_no_credential(self, patch_parent, mocker):
        view = HostInsights()

        class MockInventory():
            insights_credential = None
            name = 'inventory_name_here'

        class MockHost():
            insights_system_id = 'insights_system_id_value'
            inventory = MockInventory()

        mocker.patch.object(view, 'get_object', return_value=MockHost())

        resp = view.get(None)

        assert resp.data['error'] == 'The Insights Credential for "inventory_name_here" was not found.'
        assert resp.status_code == 404


class TestInventoryHostsList(object):

    def test_host_list_smart_inventory(self, mocker):
        Inventory = namedtuple('Inventory', ['kind', 'host_filter', 'hosts', 'organization_id'])
        obj = Inventory(kind='smart', host_filter='localhost', hosts=HostManager(), organization_id=None)
        obj.hosts.instance = obj

        with mock.patch.object(InventoryHostsList, 'get_parent_object', return_value=obj):
            with mock.patch('awx.main.utils.filters.SmartFilter.query_from_string') as mock_query:
                view = InventoryHostsList()
                view.get_queryset()
                mock_query.assert_called_once_with('localhost')


class TestSurveySpecValidation:

    @pytest.fixture
    def spec_view(self):
        def view_factory(old_spec):
            obj = JobTemplate()
            if old_spec:
                obj.survey_spec = old_spec

            def save(**kwargs):
                pass

            def get_object():
                return get_object.object

            get_object.object = obj
            obj.save = save

            user = User(username='admin')

            def can_access(*args, **kwargs):
                return True

            user.can_access = can_access

            request = APIRequestFactory().get('/api/v2/job_templates/42/survey_spec/')
            request.user = user
            view = JobTemplateSurveySpec()
            view.request = request
            view.get_object = get_object
            return view
        return view_factory

    def test_create_text_encrypted(self, spec_view):
        view = spec_view(None)
        view.request.data = {
            "name": "new survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "$encrypted$",
                    "max": 1024,
                    "required": True,
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "text"
                }
            ]
        }
        resp = view.post(view.request)
        assert resp.status_code == 400
        assert '$encrypted$ is a reserved keyword for password question defaults' in str(resp.data['error'])


    def test_change_encrypted_var_name(self, spec_view):
        old = {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "$encrypted$foooooooo",
                    "max": 1024,
                    "required": True,
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }
        view = spec_view(old)
        new = deepcopy(old)
        new['spec'][0]['variable'] = 'openstack_username'
        view.request.data = new
        resp = view.post(view.request)
        assert resp.status_code == 400
        assert 'may not be used for new default' in str(resp.data['error'])

    def test_use_saved_encrypted_default(self, spec_view):
        '''
        Save is allowed, the $encrypted$ replacement is done
        '''
        old = {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "$encrypted$foooooooo",
                    "max": 1024,
                    "required": True,
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }
        view = spec_view(old)
        new = deepcopy(old)
        new['spec'][0]['default'] = '$encrypted$'
        new['spec'][0]['required'] = False
        view.request.data = new
        resp = view.post(view.request)
        assert resp.status_code == 200
        assert resp.data is None
        assert view.get_object.object.survey_spec == {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "$encrypted$foooooooo",
                    "max": 1024,
                    "required": False,  # only thing changed
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }
