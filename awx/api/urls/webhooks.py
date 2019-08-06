from django.conf.urls import url

from awx.api.views import (
    GithubWebhookReceiver,
    GitlabWebhookReceiver,
    BitbucketWebhookReceiver,
)


urlpatterns = [
    url(r'^github/$', GithubWebhookReceiver.as_view(), name='webhook_receiver_github'),
    url(r'^gitlab/$', GitlabWebhookReceiver.as_view(), name='webhook_receiver_gitlab'),
    url(r'^bitbucket/$', BitbucketWebhookReceiver.as_view(), name='webhook_receiver_bitbucket'),
]
