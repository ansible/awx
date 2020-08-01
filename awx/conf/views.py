# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import collections
import logging
import subprocess
import sys
import socket
from socket import SHUT_RDWR

# Django
from django.db import connection
from django.conf import settings
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status

# Tower
from awx.api.generics import (
    APIView,
    GenericAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from awx.api.permissions import IsSuperUser
from awx.api.versioning import reverse
from awx.main.utils import camelcase_to_underscore
from awx.main.tasks import handle_setting_changes
from awx.conf.models import Setting
from awx.conf.serializers import SettingCategorySerializer, SettingSingletonSerializer
from awx.conf import settings_registry


SettingCategory = collections.namedtuple('SettingCategory', ('url', 'slug', 'name'))


class SettingCategoryList(ListAPIView):

    model = Setting  # Not exactly, but needed for the view.
    serializer_class = SettingCategorySerializer
    filter_backends = []
    name = _('Setting Categories')

    def get_queryset(self):
        setting_categories = []
        categories = settings_registry.get_registered_categories()
        if self.request.user.is_superuser or self.request.user.is_system_auditor:
            pass  # categories = categories
        elif 'user' in categories:
            categories = {'user', _('User')}
        else:
            categories = {}
        for category_slug in sorted(categories.keys()):
            url = reverse('api:setting_singleton_detail', kwargs={'category_slug': category_slug}, request=self.request)
            setting_categories.append(SettingCategory(url, category_slug, categories[category_slug]))
        return setting_categories


class SettingSingletonDetail(RetrieveUpdateDestroyAPIView):

    model = Setting  # Not exactly, but needed for the view.
    serializer_class = SettingSingletonSerializer
    filter_backends = []
    name = _('Setting Detail')

    def get_queryset(self):
        self.category_slug = self.kwargs.get('category_slug', 'all')
        all_category_slugs = list(settings_registry.get_registered_categories().keys())
        if self.request.user.is_superuser or getattr(self.request.user, 'is_system_auditor', False):
            category_slugs = all_category_slugs
        else:
            category_slugs = {'user'}
        if self.category_slug not in all_category_slugs:
            raise Http404
        if self.category_slug not in category_slugs:
            raise PermissionDenied()

        registered_settings = settings_registry.get_registered_settings(
            category_slug=self.category_slug, read_only=False,
        )
        if self.category_slug == 'user':
            return Setting.objects.filter(key__in=registered_settings, user=self.request.user)
        else:
            return Setting.objects.filter(key__in=registered_settings, user__isnull=True)

    def get_object(self):
        settings_qs = self.get_queryset()
        registered_settings = settings_registry.get_registered_settings(
            category_slug=self.category_slug,
        )
        all_settings = {}
        for setting in settings_qs:
            all_settings[setting.key] = setting.value
        for key in registered_settings:
            if key in all_settings or self.category_slug == 'changed':
                continue
            try:
                field = settings_registry.get_setting_field(key, for_user=bool(self.category_slug == 'user'))
                all_settings[key] = field.get_default()
            except serializers.SkipField:
                all_settings[key] = None
        all_settings['user'] = self.request.user if self.category_slug == 'user' else None
        obj = type('Settings', (object,), all_settings)()
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        settings_qs = self.get_queryset()
        user = self.request.user if self.category_slug == 'user' else None
        settings_change_list = []
        for key, value in serializer.validated_data.items():
            if key == 'LICENSE' or settings_registry.is_setting_read_only(key):
                continue
            if settings_registry.is_setting_encrypted(key) and \
                    isinstance(value, str) and \
                    value.startswith('$encrypted$'):
                continue
            setattr(serializer.instance, key, value)
            setting = settings_qs.filter(key=key).order_by('pk').first()
            if not setting:
                setting = Setting.objects.create(key=key, user=user, value=value)
                settings_change_list.append(key)
            elif setting.value != value:
                setting.value = value
                setting.save(update_fields=['value'])
                settings_change_list.append(key)
        if settings_change_list:
            connection.on_commit(lambda: handle_setting_changes.delay(settings_change_list))


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        settings_change_list = []
        for setting in self.get_queryset().exclude(key='LICENSE'):
            if settings_registry.get_setting_field(setting.key).read_only:
                continue
            setting.delete()
            settings_change_list.append(setting.key)
        if settings_change_list:
            connection.on_commit(lambda: handle_setting_changes.delay(settings_change_list))

        # When TOWER_URL_BASE is deleted from the API, reset it to the hostname
        # used to make the request as a default.
        if hasattr(instance, 'TOWER_URL_BASE'):
            url = '{}://{}'.format(self.request.scheme, self.request.get_host())
            if settings.TOWER_URL_BASE != url:
                settings.TOWER_URL_BASE = url


class SettingLoggingTest(GenericAPIView):

    name = _('Logging Connectivity Test')
    model = Setting
    serializer_class = SettingSingletonSerializer
    permission_classes = (IsSuperUser,)
    filter_backends = []

    def post(self, request, *args, **kwargs):
        # Error if logging is not enabled
        enabled = getattr(settings, 'LOG_AGGREGATOR_ENABLED', False)
        if not enabled:
            return Response({'error': 'Logging not enabled'}, status=status.HTTP_409_CONFLICT)
        
        # Send test message to configured logger based on db settings
        try:
            default_logger = settings.LOG_AGGREGATOR_LOGGERS[0]
            if default_logger != 'awx':
                default_logger = f'awx.analytics.{default_logger}'
        except IndexError:
            default_logger = 'awx'
        logging.getLogger(default_logger).error('AWX Connection Test Message')
        
        hostname = getattr(settings, 'LOG_AGGREGATOR_HOST', None)
        protocol = getattr(settings, 'LOG_AGGREGATOR_PROTOCOL', None)

        try:
            subprocess.check_output(
                ['rsyslogd', '-N1', '-f', '/var/lib/awx/rsyslog/rsyslog.conf'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as exc:
            return Response({'error': exc.output}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check to ensure port is open at host
        if protocol in ['udp', 'tcp']:
            port = getattr(settings, 'LOG_AGGREGATOR_PORT', None)
            # Error if port is not set when using UDP/TCP
            if not port:
                return Response({'error': 'Port required for ' + protocol}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # if http/https by this point, domain is reacheable
            return Response(status=status.HTTP_202_ACCEPTED)

        if protocol == 'udp':
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(.5)
            s.connect((hostname, int(port)))
            s.shutdown(SHUT_RDWR)
            s.close()
            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
for attr, value in list(locals().items()):
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
