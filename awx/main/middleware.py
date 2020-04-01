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
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.shortcuts import get_object_or_404, redirect
from django.apps import apps
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse, resolve

from awx.main.utils.named_url_graph import generate_graph, GraphNode
from awx.conf import fields, register


logger = logging.getLogger('awx.main.middleware')
perf_logger = logging.getLogger('awx.analytics.performance')


class TimingMiddleware(threading.local, MiddlewareMixin):

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

        if settings.AWX_REQUEST_PROFILE_WITH_DOT:
            from gprof2dot import main as generate_dot
            raw = os.path.join(self.dest, filename) + '.raw'
            pstats.Stats(self.prof).dump_stats(raw)
            generate_dot([
                '-n', '2.5', '-f', 'pstats', '-o',
                os.path.join( self.dest, filename).replace('.pstats', '.dot'),
                raw
            ])
            os.remove(raw)
        return filepath


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Resets the session timeout for both the UI and the actual session for the API
    to the value of SESSION_COOKIE_AGE on every request if there is a valid session.
    """

    def process_response(self, request, response):
        should_skip = 'HTTP_X_WS_SESSION_QUIET' in request.META
        # Something went wrong, such as upgrade-in-progress page
        if not hasattr(request, 'session'):
            return response
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


class URLModificationMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
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
        super().__init__(get_response)

    @staticmethod
    def _hijack_for_old_jt_name(node, kwargs, named_url):
        try:
            int(named_url)
            return False
        except ValueError:
            pass
        JobTemplate = node.model
        name = urllib.parse.unquote(named_url)
        return JobTemplate.objects.filter(name=name).order_by('organization__created').first()

    @classmethod
    def _named_url_to_pk(cls, node, resource, named_url):
        kwargs = {}
        if node.populate_named_url_query_kwargs(kwargs, named_url):
            return str(get_object_or_404(node.model, **kwargs).pk)
        if resource == 'job_templates' and '++' not in named_url:
            # special case for deprecated job template case
            # will not raise a 404 on its own
            jt = cls._hijack_for_old_jt_name(node, kwargs, named_url)
            if jt:
                return str(jt.pk)
        return named_url

    @classmethod
    def _convert_named_url(cls, url_path):
        url_units = url_path.split('/')
        # If the identifier is an empty string, it is always invalid.
        if len(url_units) < 6 or url_units[1] != 'api' or url_units[2] not in ['v2'] or not url_units[4]:
            return url_path
        resource = url_units[3]
        if resource in settings.NAMED_URL_MAPPINGS:
            url_units[4] = cls._named_url_to_pk(
                settings.NAMED_URL_GRAPH[settings.NAMED_URL_MAPPINGS[resource]],
                resource, url_units[4])
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


class MigrationRanCheckMiddleware(MiddlewareMixin):

    def process_request(self, request):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if bool(plan) and \
                getattr(resolve(request.path), 'url_name', '') != 'migrations_notran':
            return redirect(reverse("ui:migrations_notran"))
