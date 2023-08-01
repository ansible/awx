# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from __future__ import absolute_import, unicode_literals
import importlib
from os.path import dirname
from pkgutil import iter_modules
import logging

from django.urls import include, re_path

from awx.api.views.root import (
    ApiRootView,
    ApiV2RootView,
)
from awx.api.urls import api_v2, api_root

logger = logging.getLogger('awx.urls')


def extend_urls(urls, base_module):
    urls_dir = dirname(base_module.__file__)
    for _, module_name, _ in iter_modules([urls_dir]):
        if module_name == '__init__':
            continue
        fully_qualified_module = f'{base_module.__name__}.{module_name}'
        url_module = importlib.import_module(fully_qualified_module)
        imported_something = False
        if hasattr(url_module, 'urls'):
            entry_point = r'^{}/'.format(module_name)
            if hasattr(url_module, 'entry_point'):
                entry_point = url_module.entry_point
            urls.append(re_path(entry_point, include(url_module.urls)))
            imported_something = True
        if hasattr(url_module, 'extend_urls'):
            urls.extend(url_module.extend_urls)
            imported_something = True

        if not imported_something:
            logger.error(f"Not loading {fully_qualified_module} missing urls or extend_urls")


v2_urls = [
    re_path(r'^$', ApiV2RootView.as_view(), name='api_v2_root_view'),
]
extend_urls(v2_urls, api_v2)

urlpatterns = [
    re_path(r'^$', ApiRootView.as_view(), name='api_root_view'),
    re_path(r'^(?P<version>(v2))/', include(v2_urls)),
]
extend_urls(urlpatterns, api_root)
