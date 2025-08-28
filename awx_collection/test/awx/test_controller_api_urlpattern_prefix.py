from __future__ import absolute_import, division, print_function

import os
from unittest import mock

__metaclass__ = type

import pytest


def mock_get_registered_page(prefix):
    return mock.Mock(return_value=mock.Mock(get=mock.Mock(return_value={'prefix': prefix})))


@pytest.mark.parametrize(
    "env_dict, controller_host, expected",
    [
        # without CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        [{}, "https://localhost", "/api/v2/"],
        # with CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        [{"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": "/api/controller/"}, "https://localhost", "/api/controller/v2/"],
        [{"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": "/api/controller"}, "https://localhost", "/api/controller/v2/"],
        [{"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": "api/controller"}, "https://localhost", "/api/controller/v2/"],
        [{"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": "/custom/path/"}, "https://localhost", "/custom/path/v2/"],
        # with AWXKIT_API_BASE_PATH env variable
        [{"AWXKIT_API_BASE_PATH": "/api/"}, "https://localhost", "/api/v2/"],
        [{"AWXKIT_API_BASE_PATH": "/awx-api/"}, "https://localhost", "/awx-api/v2/"],
    ],
)
def test_controller_awxkit_get_api_v2_object(collection_import, env_dict, controller_host, expected):
    with mock.patch.dict(os.environ, env_dict):
        controller_awxkit_class = collection_import('plugins.module_utils.awxkit').ControllerAWXKitModule
        controller_awxkit = controller_awxkit_class(argument_spec={}, direct_params=dict(controller_host=controller_host))
        with mock.patch('plugins.module_utils.awxkit.get_registered_page', mock_get_registered_page):
            api_v2_object = controller_awxkit.get_api_v2_object()
        assert getattr(api_v2_object, 'prefix') == expected
