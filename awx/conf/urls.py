# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.conf.urls import patterns

# Tower
from awx.api.urls import url


urlpatterns = patterns(
    'awx.conf.views',
    url(r'^$', 'setting_category_list'),
    url(r'^(?P<category_slug>[a-z0-9-]+)/$', 'setting_singleton_detail'),
    url(r'^logging/test/$', 'setting_logging_test'),
)
