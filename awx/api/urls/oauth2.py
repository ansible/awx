# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    OAuth2ApplicationList,
    OAuth2ApplicationDetail,
    ApplicationOAuth2TokenList,
    OAuth2ApplicationActivityStreamList,
    OAuth2TokenList,
    OAuth2TokenDetail,
    OAuth2TokenActivityStreamList,
)


urls = [
    url(r'^applications/$', OAuth2ApplicationList.as_view(), name='o_auth2_application_list'),
    url(
        r'^applications/(?P<pk>[0-9]+)/$',
        OAuth2ApplicationDetail.as_view(),
        name='o_auth2_application_detail'
    ),
    url(
        r'^applications/(?P<pk>[0-9]+)/tokens/$',
        ApplicationOAuth2TokenList.as_view(),
        name='o_auth2_application_token_list'
    ),
    url(
        r'^applications/(?P<pk>[0-9]+)/activity_stream/$',
        OAuth2ApplicationActivityStreamList.as_view(),
        name='o_auth2_application_activity_stream_list'
    ),
    url(r'^tokens/$', OAuth2TokenList.as_view(), name='o_auth2_token_list'),
    url(
        r'^tokens/(?P<pk>[0-9]+)/$',
        OAuth2TokenDetail.as_view(),
        name='o_auth2_token_detail'
    ),
    url(
        r'^tokens/(?P<pk>[0-9]+)/activity_stream/$',
        OAuth2TokenActivityStreamList.as_view(),
        name='o_auth2_token_activity_stream_list'
    ),   
]

__all__ = ['urls']
