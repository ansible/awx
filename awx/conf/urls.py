# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.conf.views import SettingCategoryList, SettingSingletonDetail, SettingLoggingTest


urlpatterns = [
    re_path(r'^$', SettingCategoryList.as_view(), name='setting_category_list'),
    re_path(r'^(?P<category_slug>[a-z0-9-]+)/$', SettingSingletonDetail.as_view(), name='setting_singleton_detail'),
    re_path(r'^logging/test/$', SettingLoggingTest.as_view(), name='setting_logging_test'),
]
