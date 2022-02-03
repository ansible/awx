# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.sso.views import sso_complete, sso_error, sso_inactive, saml_metadata


app_name = 'sso'
urlpatterns = [
    re_path(r'^complete/$', sso_complete, name='sso_complete'),
    re_path(r'^error/$', sso_error, name='sso_error'),
    re_path(r'^inactive/$', sso_inactive, name='sso_inactive'),
    re_path(r'^metadata/saml/$', saml_metadata, name='saml_metadata'),
]
