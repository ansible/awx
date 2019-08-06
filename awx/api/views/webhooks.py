from hashlib import sha1
import hmac

from django.utils.encoding import force_bytes
from rest_framework.exceptions import PermissionDenied

from awx.api.generics import APIView


class WebhookReceiverBase(APIView):
    def get_object(self):
        queryset = self.queryset.filter(webhook_service=self.service)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        obj = queryset.filter(**filter_kwargs).first()
        if obj is None:
            raise PermissionDenied

        return obj

    def get_event_type(self):
        raise NotImplementedError

    def get_event_guid(self):
        raise NotImplementedError

    def get_signature(self):
        raise NotImplementedError

    def check_signature(self, obj):
        mac = hmac.new(force_bytes(obj.webhook_key), msg=force_bytes(self.request.body), digestmod=sha1)
        if not hmac.compare_digest(force_bytes(mac.hexdigest()), self.get_signature()):
            raise PermissionDenied

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_signature(obj)


class GithubWebhookReceiver(WebhookReceiverBase):
    service = 'github'

    def get_event_type(self):
        return self.request.META.get('HTTP_X_GITHUB_EVENT')

    def get_event_guid(self):
        return self.request.META.get('HTTP_X_GITHUB_DELIVERY')

    def get_signature(self):
        header_sig = self.request.META.get('HTTP_X_HUB_SIGNATURE')
        if not header_sig:
            raise PermissionDenied
        hash_alg, signature = header_sig.split('=')
        if hash_alg != 'sha1':
            raise PermissionDenied
        return force_bytes(signature)


class GitlabWebhookReceiver(WebhookReceiverBase):
    service = 'gitlab'

    def get_event_type(self):
        return self.request.META.get('HTTP_X_GITLAB_EVENT')

    def get_event_guid(self):
        # Gitlab does not provide a unique identifier on events.
        return ''

    def get_signature(self):
        return self.request.META.get('HTTP_X_GITLAB_TOKEN')

    def check_signature(self, obj):
        # Gitlab only returns the secret token, not an hmac hash

        # Use the hmac `compare_digest` helper function to prevent timing analysis by attackers.
        if not hmac.compare_digest(force_bytes(obj.webhook_key), self.get_signature()):
            raise PermissionDenied


class BitbucketWebhookReceiver(WebhookReceiverBase):
    service = 'bitbucket'

    def get_event_type(self):
        return self.request.META.get('HTTP_X_EVENT_KEY')

    def get_event_guid(self):
        return self.request.META.get('HTTP_X_REQUEST_UUID')

    def get_signature(self):
        header_sig = self.request.META.get('HTTP_X_HUB_SIGNATURE')
        if not header_sig:
            raise PermissionDenied
        return force_bytes(header_sig)
