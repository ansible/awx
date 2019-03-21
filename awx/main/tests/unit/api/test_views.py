# -*- coding: utf-8 -*-
import re
import pytest
import requests
from copy import deepcopy
from unittest import mock

from collections import namedtuple

from awx.api.views import (
    ApiVersionRootView,
    JobTemplateLabelList,
    InventoryInventorySourcesUpdate,
    HostInsights,
    JobTemplateSurveySpec
)

from awx.main.models import (
    Host,
)
from awx.main.views import handle_error

from rest_framework.test import APIRequestFactory


def test_handle_error():
    # Assure that templating of error does not raise errors
    request = APIRequestFactory().get('/fooooo/')
    handle_error(request)


class TestApiRootView:
    def test_get_endpoints(self, mocker):
        endpoints = [
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
        assert ret.status_code == 200
        for endpoint in endpoints:
            assert endpoint in ret.data


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
            with mocker.patch.object(InventoryInventorySourcesUpdate, 'get_serializer_context', return_value=None):
                with mocker.patch('awx.api.serializers.InventoryUpdateDetailSerializer') as serializer_class:
                    serializer = serializer_class.return_value
                    serializer.to_representation.return_value = {}

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
        (502, requests.exceptions.RequestException, 'booo!', 'Unknown exception booo! while trying to GET https://myexample.com/whocares/me/'),
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
        assert msg['error'] == (
            'Failed to gather reports and maintenance plans from Insights API at URL'
            ' https://myexample.com/whocares/me/. Server responded with 500 status code '
            'and message mock 500 err msg')

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

    def test_get_insights_user_agent(self, patch_parent, mocker):
        with mock.patch.object(requests.Session, 'get') as get:
            HostInsights()._get_insights('https://example.org', 'joe', 'example')
            assert get.call_count == 1
            args, kwargs = get.call_args_list[0]
            assert args == ('https://example.org',)
            assert re.match(r'AWX [^\s]+ \(open\)', kwargs['headers']['User-Agent'])


class TestSurveySpecValidation:

    def test_create_text_encrypted(self):
        view = JobTemplateSurveySpec()
        resp = view._validate_spec_data({
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
        }, {})
        assert resp.status_code == 400
        assert '$encrypted$ is a reserved keyword for password question defaults' in str(resp.data['error'])

    def test_change_encrypted_var_name(self):
        view = JobTemplateSurveySpec()
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
        new = deepcopy(old)
        new['spec'][0]['variable'] = 'openstack_username'
        resp = view._validate_spec_data(new, old)
        assert resp.status_code == 400
        assert 'may not be used for new default' in str(resp.data['error'])

    def test_use_saved_encrypted_default(self):
        '''
        Save is allowed, the $encrypted$ replacement is done
        '''
        view = JobTemplateSurveySpec()
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
        new = deepcopy(old)
        new['spec'][0]['default'] = '$encrypted$'
        new['spec'][0]['required'] = False
        resp = view._validate_spec_data(new, old)
        assert resp is None, resp.data
        assert new == {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "$encrypted$foooooooo",  # default remained the same
                    "max": 1024,
                    "required": False,  # only thing changed
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }

    def test_use_saved_empty_string_default(self):
        '''
        Save is allowed, the $encrypted$ replacement is done with empty string
        The empty string value for default is unencrypted,
        unlike all other password questions
        '''
        view = JobTemplateSurveySpec()
        old = {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "",
                    "max": 1024,
                    "required": True,
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }
        new = deepcopy(old)
        new['spec'][0]['default'] = '$encrypted$'
        resp = view._validate_spec_data(new, old)
        assert resp is None
        assert new == {
            "name": "old survey",
            "description": "foobar",
            "spec": [
                {
                    "question_description": "",
                    "min": 0,
                    "default": "",  # still has old unencrypted default
                    "max": 1024,
                    "required": True,
                    "choices": "",
                    "variable": "openshift_username",
                    "question_name": "OpenShift Username",
                    "type": "password"
                }
            ]
        }


    @staticmethod
    def spec_from_element(survey_item):
        survey_item.setdefault('name', 'foo')
        survey_item.setdefault('variable', 'foo')
        survey_item.setdefault('required', False)
        survey_item.setdefault('question_name', 'foo')
        survey_item.setdefault('type', 'text')
        spec = {
            'name': 'test survey',
            'description': 'foo',
            'spec': [survey_item]
        }
        return spec


    @pytest.mark.parametrize("survey_item, error_text", [
        ({'type': 'password', 'default': ['some', 'invalid', 'list']}, 'expected to be string'),
        ({'type': 'password', 'default': False}, 'expected to be string'),
        ({'type': 'integer', 'default': 'foo'}, 'expected to be int'),
        ({'type': 'integer', 'default': u'🐉'}, 'expected to be int'),
        ({'type': 'foo'}, 'allowed question types'),
        ({'type': u'🐉'}, 'allowed question types'),
        ({'type': 'multiplechoice'}, 'multiplechoice must specify choices'),
        ({'type': 'integer', 'min': 'foo'}, 'min limit in survey question 0 expected to be integer'),
        ({'question_name': 42}, "'question_name' in survey question 0 expected to be string.")
    ])
    def test_survey_question_element_validation(self, survey_item, error_text):
        spec = self.spec_from_element(survey_item)
        r = JobTemplateSurveySpec._validate_spec_data(spec, {})
        assert r is not None, (spec, error_text)
        assert 'error' in r.data
        assert error_text in r.data['error']


    def test_survey_spec_non_dict_error(self):
        spec = self.spec_from_element({})
        spec['spec'][0] = 'foo'
        r = JobTemplateSurveySpec._validate_spec_data(spec, {})
        assert 'Survey question 0 is not a json object' in r.data['error']


    def test_survey_spec_dual_names_error(self):
        spec = self.spec_from_element({})
        spec['spec'].append(spec['spec'][0].copy())
        r = JobTemplateSurveySpec._validate_spec_data(spec, {})
        assert "'variable' 'foo' duplicated in survey question 1." in r.data['error']


    def test_survey_spec_element_missing_property(self):
        spec = self.spec_from_element({})
        spec['spec'][0].pop('type')
        r = JobTemplateSurveySpec._validate_spec_data(spec, {})
        assert "'type' missing from survey question 0" in r.data['error']


    @pytest.mark.parametrize('_type', ['integer', 'float'])
    def test_survey_spec_element_number_empty_default(self, _type):
        """ Assert that empty default is allowed for answer. """
        spec = self.spec_from_element({'type': _type, 'default': ''})
        r = JobTemplateSurveySpec._validate_spec_data(spec, {})
        assert r is None
