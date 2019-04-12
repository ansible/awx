# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import uuid
import logging
import threading
import time
import cProfile
import pstats
import os
import urllib.parse

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.migrations.executor import MigrationExecutor
from django.db import IntegrityError, connection
from django.utils.functional import curry
from django.shortcuts import get_object_or_404, redirect
from django.apps import apps
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse, resolve

from awx.main.models import ActivityStream
from awx.main.utils.named_url_graph import generate_graph, GraphNode
from awx.conf import fields, register


logger = logging.getLogger('awx.main.middleware')
analytics_logger = logging.getLogger('awx.analytics.activity_stream')
perf_logger = logging.getLogger('awx.analytics.performance')


class TimingMiddleware(threading.local):

    dest = '/var/log/tower/profile'

    def process_request(self, request):
        self.start_time = time.time()
        if settings.AWX_REQUEST_PROFILE:
            self.prof = cProfile.Profile()
            self.prof.enable()

    def process_response(self, request, response):
        if not hasattr(self, 'start_time'):  # some tools may not invoke process_request
            return response
        total_time = time.time() - self.start_time
        response['X-API-Total-Time'] = '%0.3fs' % total_time
        if settings.AWX_REQUEST_PROFILE:
            self.prof.disable()
            cprofile_file = self.save_profile_file(request)
            response['cprofile_file'] = cprofile_file
        perf_logger.info('api response times', extra=dict(python_objects=dict(request=request, response=response)))
        return response

    def save_profile_file(self, request):
        if not os.path.isdir(self.dest):
            os.makedirs(self.dest)
        filename = '%.3fs-%s.pstats' % (pstats.Stats(self.prof).total_tt, uuid.uuid4())
        filepath = os.path.join(self.dest, filename)
        with open(filepath, 'w') as f:
            f.write('%s %s\n' % (request.method, request.get_full_path()))
            pstats.Stats(self.prof, stream=f).sort_stats('cumulative').print_stats()
        return filepath


class ActivityStreamMiddleware(threading.local):

    def __init__(self):
        self.disp_uid = None
        self.instance_ids = []

    def process_request(self, request):
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        set_actor = curry(self.set_actor, user)
        self.disp_uid = str(uuid.uuid1())
        self.instance_ids = []
        post_save.connect(set_actor, sender=ActivityStream, dispatch_uid=self.disp_uid, weak=False)

    def process_response(self, request, response):
        drf_request = getattr(request, 'drf_request', None)
        drf_user = getattr(drf_request, 'user', None)
        if self.disp_uid is not None:
            post_save.disconnect(dispatch_uid=self.disp_uid)

        for instance in ActivityStream.objects.filter(id__in=self.instance_ids):
            if drf_user and drf_user.id:
                instance.actor = drf_user
                try:
                    instance.save(update_fields=['actor'])
                    analytics_logger.info('Activity Stream update entry for %s' % str(instance.object1),
                                          extra=dict(changes=instance.changes, relationship=instance.object_relationship_type,
                                          actor=drf_user.username, operation=instance.operation,
                                          object1=instance.object1, object2=instance.object2))
                except IntegrityError:
                    logger.debug("Integrity Error saving Activity Stream instance for id : " + str(instance.id))
            # else:
            #     obj1_type_actual = instance.object1_type.split(".")[-1]
            #     if obj1_type_actual in ("InventoryUpdate", "ProjectUpdate", "Job") and instance.id is not None:
            #         instance.delete()

        self.instance_ids = []
        return response

    def set_actor(self, user, sender, instance, **kwargs):
        if sender == ActivityStream:
            if isinstance(user, User) and instance.actor is None:
                user = User.objects.filter(id=user.id)
                if user.exists():
                    user = user[0]
                    instance.actor = user
            else:
                if instance.id not in self.instance_ids:
                    self.instance_ids.append(instance.id)


class SessionTimeoutMiddleware(object):
    """
    Resets the session timeout for both the UI and the actual session for the API
    to the value of SESSION_COOKIE_AGE on every request if there is a valid session.
    """

    def process_response(self, request, response):
        should_skip = 'HTTP_X_WS_SESSION_QUIET' in request.META
        # Only update the session if it hasn't been flushed by being forced to log out.
        if request.session and not request.session.is_empty() and not should_skip:
            expiry = int(settings.SESSION_COOKIE_AGE)
            request.session.set_expiry(expiry)
            response['Session-Timeout'] = expiry
        return response


def _customize_graph():
    from awx.main.models import Instance, Schedule, UnifiedJobTemplate
    for model in [Schedule, UnifiedJobTemplate]:
        if model in settings.NAMED_URL_GRAPH:
            settings.NAMED_URL_GRAPH[model].remove_bindings()
            settings.NAMED_URL_GRAPH.pop(model)
    if User not in settings.NAMED_URL_GRAPH:
        settings.NAMED_URL_GRAPH[User] = GraphNode(User, ['username'], [])
        settings.NAMED_URL_GRAPH[User].add_bindings()
    if Instance not in settings.NAMED_URL_GRAPH:
        settings.NAMED_URL_GRAPH[Instance] = GraphNode(Instance, ['hostname'], [])
        settings.NAMED_URL_GRAPH[Instance].add_bindings()


class URLModificationMiddleware(object):

    def __init__(self):
        models = [m for m in apps.get_app_config('main').get_models() if hasattr(m, 'get_absolute_url')]
        generate_graph(models)
        _customize_graph()
        register(
            'NAMED_URL_FORMATS',
            field_class=fields.DictField,
            read_only=True,
            label=_('Formats of all available named urls'),
            help_text=_('Read-only list of key-value pairs that shows the standard format of all '
                        'available named URLs.'),
            category=_('Named URL'),
            category_slug='named-url',
        )
        register(
            'NAMED_URL_GRAPH_NODES',
            field_class=fields.DictField,
            read_only=True,
            label=_('List of all named url graph nodes.'),
            help_text=_('Read-only list of key-value pairs that exposes named URL graph topology.'
                        ' Use this list to programmatically generate named URLs for resources'),
            category=_('Named URL'),
            category_slug='named-url',
        )

    def _named_url_to_pk(self, node, named_url):
        kwargs = {}
        if not node.populate_named_url_query_kwargs(kwargs, named_url):
            return named_url
        return str(get_object_or_404(node.model, **kwargs).pk)

    def _convert_named_url(self, url_path):
        url_units = url_path.split('/')
        # If the identifier is an empty string, it is always invalid.
        if len(url_units) < 6 or url_units[1] != 'api' or url_units[2] not in ['v2'] or not url_units[4]:
            return url_path
        resource = url_units[3]
        if resource in settings.NAMED_URL_MAPPINGS:
            url_units[4] = self._named_url_to_pk(settings.NAMED_URL_GRAPH[settings.NAMED_URL_MAPPINGS[resource]],
                                                 url_units[4])
        return '/'.join(url_units)

    def process_request(self, request):
        if hasattr(request, 'environ') and 'REQUEST_URI' in request.environ:
            old_path = urllib.parse.urlsplit(request.environ['REQUEST_URI']).path
            old_path = old_path[request.path.find(request.path_info):]
        else:
            old_path = request.path_info
        new_path = self._convert_named_url(old_path)
        if request.path_info != new_path:
            request.path = request.path.replace(request.path_info, new_path)
            request.path_info = new_path


class MigrationRanCheckMiddleware(object):

    def process_request(self, request):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if bool(plan) and \
                getattr(resolve(request.path), 'url_name', '') != 'migrations_notran':
            return redirect(reverse("ui:migrations_notran"))
