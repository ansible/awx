from hashlib import sha1
import hmac

from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from awx.api import serializers
from awx.api.generics import APIView, GenericAPIView
from awx.main.models import JobTemplate, WorkflowJobTemplate


class WebhookKeyView(GenericAPIView):
    serializer_class = serializers.EmptySerializer

    @property
    def model(self):
        qs_models = {
            'job_templates': JobTemplate,
            'workflow_job_templates': WorkflowJobTemplate,
        }
        model = qs_models.get(self.kwargs['model_kwarg'])
        if model is None:
            raise PermissionDenied

        return model

    def get_queryset(self):
        return self.request.user.get_queryset(self.model)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        return Response({'webhook_key': obj.webhook_key})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.rotate_webhook_key()

        return Response({'webhook_key': obj.webhook_key}, status=status.HTTP_201_CREATED)


class WebhookReceiverBase(APIView):
    lookup_url_kwarg = None
    lookup_field = 'pk'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        qs_models = {
            'job_templates': JobTemplate,
            'workflow_job_templates': WorkflowJobTemplate,
        }
        model = qs_models.get(self.kwargs['model_kwarg'])
        if model is None:
            raise PermissionDenied

        return model.objects.filter(webhook_service=self.service)

    def get_object(self):
        queryset = self.get_queryset()
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
        if not obj.webhook_key:
            raise PermissionDenied

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
        if not obj.webhook_key:
            raise PermissionDenied

        # Gitlab only returns the secret token, not an hmac hash.  Use
        # the hmac `compare_digest` helper function to prevent timing
        # analysis by attackers.
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
