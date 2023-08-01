from django.urls import re_path

from awx.api.views import (
    OAuth2ApplicationList,
    ApplicationOAuth2TokenList,
    OAuth2ApplicationDetail,
)


extend_urls = [
    re_path(r'^applications/$', OAuth2ApplicationList.as_view(), name='o_auth2_application_list'),
    re_path(r'^applications/(?P<pk>[0-9]+)/$', OAuth2ApplicationDetail.as_view(), name='o_auth2_application_detail'),
    re_path(r'^applications/(?P<pk>[0-9]+)/tokens/$', ApplicationOAuth2TokenList.as_view(), name='application_o_auth2_token_list'),
]
