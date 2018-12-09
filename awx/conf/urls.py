# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.


from django.conf.urls import url
from awx.conf.views import (
    SettingCategoryList,
    SettingSingletonDetail,
    SettingLoggingTest,
)


urlpatterns = [ 
    url(r'^$', SettingCategoryList.as_view(), name='setting_category_list'),
    url(r'^(?P<category_slug>[a-z0-9-]+)/$', SettingSingletonDetail.as_view(), name='setting_singleton_detail'),
    url(r'^logging/test/$', SettingLoggingTest.as_view(), name='setting_logging_test'),
]
