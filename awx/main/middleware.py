# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import functools
import logging
import threading
import time
import urllib.parse
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.contrib.auth import logout
from django.db.migrations.recorder import MigrationRecorder
from django.db import connection
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse, resolve

from awx.main import migrations
from awx.main.utils.profiling import AWXProfiler
from awx.main.utils.common import memoize
from awx.urls import get_urlpatterns
from awx.main.utils.named_url_graph import reset_counters


logger = logging.getLogger('awx.main.middleware')
perf_logger = logging.getLogger('awx.analytics.performance')


class SettingsCacheMiddleware(MiddlewareMixin):
    """
    Clears the in-memory settings cache at the beginning of a request.
    We do this so that a script can POST to /api/v2/settings/all/ and then
    right away GET /api/v2/settings/all/ and see the updated value.
    """

    def process_request(self, request):
        settings._awx_conf_memoizedcache.clear()


class TimingMiddleware(threading.local, MiddlewareMixin):
    dest = '/var/log/tower/profile'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prof = AWXProfiler("TimingMiddleware")

    def process_request(self, request):
        self.start_time = time.time()
        if settings.AWX_REQUEST_PROFILE:
            self.prof.start()

    def process_response(self, request, response):
        if not hasattr(self, 'start_time'):  # some tools may not invoke process_request
            return response
        total_time = time.time() - self.start_time
        response['X-API-Total-Time'] = '%0.3fs' % total_time
        if settings.AWX_REQUEST_PROFILE:
            response['X-API-Profile-File'] = self.prof.stop()
        perf_logger.debug(
            f'request: {request}, response_time: {response["X-API-Total-Time"]}',
            extra=dict(python_objects=dict(request=request, response=response, X_API_TOTAL_TIME=response["X-API-Total-Time"])),
        )
        return response


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


class DisableLocalAuthMiddleware(MiddlewareMixin):
    """
    Respects the presence of the DISABLE_LOCAL_AUTH setting and forces
    local-only users to logout when they make a request.
    """

    def process_request(self, request):
        if settings.DISABLE_LOCAL_AUTH:
            user = request.user
            if not user.pk:
                return

            logout(request)


class URLModificationMiddleware(MiddlewareMixin):
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
        reset_counters()
        if node.populate_named_url_query_kwargs(kwargs, named_url):
            match = node.model.objects.filter(**kwargs).first()
            if match:
                return str(match.pk)
            else:
                # if the name does *not* resolve to any actual resource,
                # we should still attempt to route it through so that 401s are
                # respected
                # using "zero" here will cause the URL regex to match e.g.,
                # /api/v2/users/<integer>/, but it also means that anonymous
                # users will go down the path of having their credentials
                # verified; in this way, *anonymous* users will that visit
                # /api/v2/users/invalid-username/ *won't* see a 404, they'll
                # see a 401 as if they'd gone to /api/v2/users/0/
                #
                return '0'
        if resource == 'job_templates' and '++' not in named_url:
            # special case for deprecated job template case
            # will not raise a 404 on its own
            jt = cls._hijack_for_old_jt_name(node, kwargs, named_url)
            if jt:
                return str(jt.pk)
        return named_url

    @classmethod
    def _convert_named_url(cls, url_path):
        default_prefix = PurePosixPath('/api/v2/')
        optional_prefix = PurePosixPath(f'/api/{settings.OPTIONAL_API_URLPATTERN_PREFIX}/v2/')

        url_path_original = url_path
        url_path = PurePosixPath(url_path)

        if set(optional_prefix.parts).issubset(set(url_path.parts)):
            url_prefix = optional_prefix
        elif set(default_prefix.parts).issubset(set(url_path.parts)):
            url_prefix = default_prefix
        else:
            return url_path_original

        # Remove prefix
        url_path = PurePosixPath(*url_path.parts[len(url_prefix.parts) :])
        try:
            resource_path = PurePosixPath(url_path.parts[0])
            name = url_path.parts[1]
            url_suffix = PurePosixPath(*url_path.parts[2:])  # remove name and resource
        except IndexError:
            return url_path_original

        resource = resource_path.parts[0]
        if resource in settings.NAMED_URL_MAPPINGS:
            pk = PurePosixPath(cls._named_url_to_pk(settings.NAMED_URL_GRAPH[settings.NAMED_URL_MAPPINGS[resource]], resource, name))
        else:
            return url_path_original

        parts = url_prefix.parts + resource_path.parts + pk.parts + url_suffix.parts
        return PurePosixPath(*parts).as_posix() + '/'

    def process_request(self, request):
        old_path = request.path_info
        new_path = self._convert_named_url(old_path)
        if request.path_info != new_path:
            request.environ['awx.named_url_rewritten'] = request.path
            request.path = request.path.replace(request.path_info, new_path)
            request.path_info = new_path


@memoize(ttl=20)
def is_migrating():
    latest_number = 0
    latest_name = ''
    for migration_path in Path(migrations.__path__[0]).glob('[0-9]*.py'):
        try:
            migration_number = int(migration_path.name.split('_', 1)[0])
        except ValueError:
            continue
        if migration_number > latest_number:
            latest_number = migration_number
            latest_name = migration_path.name[: -len('.py')]
    return not MigrationRecorder(connection).migration_qs.filter(app='main', name=latest_name).exists()


class MigrationRanCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if is_migrating() and getattr(resolve(request.path), 'url_name', '') != 'migrations_notran':
            return redirect(reverse("ui:migrations_notran"))


class OptionalURLPrefixPath(MiddlewareMixin):
    @functools.lru_cache
    def _url_optional(self, prefix):
        # Relavant Django code path https://github.com/django/django/blob/stable/4.2.x/django/core/handlers/base.py#L300
        #
        # resolve_request(request)
        #   get_resolver(request.urlconf)
        #     _get_cached_resolver(request.urlconf) <-- cached via @functools.cache
        #
        # Django will attempt to cache the value(s) of request.urlconf
        # Being hashable is a prerequisit for being cachable.
        # tuple() is hashable list() is not.
        # Hence the tuple(list()) wrap.
        return tuple(get_urlpatterns(prefix=prefix))

    def process_request(self, request):
        prefix = settings.OPTIONAL_API_URLPATTERN_PREFIX

        if request.path.startswith(f"/api/{prefix}"):
            request.urlconf = self._url_optional(prefix)
        else:
            request.urlconf = 'awx.urls'
