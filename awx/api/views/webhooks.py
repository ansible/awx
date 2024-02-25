from hashlib import sha1, sha256
import hmac
import logging
import urllib.parse

from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from awx.api import serializers
from awx.api.generics import APIView, GenericAPIView
from awx.api.permissions import WebhookKeyPermission
from awx.main.models import Job, JobTemplate, WorkflowJob, WorkflowJobTemplate
from awx.main.constants import JOB_VARIABLE_PREFIXES

logger = logging.getLogger('awx.api.views.webhooks')


class WebhookKeyView(GenericAPIView):
    serializer_class = serializers.EmptySerializer
    permission_classes = (WebhookKeyPermission,)

    def get_queryset(self):
        qs_models = {'job_templates': JobTemplate, 'workflow_job_templates': WorkflowJobTemplate}
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
        qs_models = {'job_templates': JobTemplate, 'workflow_job_templates': WorkflowJobTemplate}
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

    def must_check_signature(self):
        return True

    def is_ignored_request(self):
        return False

    def check_signature(self, obj):
        if not obj.webhook_key:
            raise PermissionDenied
        if not self.must_check_signature():
            logger.debug("skipping signature validation")
            return

        hash_alg, expected_digest = self.get_signature()
        if hash_alg == 'sha1':
            mac = hmac.new(force_bytes(obj.webhook_key), msg=force_bytes(self.request.body), digestmod=sha1)
        elif hash_alg == 'sha256':
            mac = hmac.new(force_bytes(obj.webhook_key), msg=force_bytes(self.request.body), digestmod=sha256)
        else:
            logger.debug("Unsupported signature type, supported: sha1, sha256, received: {}".format(hash_alg))
            raise PermissionDenied

        logger.debug("header signature: %s", expected_digest)
        logger.debug("calculated signature: %s", force_bytes(mac.hexdigest()))
        if not hmac.compare_digest(force_bytes(mac.hexdigest()), expected_digest):
            raise PermissionDenied

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        # Ensure that the full contents of the request are captured for multiple uses.
        request.body

        logger.debug("headers: {}\ndata: {}\n".format(request.headers, request.data))
        obj = self.get_object()
        self.check_signature(obj)

        if self.is_ignored_request():
            # This was an ignored request type (e.g. ping), don't act on it
            return Response({'message': _("Webhook ignored")}, status=status.HTTP_200_OK)

        event_type = self.get_event_type()
        event_guid = self.get_event_guid()
        event_ref = self.get_event_ref()
        status_api = self.get_event_status_api()

        kwargs = {'unified_job_template_id': obj.id, 'webhook_service': obj.webhook_service, 'webhook_guid': event_guid}
        if WorkflowJob.objects.filter(**kwargs).exists() or Job.objects.filter(**kwargs).exists():
            # Short circuit if this webhook has already been received and acted upon.
            logger.debug("Webhook previously received, returning without action.")
            return Response({'message': _("Webhook previously received, aborting.")}, status=status.HTTP_202_ACCEPTED)

        kwargs = {
            '_eager_fields': {
                'launch_type': 'webhook',
                'webhook_service': obj.webhook_service,
                'webhook_credential': obj.webhook_credential,
                'webhook_guid': event_guid,
            },
            'extra_vars': {},
        }

        for name in JOB_VARIABLE_PREFIXES:
            kwargs['extra_vars']['{}_webhook_event_type'.format(name)] = event_type
            kwargs['extra_vars']['{}_webhook_event_guid'.format(name)] = event_guid
            kwargs['extra_vars']['{}_webhook_event_ref'.format(name)] = event_ref
            kwargs['extra_vars']['{}_webhook_status_api'.format(name)] = status_api
            kwargs['extra_vars']['{}_webhook_payload'.format(name)] = request.data

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
        return hash_alg, force_bytes(signature)


class GitlabWebhookReceiver(WebhookReceiverBase):
    service = 'gitlab'

    ref_keys = {'Push Hook': 'checkout_sha', 'Tag Push Hook': 'checkout_sha', 'Merge Request Hook': 'object_attributes.last_commit.id'}

    def get_event_type(self):
        return self.request.META.get('HTTP_X_GITLAB_EVENT')

    def get_event_guid(self):
        # GitLab does not provide a unique identifier on events, so construct one.
        h = sha1()
        h.update(force_bytes(self.request.body))
        return h.hexdigest()

    def get_event_status_api(self):
        if self.get_event_type() not in self.ref_keys.keys():
            return
        project = self.request.data.get('project', {})
        repo_url = project.get('web_url')
        if not repo_url:
            return
        parsed = urllib.parse.urlparse(repo_url)

        return "{}://{}/api/v4/projects/{}/statuses/{}".format(parsed.scheme, parsed.netloc, project['id'], self.get_event_ref())

    def check_signature(self, obj):
        if not obj.webhook_key:
            raise PermissionDenied

        token_from_request = force_bytes(self.request.META.get('HTTP_X_GITLAB_TOKEN') or '')

        # GitLab only returns the secret token, not an hmac hash.  Use
        # the hmac `compare_digest` helper function to prevent timing
        # analysis by attackers.
        if not hmac.compare_digest(force_bytes(obj.webhook_key), token_from_request):
            raise PermissionDenied


class BitbucketDcWebhookReceiver(WebhookReceiverBase):
    service = 'bitbucket_dc'

    ref_keys = {
        'repo:refs_changed': 'changes.0.toHash',
        'mirror:repo_synchronized': 'changes.0.toHash',
        'pr:opened': 'pullRequest.toRef.latestCommit',
        'pr:from_ref_updated': 'pullRequest.toRef.latestCommit',
        'pr:modified': 'pullRequest.toRef.latestCommit',
    }

    def get_event_type(self):
        return self.request.META.get('HTTP_X_EVENT_KEY')

    def get_event_guid(self):
        return self.request.META.get('HTTP_X_REQUEST_ID')

    def get_event_status_api(self):
        # https://<bitbucket-base-url>/rest/build-status/1.0/commits/<commit-hash>
        if self.get_event_type() not in self.ref_keys.keys():
            return
        if self.get_event_ref() is None:
            return
        any_url = None
        if 'actor' in self.request.data:
            any_url = self.request.data['actor'].get('links', {}).get('self')
        if any_url is None and 'repository' in self.request.data:
            any_url = self.request.data['repository'].get('links', {}).get('self')
        if any_url is None:
            return
        any_url = any_url[0].get('href')
        if any_url is None:
            return
        parsed = urllib.parse.urlparse(any_url)

        return "{}://{}/rest/build-status/1.0/commits/{}".format(parsed.scheme, parsed.netloc, self.get_event_ref())

    def is_ignored_request(self):
        return self.get_event_type() not in [
            'repo:refs_changed',
            'mirror:repo_synchronized',
            'pr:opened',
            'pr:from_ref_updated',
            'pr:modified',
        ]

    def must_check_signature(self):
        # Bitbucket does not sign ping requests...
        return self.get_event_type() != 'diagnostics:ping'

    def get_signature(self):
        header_sig = self.request.META.get('HTTP_X_HUB_SIGNATURE')
        if not header_sig:
            logger.debug("Expected signature missing from header key HTTP_X_HUB_SIGNATURE")
            raise PermissionDenied
        hash_alg, signature = header_sig.split('=')
        return hash_alg, force_bytes(signature)
