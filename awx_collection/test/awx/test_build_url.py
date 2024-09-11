from __future__ import absolute_import, division, print_function

import os
from unittest import mock

__metaclass__ = type

import pytest


@pytest.mark.parametrize(
    "collection_type, env_prefix, controller_host, app_key, endpoint, expected",
    [
        # without CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        ["awx", None, "https://localhost:8043", None, "jobs", "https://localhost:8043/api/v2/jobs/"],
        ["awx", None, "https://localhost:8043", None, "jobs/209", "https://localhost:8043/api/v2/jobs/209/"],
        ["awx", None, "https://localhost:8043", None, "organizations", "https://localhost:8043/api/v2/organizations/"],
        ["awx", None, "https://localhost", "controller", "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["awx", None, "https://localhost", "controller", "jobs/1", "https://localhost/api/controller/v2/jobs/1/"],
        ["awx", None, "https://localhost", "gateway", "tokens", "https://localhost/api/gateway/v1/tokens/"],
        ["awx", None, "https://localhost", "gateway", "tokens/199", "https://localhost/api/gateway/v1/tokens/199/"],
        ["controller", None, "https://localhost", None, "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["controller", None, "https://localhost", None, "jobs/209", "https://localhost/api/controller/v2/jobs/209/"],
        ["controller", None, "https://localhost", None, "organizations", "https://localhost/api/controller/v2/organizations/"],
        ["controller", None, "https://localhost", "controller", "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["controller", None, "https://localhost", "controller", "jobs/1", "https://localhost/api/controller/v2/jobs/1/"],
        ["controller", None, "https://localhost", "gateway", "tokens", "https://localhost/api/gateway/v1/tokens/"],
        ["controller", None, "https://localhost", "gateway", "tokens/199", "https://localhost/api/gateway/v1/tokens/199/"],
        # with CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX env variable
        ["awx", "api/controller", "https://localhost", None, "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["awx", "api/controller", "https://localhost", None, "jobs/209", "https://localhost/api/controller/v2/jobs/209/"],
        ["awx", "api/controller", "https://localhost", None, "organizations", "https://localhost/api/controller/v2/organizations/"],
        ["awx", "api/controller", "https://localhost", "controller", "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["awx", "api/controller", "https://localhost", "controller", "jobs/1", "https://localhost/api/controller/v2/jobs/1/"],
        ["awx", "api/controller", "https://localhost", "gateway", "tokens", "https://localhost/api/gateway/v1/tokens/"],
        ["awx", "api/controller", "https://localhost", "gateway", "tokens/199", "https://localhost/api/gateway/v1/tokens/199/"],
        ["controller", "api/controller", "https://localhost", None, "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["controller", "api/controller", "https://localhost", None, "jobs/209", "https://localhost/api/controller/v2/jobs/209/"],
        ["controller", "api/controller", "https://localhost", "controller", "jobs", "https://localhost/api/controller/v2/jobs/"],
        ["controller", "api/controller", "https://localhost", "controller", "jobs/1", "https://localhost/api/controller/v2/jobs/1/"],
        ["controller", "api/controller", "https://localhost", "gateway", "tokens", "https://localhost/api/gateway/v1/tokens/"],
        ["controller", "api/controller", "https://localhost", "gateway", "tokens/199", "https://localhost/api/gateway/v1/tokens/199/"],
    ]
)
def test_controller_api_build_url(collection_import, collection_type, env_prefix, controller_host, app_key, endpoint, expected):
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    controller_api = controller_api_class(argument_spec={}, direct_params=dict(controller_host=controller_host))
    controller_api._COLLECTION_TYPE = collection_type
    if env_prefix:
        with mock.patch.dict(os.environ, {"CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX": env_prefix}):
            request_url = controller_api.build_url(endpoint, app_key=app_key).geturl()
    else:
        request_url = controller_api.build_url(endpoint, app_key=app_key).geturl()

    assert request_url == expected
