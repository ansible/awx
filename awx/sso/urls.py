# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'awx.sso.views',
    url(r'^complete/$', 'sso_complete', name='sso_complete'),
    url(r'^error/$', 'sso_error', name='sso_error'),
    url(r'^inactive/$', 'sso_inactive', name='sso_inactive'),
    url(r'^metadata/saml/$', 'saml_metadata', name='saml_metadata'),
)
