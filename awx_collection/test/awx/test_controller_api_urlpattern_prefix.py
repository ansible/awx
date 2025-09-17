from __future__ import absolute_import, division, print_function

import os
from unittest import mock

__metaclass__ = type

import pytest


def mock_get_registered_page(prefix):
    return mock.Mock(return_value=mock.Mock(get=mock.Mock(return_value={'prefix': prefix})))


@pytest.mark.parametrize(
    "env_prefix, controller_host, expected",
    [
        # without CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        [None, "https://localhost", "/api/v2/"],
        # with CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        ["/api/controller/", "https://localhost", "/api/controller/v2/"],
        ["/api/controller", "https://localhost", "/api/controller/v2/"],
        ["api/controller", "https://localhost", "/api/controller/v2/"],
        ["/custom/path/", "https://localhost", "/custom/path/v2/"],
    ],
)
def test_controller_awxkit_get_api_v2_object(collection_import, env_prefix, controller_host, expected):
    controller_awxkit_class = collection_import('plugins.module_utils.awxkit').ControllerAWXKitModule
    controller_awxkit = controller_awxkit_class(argument_spec={}, direct_params=dict(controller_host=controller_host))
    with mock.patch('plugins.module_utils.awxkit.get_registered_page', mock_get_registered_page):
        if env_prefix:
            with mock.patch.dict(os.environ, {"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": env_prefix}):
                api_v2_object = controller_awxkit.get_api_v2_object()
        else:
            api_v2_object = controller_awxkit.get_api_v2_object()
        assert getattr(api_v2_object, 'prefix') == expected
