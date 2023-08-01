from django.urls import re_path

from awx.api.views.root import (
    ApiV2ConfigView,
    ApiV2SubscriptionView,
    ApiV2AttachView,
)


extend_urls = [
    re_path(r'^config/$', ApiV2ConfigView.as_view(), name='api_v2_config_view'),
    re_path(r'^config/subscriptions/$', ApiV2SubscriptionView.as_view(), name='api_v2_subscription_view'),
    re_path(r'^config/attach/$', ApiV2AttachView.as_view(), name='api_v2_attach_view'),
]
