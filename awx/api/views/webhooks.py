from hashlib import sha1
import hmac
import logging
import urllib.parse

from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from awx.api import serializers
from awx.api.generics import APIView, GenericAPIView
from awx.api.permissions import WebhookKeyPermission
from awx.main.models import Job, JobTemplate, WorkflowJob, WorkflowJobTemplate


logger = logging.getLogger('awx.api.views.webhooks')


class WebhookKeyView(GenericAPIView):
    serializer_class = serializers.EmptySerializer
    permission_classes = (WebhookKeyPermission,)

    def get_queryset(self):
        qs_models = {
            'job_templates': JobTemplate,
            'workflow_job_templates': WorkflowJobTemplate,
        }
        self.model = qs_models.get(self.kwargs['model_kwarg'])

        return super().get_queryset()

    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        return Response({'webhook_key': obj.webhook_key})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.rotate_webhook_key()
        obj.save(update_fields=['webhook_key'])

        return Response({'webhook_key': obj.webhook_key}, status=status.HTTP_201_CREATED)


class WebhookReceiverBase(APIView):
    lookup_url_kwarg = None
    lookup_field = 'pk'

    permission_classes = (AllowAny,)
    authentication_classes = ()

    ref_keys = {}

    def get_queryset(self):
        qs_models = {
            'job_templates': JobTemplate,
            'workflow_job_templates': WorkflowJobTemplate,
        }
        model = qs_models.get(self.kwargs['model_kwarg'])
        if model is None:
            raise PermissionDenied

        return model.objects.filter(webhook_service=self.service).exclude(webhook_key='')

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

    def get_event_status_api(self):
        raise NotImplementedError

    def get_event_ref(self):
        key = self.ref_keys.get(self.get_event_type(), '')
        value = self.request.data
        for element in key.split('.'):
            try:
                if element.isdigit():
                    value = value[int(element)]
                else:
                    value = (value or {}).get(element)
            except Exception:
                value = None
        if value == '0000000000000000000000000000000000000000':  # a deleted ref
            value = None
        return value

    def get_signature(self):
        raise NotImplementedError

    def check_signature(self, obj):
        if not obj.webhook_key:
            raise PermissionDenied

        mac = hmac.new(force_bytes(obj.webhook_key), msg=force_bytes(self.request.body), digestmod=sha1)
        logger.debug("header signature: %s", self.get_signature())
        logger.debug("calculated signature: %s", force_bytes(mac.hexdigest()))
        if not hmac.compare_digest(force_bytes(mac.hexdigest()), self.get_signature()):
            raise PermissionDenied

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        # Ensure that the full contents of the request are captured for multiple uses.
        request.body

        logger.debug(
            "headers: {}\n"
            "data: {}\n".format(request.headers, request.data)
        )
        obj = self.get_object()
        self.check_signature(obj)

        event_type = self.get_event_type()
        event_guid = self.get_event_guid()
        event_ref = self.get_event_ref()
        status_api = self.get_event_status_api()

        kwargs = {
            'unified_job_template_id': obj.id,
            'webhook_service': obj.webhook_service,
            'webhook_guid': event_guid,
        }
        if WorkflowJob.objects.filter(**kwargs).exists() or Job.objects.filter(**kwargs).exists():
            # Short circuit if this webhook has already been received and acted upon.
            logger.debug("Webhook previously received, returning without action.")
            return Response({'message': _("Webhook previously received, aborting.")},
                            status=status.HTTP_202_ACCEPTED)

        kwargs = {
            '_eager_fields': {
                'launch_type': 'webhook',
                'webhook_service': obj.webhook_service,
                'webhook_credential': obj.webhook_credential,
                'webhook_guid': event_guid,
            },
            'extra_vars': {
                'tower_webhook_event_type': event_type,
                'tower_webhook_event_guid': event_guid,
                'tower_webhook_event_ref': event_ref,
                'tower_webhook_status_api': status_api,
                'tower_webhook_payload': request.data,
            }
        }

        new_job = obj.create_unified_job(**kwargs)
        new_job.signal_start()

        return Response({'message': "Job queued."}, status=status.HTTP_202_ACCEPTED)


class GithubWebhookReceiver(WebhookReceiverBase):
    service = 'github'

    ref_keys = {
        'pull_request': 'pull_request.head.sha',
        'pull_request_review': 'pull_request.head.sha',
        'pull_request_review_comment': 'pull_request.head.sha',
        'push': 'after',
        'release': 'release.tag_name',
        'commit_comment': 'comment.commit_id',
        'create': 'ref',
        'page_build': 'build.commit',
    }

    def get_event_type(self):
        return self.request.META.get('HTTP_X_GITHUB_EVENT')

    def get_event_guid(self):
        return self.request.META.get('HTTP_X_GITHUB_DELIVERY')

    def get_event_status_api(self):
        if self.get_event_type() != 'pull_request':
            return
        return self.request.data.get('pull_request', {}).get('statuses_url')

    def get_signature(self):
        header_sig = self.request.META.get('HTTP_X_HUB_SIGNATURE')
        if not header_sig:
            logger.debug("Expected signature missing from header key HTTP_X_HUB_SIGNATURE")
            raise PermissionDenied
        hash_alg, signature = header_sig.split('=')
        if hash_alg != 'sha1':
            logger.debug("Unsupported signature type, expected: sha1, received: {}".format(hash_alg))
            raise PermissionDenied
        return force_bytes(signature)


class GitlabWebhookReceiver(WebhookReceiverBase):
    service = 'gitlab'

    ref_keys = {
        'Push Hook': 'checkout_sha',
        'Tag Push Hook': 'checkout_sha',
        'Merge Request Hook': 'object_attributes.last_commit.id',
    }

    def get_event_type(self):
        return self.request.META.get('HTTP_X_GITLAB_EVENT')

    def get_event_guid(self):
        # GitLab does not provide a unique identifier on events, so construct one.
        h = sha1()
        h.update(force_bytes(self.request.body))
        return h.hexdigest()

    def get_event_status_api(self):
        if self.get_event_type() != 'Merge Request Hook':
            return
        project = self.request.data.get('project', {})
        repo_url = project.get('web_url')
        if not repo_url:
            return
        parsed = urllib.parse.urlparse(repo_url)

        return "{}://{}/api/v4/projects/{}/statuses/{}".format(
            parsed.scheme, parsed.netloc, project['id'], self.get_event_ref())

    def get_signature(self):
        return force_bytes(self.request.META.get('HTTP_X_GITLAB_TOKEN') or '')

    def check_signature(self, obj):
        if not obj.webhook_key:
            raise PermissionDenied

        # GitLab only returns the secret token, not an hmac hash.  Use
        # the hmac `compare_digest` helper function to prevent timing
        # analysis by attackers.
        if not hmac.compare_digest(force_bytes(obj.webhook_key), self.get_signature()):
            raise PermissionDenied
