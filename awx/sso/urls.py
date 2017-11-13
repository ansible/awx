# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url
from awx.sso.views import (
    sso_complete,
    sso_error,
    sso_inactive,
    saml_metadata,
)


app_name = 'sso'
urlpatterns = [
    url(r'^complete/$', sso_complete, name='sso_complete'),
    url(r'^error/$', sso_error, name='sso_error'),
    url(r'^inactive/$', sso_inactive, name='sso_inactive'),
    url(r'^metadata/saml/$', saml_metadata, name='saml_metadata'),
]
