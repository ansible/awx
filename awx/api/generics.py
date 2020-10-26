# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import inspect
import logging
import time
import uuid
import urllib.parse

# Django
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import OneToOneRel
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import views as auth_views

# Django REST Framework
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, ParseError, NotAcceptable, UnsupportedMediaType
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework.negotiation import DefaultContentNegotiation

# AWX
from awx.api.filters import FieldLookupBackend
from awx.main.models import (
    UnifiedJob, UnifiedJobTemplate, User, Role, Credential,
    WorkflowJobTemplateNode, WorkflowApprovalTemplate
)
from awx.main.access import access_registry
from awx.main.utils import (
    camelcase_to_underscore,
    get_search_fields,
    getattrd,
    get_object_or_400,
    decrypt_field,
    get_awx_version,
)
from awx.main.utils.db import get_all_field_names
from awx.main.views import ApiErrorView
from awx.api.serializers import ResourceAccessListElementSerializer, CopySerializer, UserSerializer
from awx.api.versioning import URLPathVersioning
from awx.api.metadata import SublistAttachDetatchMetadata, Metadata

__all__ = ['APIView', 'GenericAPIView', 'ListAPIView', 'SimpleListAPIView',
           'ListCreateAPIView', 'SubListAPIView', 'SubListCreateAPIView',
           'SubListDestroyAPIView',
           'SubListCreateAttachDetachAPIView', 'RetrieveAPIView',
           'RetrieveUpdateAPIView', 'RetrieveDestroyAPIView',
           'RetrieveUpdateDestroyAPIView',
           'SubDetailAPIView',
           'ResourceAccessList',
           'ParentMixin',
           'DeleteLastUnattachLabelMixin',
           'SubListAttachDetachAPIView',
           'CopyAPIView', 'BaseUsersList',]

logger = logging.getLogger('awx.api.generics')
analytics_logger = logging.getLogger('awx.analytics.performance')


class LoggedLoginView(auth_views.LoginView):

    def get(self, request, *args, **kwargs):
        # The django.auth.contrib login form doesn't perform the content
        # negotiation we've come to expect from DRF; add in code to catch
        # situations where Accept != text/html (or */*) and reply with
        # an HTTP 406
        try:
            DefaultContentNegotiation().select_renderer(
                request,
                [StaticHTMLRenderer],
                'html'
            )
        except NotAcceptable:
            resp = Response(status=status.HTTP_406_NOT_ACCEPTABLE)
            resp.accepted_renderer = StaticHTMLRenderer()
            resp.accepted_media_type = 'text/plain'
            resp.renderer_context = {}
            return resp
        return super(LoggedLoginView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ret = super(LoggedLoginView, self).post(request, *args, **kwargs)
        current_user = getattr(request, 'user', None)
        if request.user.is_authenticated:
            logger.info(smart_text(u"User {} logged in from {}".format(self.request.user.username,request.META.get('REMOTE_ADDR', None))))
            ret.set_cookie('userLoggedIn', 'true')
            current_user = UserSerializer(self.request.user)
            current_user = smart_text(JSONRenderer().render(current_user.data))
            current_user = urllib.parse.quote('%s' % current_user, '')
            ret.set_cookie('current_user', current_user, secure=settings.SESSION_COOKIE_SECURE or None)

            return ret
        else:
            if 'username' in self.request.POST:
                logger.warn(smart_text(u"Login failed for user {} from {}".format(self.request.POST.get('username'),request.META.get('REMOTE_ADDR', None))))
            ret.status_code = 401
            return ret


class LoggedLogoutView(auth_views.LogoutView):

    def dispatch(self, request, *args, **kwargs):
        original_user = getattr(request, 'user', None)
        ret = super(LoggedLogoutView, self).dispatch(request, *args, **kwargs)
        current_user = getattr(request, 'user', None)
        ret.set_cookie('userLoggedIn', 'false')
        if (not current_user or not getattr(current_user, 'pk', True)) \
                and current_user != original_user:
            logger.info("User {} logged out.".format(original_user.username))
        return ret


def get_view_description(view, html=False):
    '''Wrapper around REST framework get_view_description() to continue
    to support our historical div.

    '''
    desc = views.get_view_description(view, html=html)
    if html:
        desc = '<div class="description">%s</div>' % desc
    return mark_safe(desc)


def get_default_schema():
    if settings.SETTINGS_MODULE == 'awx.settings.development':
        from awx.api.swagger import AutoSchema
        return AutoSchema()
    else:
        return views.APIView.schema


class APIView(views.APIView):

    schema = get_default_schema()
    versioning_class = URLPathVersioning

    def initialize_request(self, request, *args, **kwargs):
        '''
        Store the Django REST Framework Request object as an attribute on the
        normal Django request, store time the request started.
        '''
        self.time_started = time.time()
        if getattr(settings, 'SQL_DEBUG', False):
            self.queries_before = len(connection.queries)

        # If there are any custom headers in REMOTE_HOST_HEADERS, make sure
        # they respect the allowed proxy list
        if all([
            settings.PROXY_IP_ALLOWED_LIST,
            request.environ.get('REMOTE_ADDR') not in settings.PROXY_IP_ALLOWED_LIST,
            request.environ.get('REMOTE_HOST') not in settings.PROXY_IP_ALLOWED_LIST
        ]):
            for custom_header in settings.REMOTE_HOST_HEADERS:
                if custom_header.startswith('HTTP_'):
                    request.environ.pop(custom_header, None)

        drf_request = super(APIView, self).initialize_request(request, *args, **kwargs)
        request.drf_request = drf_request
        try:
            request.drf_request_user = getattr(drf_request, 'user', False)
        except AuthenticationFailed:
            request.drf_request_user = None
        except (PermissionDenied, ParseError) as exc:
            request.drf_request_user = None
            self.__init_request_error__ = exc
        except UnsupportedMediaType as exc:
            exc.detail = _('You did not use correct Content-Type in your HTTP request. '
                           'If you are using our REST API, the Content-Type must be application/json')
            self.__init_request_error__ = exc
        return drf_request

    def finalize_response(self, request, response, *args, **kwargs):
        '''
        Log warning for 400 requests.  Add header with elapsed time.
        '''
        from awx.main.utils import get_licenser
        from awx.main.utils.licensing import OpenLicense
        #
        # If the URL was rewritten, and we get a 404, we should entirely
        # replace the view in the request context with an ApiErrorView()
        # Without this change, there will be subtle differences in the BrowseableAPIRenderer
        #
        # These differences could provide contextual clues which would allow
        # anonymous users to determine if usernames were valid or not
        # (e.g., if an anonymous user visited `/api/v2/users/valid/`, and got a 404,
        # but also saw that the page heading said "User Detail", they might notice
        # that's a difference in behavior from a request to `/api/v2/users/not-valid/`, which
        # would show a page header of "Not Found").  Changing the view here
        # guarantees that the rendered response will look exactly like the response
        # when you visit a URL that has no matching URL paths in `awx.api.urls`.
        #
        if response.status_code == 404 and 'awx.named_url_rewritten' in request.environ:
            self.headers.pop('Allow', None)
            response = super(APIView, self).finalize_response(request, response, *args, **kwargs)
            view = ApiErrorView()
            setattr(view, 'request', request)
            response.renderer_context['view'] = view
            return response

        if response.status_code >= 400:
            status_msg = "status %s received by user %s attempting to access %s from %s" % \
                         (response.status_code, request.user, request.path, request.META.get('REMOTE_ADDR', None))
            if hasattr(self, '__init_request_error__'):
                response = self.handle_exception(self.__init_request_error__)
            if response.status_code == 401:
                response.data['detail'] += ' To establish a login session, visit /api/login/.'
                logger.info(status_msg)
            else:
                logger.warning(status_msg)
        response = super(APIView, self).finalize_response(request, response, *args, **kwargs)
        time_started = getattr(self, 'time_started', None)
        response['X-API-Product-Version'] = get_awx_version()
        response['X-API-Product-Name'] = 'AWX' if isinstance(get_licenser(), OpenLicense) else 'Red Hat Ansible Tower'
        
        response['X-API-Node'] = settings.CLUSTER_HOST_ID
        if time_started:
            time_elapsed = time.time() - self.time_started
            response['X-API-Time'] = '%0.3fs' % time_elapsed
        if getattr(settings, 'SQL_DEBUG', False):
            queries_before = getattr(self, 'queries_before', 0)
            q_times = [float(q['time']) for q in connection.queries[queries_before:]]
            response['X-API-Query-Count'] = len(q_times)
            response['X-API-Query-Time'] = '%0.3fs' % sum(q_times)

        if getattr(self, 'deprecated', False):
            response['Warning'] = '299 awx "This resource has been deprecated and will be removed in a future release."'  # noqa

        return response

    def get_authenticate_header(self, request):
        # HTTP Basic auth is insecure by default, because the basic auth
        # backend does not provide CSRF protection.
        #
        # If you visit `/api/v2/job_templates/` and we return
        # `WWW-Authenticate: Basic ...`, your browser will prompt you for an
        # HTTP basic auth username+password and will store it _in the browser_
        # for subsequent requests.  Because basic auth does not require CSRF
        # validation (because it's commonly used with e.g., tower-cli and other
        # non-browser clients), browsers that save basic auth in this way are
        # vulnerable to cross-site request forgery:
        #
        # 1. Visit `/api/v2/job_templates/` and specify a user+pass for basic auth.
        # 2. Visit a nefarious website and submit a
        #    `<form action='POST' method='https://tower.example.org/api/v2/job_templates/N/launch/'>`
        # 3. The browser will use your persisted user+pass and your login
        #    session is effectively hijacked.
        #
        # To prevent this, we will _no longer_ send `WWW-Authenticate: Basic ...`
        # headers in responses; this means that unauthenticated /api/v2/... requests
        # will now return HTTP 401 in-browser, rather than popping up an auth dialog.
        #
        # This means that people who wish to use the interactive API browser
        # must _first_ login in via `/api/login/` to establish a session (which
        # _does_ enforce CSRF).
        #
        # CLI users can _still_ specify basic auth credentials explicitly via
        # a header or in the URL e.g.,
        # `curl https://user:pass@tower.example.org/api/v2/job_templates/N/launch/`
        return 'Bearer realm=api authorization_url=/api/o/authorize/'

    def get_description_context(self):
        return {
            'view': self,
            'docstring': type(self).__doc__ or '',
            'deprecated': getattr(self, 'deprecated', False),
            'swagger_method': getattr(self.request, 'swagger_method', None),
        }

    @property
    def description(self):
        template_list = []
        for klass in inspect.getmro(type(self)):
            template_basename = camelcase_to_underscore(klass.__name__)
            template_list.append('api/%s.md' % template_basename)
        context = self.get_description_context()

        description = render_to_string(template_list, context)
        if context.get('deprecated') and context.get('swagger_method') is None:
            # render deprecation messages at the very top
            description = '\n'.join([render_to_string('api/_deprecated.md', context), description])
        return description

    def update_raw_data(self, data):
        # Remove the parent key if the view is a sublist, since it will be set
        # automatically.
        parent_key = getattr(self, 'parent_key', None)
        if parent_key:
            data.pop(parent_key, None)

        # Use request data as-is when original request is an update and the
        # submitted data was rejected.
        request_method = getattr(self, '_raw_data_request_method', None)
        response_status = getattr(self, '_raw_data_response_status', 0)
        if request_method in ('POST', 'PUT', 'PATCH') and response_status in range(400, 500):
            return self.request.data.copy()

        return data

    def determine_version(self, request, *args, **kwargs):
        return (
            getattr(request, 'version', None),
            getattr(request, 'versioning_scheme', None),
        )

    def dispatch(self, request, *args, **kwargs):
        if self.versioning_class is not None:
            scheme = self.versioning_class()
            request.version, request.versioning_scheme = (
                scheme.determine_version(request, *args, **kwargs),
                scheme
            )
            if 'version' in kwargs:
                kwargs.pop('version')
        return super(APIView, self).dispatch(request, *args, **kwargs)

    def check_permissions(self, request):
        if request.method not in ('GET', 'OPTIONS', 'HEAD'):
            if 'write' not in getattr(request.user, 'oauth_scopes', ['write']):
                raise PermissionDenied()
        return super(APIView, self).check_permissions(request)


class GenericAPIView(generics.GenericAPIView, APIView):
    # Base class for all model-based views.

    # Subclasses should define:
    #   model = ModelClass
    #   serializer_class = SerializerClass

    def get_serializer(self, *args, **kwargs):
        serializer = super(GenericAPIView, self).get_serializer(*args, **kwargs)
        # Override when called from browsable API to generate raw data form;
        # update serializer "validated" data to be displayed by the raw data
        # form.
        if hasattr(self, '_raw_data_form_marker'):
            # Always remove read only fields from serializer.
            for name, field in list(serializer.fields.items()):
                if getattr(field, 'read_only', None):
                    del serializer.fields[name]
            serializer._data = self.update_raw_data(serializer.data)
        return serializer

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset._clone()
        elif self.model is not None:
            qs = self.model._default_manager
            if self.model in access_registry:
                access_class = access_registry[self.model]
                if access_class.select_related:
                    qs = qs.select_related(*access_class.select_related)
                if access_class.prefetch_related:
                    qs = qs.prefetch_related(*access_class.prefetch_related)
            return qs
        else:
            return super(GenericAPIView, self).get_queryset()

    def get_description_context(self):
        # Set instance attributes needed to get serializer metadata.
        if not hasattr(self, 'request'):
            self.request = None
        if not hasattr(self, 'format_kwarg'):
            self.format_kwarg = 'format'
        d = super(GenericAPIView, self).get_description_context()
        if hasattr(self.model, "_meta"):
            if hasattr(self.model._meta, "verbose_name"):
                d.update({
                    'model_verbose_name': smart_text(self.model._meta.verbose_name),
                    'model_verbose_name_plural': smart_text(self.model._meta.verbose_name_plural),
                })
            serializer = self.get_serializer()
            metadata = self.metadata_class()
            metadata.request = self.request
            for method, key in [
                ('GET', 'serializer_fields'),
                ('POST', 'serializer_create_fields'),
                ('PUT', 'serializer_update_fields')
            ]:
                d[key] = metadata.get_serializer_info(serializer, method=method)
        d['settings'] = settings
        return d


class SimpleListAPIView(generics.ListAPIView, GenericAPIView):

    def get_queryset(self):
        return self.request.user.get_queryset(self.model)


class ListAPIView(generics.ListAPIView, GenericAPIView):
    # Base class for a read-only list view.

    def get_queryset(self):
        return self.request.user.get_queryset(self.model)

    def get_description_context(self):
        if 'username' in get_all_field_names(self.model):
            order_field = 'username'
        else:
            order_field = 'name'
        d = super(ListAPIView, self).get_description_context()
        d.update({
            'order_field': order_field,
        })
        return d

    @property
    def search_fields(self):
        return get_search_fields(self.model)

    @property
    def related_search_fields(self):
        def skip_related_name(name):
            return (
                name is None or name.endswith('_role') or name.startswith('_') or
                name.startswith('deprecated_') or name.endswith('_set') or
                name == 'polymorphic_ctype')

        fields = set([])
        for field in self.model._meta.fields:
            if skip_related_name(field.name):
                continue
            if getattr(field, 'related_model', None):
                fields.add('{}__search'.format(field.name))
        for related in self.model._meta.related_objects:
            name = related.related_name
            if isinstance(related, OneToOneRel) and self.model._meta.verbose_name.startswith('unified'):
                # Add underscores for polymorphic subclasses for user utility
                name = related.related_model._meta.verbose_name.replace(" ", "_")
            if skip_related_name(name) or name.endswith('+'):
                continue
            fields.add('{}__search'.format(name))
        m2m_related = []
        m2m_related += self.model._meta.local_many_to_many
        if issubclass(self.model, UnifiedJobTemplate) and self.model != UnifiedJobTemplate:
            m2m_related += UnifiedJobTemplate._meta.local_many_to_many
        if issubclass(self.model, UnifiedJob) and self.model != UnifiedJob:
            m2m_related += UnifiedJob._meta.local_many_to_many
        for relationship in m2m_related:
            if skip_related_name(relationship.name):
                continue
            if relationship.related_model._meta.app_label != 'main':
                continue
            fields.add('{}__search'.format(relationship.name))
        fields = list(fields)

        allowed_fields = []
        for field in fields:
            try:
                FieldLookupBackend().get_field_from_lookup(self.model, field)
            except PermissionDenied:
                pass
            except FieldDoesNotExist:
                allowed_fields.append(field)
            else:
                allowed_fields.append(field)
        return allowed_fields


class ListCreateAPIView(ListAPIView, generics.ListCreateAPIView):
    # Base class for a list view that allows creating new objects.
    pass


class ParentMixin(object):
    parent_object = None

    def get_parent_object(self):
        if self.parent_object is not None:
            return self.parent_object
        parent_filter = {
            self.lookup_field: self.kwargs.get(self.lookup_field, None),
        }
        self.parent_object = get_object_or_404(self.parent_model, **parent_filter)
        return self.parent_object

    def check_parent_access(self, parent=None):
        parent = parent or self.get_parent_object()
        parent_access = getattr(self, 'parent_access', 'read')
        if parent_access in ('read', 'delete'):
            args = (self.parent_model, parent_access, parent)
        else:
            args = (self.parent_model, parent_access, parent, None)
        if not self.request.user.can_access(*args):
            raise PermissionDenied()


class SubListAPIView(ParentMixin, ListAPIView):
    # Base class for a read-only sublist view.

    # Subclasses should define at least:
    #   model = ModelClass
    #   serializer_class = SerializerClass
    #   parent_model = ModelClass
    #   relationship = 'rel_name_from_parent_to_model'
    # And optionally (user must have given access permission on parent object
    # to view sublist):
    #   parent_access = 'read'

    def get_description_context(self):
        d = super(SubListAPIView, self).get_description_context()
        d.update({
            'parent_model_verbose_name': smart_text(self.parent_model._meta.verbose_name),
            'parent_model_verbose_name_plural': smart_text(self.parent_model._meta.verbose_name_plural),
        })
        return d

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct()
        sublist_qs = self.get_sublist_queryset(parent)
        return qs & sublist_qs

    def get_sublist_queryset(self, parent):
        return getattrd(parent, self.relationship).distinct()


class DestroyAPIView(generics.DestroyAPIView):

    def has_delete_permission(self, obj):
        return self.request.user.can_access(self.model, 'delete', obj)

    def perform_destroy(self, instance, check_permission=True):
        if check_permission and not self.has_delete_permission(instance):
            raise PermissionDenied()
        super(DestroyAPIView, self).perform_destroy(instance)


class SubListDestroyAPIView(DestroyAPIView, SubListAPIView):
    """
    Concrete view for deleting everything related by `relationship`.
    """
    check_sub_obj_permission = True

    def destroy(self, request, *args, **kwargs):
        instance_list = self.get_queryset()
        if (not self.check_sub_obj_permission and
                not request.user.can_access(self.parent_model, 'delete', self.get_parent_object())):
            raise PermissionDenied()
        self.perform_list_destroy(instance_list)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_list_destroy(self, instance_list):
        if self.check_sub_obj_permission:
            for instance in instance_list:
                if not self.has_delete_permission(instance):
                    raise PermissionDenied()
        for instance in instance_list:
            self.perform_destroy(instance, check_permission=False)


class SubListCreateAPIView(SubListAPIView, ListCreateAPIView):
    # Base class for a sublist view that allows for creating subobjects
    # associated with the parent object.

    # In addition to SubListAPIView properties, subclasses may define (if the
    # sub_obj requires a foreign key to the parent):
    #   parent_key = 'field_on_model_referring_to_parent'

    def get_description_context(self):
        d = super(SubListCreateAPIView, self).get_description_context()
        d.update({
            'parent_key': getattr(self, 'parent_key', None),
        })
        return d

    def get_queryset(self):
        if hasattr(self, 'parent_key'):
            # Prefer this filtering because ForeignKey allows us more assumptions
            parent = self.get_parent_object()
            self.check_parent_access(parent)
            qs = self.request.user.get_queryset(self.model)
            return qs.filter(**{self.parent_key: parent})
        return super(SubListCreateAPIView, self).get_queryset()

    def create(self, request, *args, **kwargs):
        # If the object ID was not specified, it probably doesn't exist in the
        # DB yet. We want to see if we can create it.  The URL may choose to
        # inject it's primary key into the object because we are posting to a
        # subcollection. Use all the normal access control mechanisms.

        # Make a copy of the data provided (since it's readonly) in order to
        # inject additional data.
        if hasattr(request.data, 'copy'):
            data = request.data.copy()
        else:
            data = QueryDict('')
            data.update(request.data)

        # add the parent key to the post data using the pk from the URL
        parent_key = getattr(self, 'parent_key', None)
        if parent_key:
            data[parent_key] = self.kwargs['pk']

        # attempt to deserialize the object
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # Verify we have permission to add the object as given.
        if not request.user.can_access(self.model, 'add', serializer.validated_data):
            raise PermissionDenied()

        # save the object through the serializer, reload and returned the saved
        # object deserialized
        obj = serializer.save()
        serializer = self.get_serializer(instance=obj)

        headers = {'Location': obj.get_absolute_url(request)}
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SubListCreateAttachDetachAPIView(SubListCreateAPIView):
    # Base class for a sublist view that allows for creating subobjects and
    # attaching/detaching them from the parent.

    def is_valid_relation(self, parent, sub, created=False):
        return None

    def get_description_context(self):
        d = super(SubListCreateAttachDetachAPIView, self).get_description_context()
        d.update({
            "has_attach": True,
        })
        return d

    def attach_validate(self, request):
        sub_id = request.data.get('id', None)
        res = None
        if sub_id and not isinstance(sub_id, int):
            data = dict(msg=_('"id" field must be an integer.'))
            res = Response(data, status=status.HTTP_400_BAD_REQUEST)
        return (sub_id, res)

    def attach(self, request, *args, **kwargs):
        created = False
        parent = self.get_parent_object()
        relationship = getattrd(parent, self.relationship)
        data = request.data

        sub_id, res = self.attach_validate(request)
        if res:
            return res

        # Create the sub object if an ID is not provided.
        if not sub_id:
            response = self.create(request, *args, **kwargs)
            if response.status_code != status.HTTP_201_CREATED:
                return response
            sub_id = response.data['id']
            data = response.data
            try:
                location = response['Location']
            except KeyError:
                location = None
            created = True

        # Retrive the sub object (whether created or by ID).
        sub = get_object_or_400(self.model, pk=sub_id)

        # Verify we have permission to attach.
        if not request.user.can_access(self.parent_model, 'attach', parent, sub,
                                       self.relationship, data,
                                       skip_sub_obj_read_check=created):
            raise PermissionDenied()

        # Verify that the relationship to be added is valid.
        attach_errors = self.is_valid_relation(parent, sub, created=created)
        if attach_errors is not None:
            if created:
                sub.delete()
            return Response(attach_errors, status=status.HTTP_400_BAD_REQUEST)

        # Attach the object to the collection.
        if sub not in relationship.all():
            relationship.add(sub)

        if created:
            headers = {}
            if location:
                headers['Location'] = location
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def unattach_validate(self, request):
        sub_id = request.data.get('id', None)
        res = None
        if not sub_id:
            data = dict(msg=_('"id" is required to disassociate'))
            res = Response(data, status=status.HTTP_400_BAD_REQUEST)
        elif not isinstance(sub_id, int):
            data = dict(msg=_('"id" field must be an integer.'))
            res = Response(data, status=status.HTTP_400_BAD_REQUEST)
        return (sub_id, res)

    def unattach_by_id(self, request, sub_id):
        parent = self.get_parent_object()
        parent_key = getattr(self, 'parent_key', None)
        relationship = getattrd(parent, self.relationship)
        sub = get_object_or_400(self.model, pk=sub_id)

        if not request.user.can_access(self.parent_model, 'unattach', parent,
                                       sub, self.relationship, request.data):
            raise PermissionDenied()

        if parent_key:
            sub.delete()
        else:
            relationship.remove(sub)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def unattach(self, request, *args, **kwargs):
        (sub_id, res) = self.unattach_validate(request)
        if res:
            return res
        return self.unattach_by_id(request, sub_id)

    def post(self, request, *args, **kwargs):
        if not isinstance(request.data, dict):
            return Response('invalid type for post data',
                            status=status.HTTP_400_BAD_REQUEST)
        if 'disassociate' in request.data:
            return self.unattach(request, *args, **kwargs)
        else:
            return self.attach(request, *args, **kwargs)



class SubListAttachDetachAPIView(SubListCreateAttachDetachAPIView):
    '''
    Derived version of SubListCreateAttachDetachAPIView that prohibits creation
    '''
    metadata_class = SublistAttachDetatchMetadata

    def post(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return Response(
                dict(msg=_("{} 'id' field is missing.".format(
                    self.model._meta.verbose_name.title()))),
                status=status.HTTP_400_BAD_REQUEST)
        return super(SubListAttachDetachAPIView, self).post(request, *args, **kwargs)

    def update_raw_data(self, data):
        request_method = getattr(self, '_raw_data_request_method', None)
        response_status = getattr(self, '_raw_data_response_status', 0)
        if request_method == 'POST' and response_status in range(400, 500):
            return super(SubListAttachDetachAPIView, self).update_raw_data(data)
        return {'id': None}


class DeleteLastUnattachLabelMixin(object):
    '''
    Models for which you want the last instance to be deleted from the database
    when the last disassociate is called should inherit from this class. Further,
    the model should implement is_detached()
    '''

    def unattach(self, request, *args, **kwargs):
        (sub_id, res) = super(DeleteLastUnattachLabelMixin, self).unattach_validate(request)
        if res:
            return res

        res = super(DeleteLastUnattachLabelMixin, self).unattach_by_id(request, sub_id)

        obj = self.model.objects.get(id=sub_id)

        if obj.is_detached():
            obj.delete()

        return res


class SubDetailAPIView(ParentMixin, generics.RetrieveAPIView, GenericAPIView):
    pass


class RetrieveAPIView(generics.RetrieveAPIView, GenericAPIView):
    pass


class RetrieveUpdateAPIView(RetrieveAPIView, generics.RetrieveUpdateAPIView):

    def update(self, request, *args, **kwargs):
        self.update_filter(request, *args, **kwargs)
        return super(RetrieveUpdateAPIView, self).update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.update_filter(request, *args, **kwargs)
        return super(RetrieveUpdateAPIView, self).partial_update(request, *args, **kwargs)

    def update_filter(self, request, *args, **kwargs):
        ''' scrub any fields the user cannot/should not put/patch, based on user context.  This runs after read-only serialization filtering '''
        pass


class RetrieveDestroyAPIView(RetrieveAPIView, DestroyAPIView):
    pass


class RetrieveUpdateDestroyAPIView(RetrieveUpdateAPIView, DestroyAPIView):
    pass


class ResourceAccessList(ParentMixin, ListAPIView):

    serializer_class = ResourceAccessListElementSerializer
    ordering = ('username',)

    def get_queryset(self):
        obj = self.get_parent_object()

        content_type = ContentType.objects.get_for_model(obj)
        roles = set(Role.objects.filter(content_type=content_type, object_id=obj.id))

        ancestors = set()
        for r in roles:
            ancestors.update(set(r.ancestors.all()))
        return User.objects.filter(roles__in=list(ancestors)).distinct()


def trigger_delayed_deep_copy(*args, **kwargs):
    from awx.main.tasks import deep_copy_model_obj
    connection.on_commit(lambda: deep_copy_model_obj.delay(*args, **kwargs))


class CopyAPIView(GenericAPIView):

    serializer_class = CopySerializer
    permission_classes = (AllowAny,)
    copy_return_serializer_class = None
    new_in_330 = True
    new_in_api_v2 = True

    def _get_copy_return_serializer(self, *args, **kwargs):
        if not self.copy_return_serializer_class:
            return self.get_serializer(*args, **kwargs)
        serializer_class_store = self.serializer_class
        self.serializer_class = self.copy_return_serializer_class
        ret = self.get_serializer(*args, **kwargs)
        self.serializer_class = serializer_class_store
        return ret

    @staticmethod
    def _decrypt_model_field_if_needed(obj, field_name, field_val):
        if field_name in getattr(type(obj), 'REENCRYPTION_BLOCKLIST_AT_COPY', []):
            return field_val
        if isinstance(obj, Credential) and field_name == 'inputs':
            for secret in obj.credential_type.secret_fields:
                if secret in field_val:
                    field_val[secret] = decrypt_field(obj, secret)
        elif isinstance(field_val, dict):
            for sub_field in field_val:
                if isinstance(sub_field, str) \
                        and isinstance(field_val[sub_field], str):
                    field_val[sub_field] = decrypt_field(obj, field_name, sub_field)
        elif isinstance(field_val, str):
            try:
                field_val = decrypt_field(obj, field_name)
            except AttributeError:
                return field_val
        return field_val

    def _build_create_dict(self, obj):
        ret = {}
        if self.copy_return_serializer_class:
            all_fields = Metadata().get_serializer_info(
                self._get_copy_return_serializer(), method='POST'
            )
            for field_name, field_info in all_fields.items():
                if not hasattr(obj, field_name) or field_info.get('read_only', True):
                    continue
                ret[field_name] = CopyAPIView._decrypt_model_field_if_needed(
                    obj, field_name, getattr(obj, field_name)
                )
        return ret

    @staticmethod
    def copy_model_obj(old_parent, new_parent, model, obj, creater, copy_name='', create_kwargs=None):
        fields_to_preserve = set(getattr(model, 'FIELDS_TO_PRESERVE_AT_COPY', []))
        fields_to_discard = set(getattr(model, 'FIELDS_TO_DISCARD_AT_COPY', []))
        m2m_to_preserve = {}
        o2m_to_preserve = {}
        create_kwargs = create_kwargs or {}
        for field_name in fields_to_discard:
            create_kwargs.pop(field_name, None)
        for field in model._meta.get_fields():
            try:
                field_val = getattr(obj, field.name)
            except AttributeError:
                continue
            # Adjust copy blocked fields here.
            if field.name in fields_to_discard or field.name in [
                'id', 'pk', 'polymorphic_ctype', 'unifiedjobtemplate_ptr', 'created_by', 'modified_by'
            ] or field.name.endswith('_role'):
                create_kwargs.pop(field.name, None)
                continue
            if field.one_to_many:
                if field.name in fields_to_preserve:
                    o2m_to_preserve[field.name] = field_val
            elif field.many_to_many:
                if field.name in fields_to_preserve and not old_parent:
                    m2m_to_preserve[field.name] = field_val
            elif field.many_to_one and not field_val:
                create_kwargs.pop(field.name, None)
            elif field.many_to_one and field_val == old_parent:
                create_kwargs[field.name] = new_parent
            elif field.name == 'name' and not old_parent:
                create_kwargs[field.name] = copy_name or field_val + ' copy'
            elif field.name in fields_to_preserve:
                create_kwargs[field.name] = CopyAPIView._decrypt_model_field_if_needed(
                    obj, field.name, field_val
                )

        # WorkflowJobTemplateNodes that represent an approval are *special*;
        # when we copy them, we actually want to *copy* the UJT they point at
        # rather than share the template reference between nodes in disparate
        # workflows
        if (
            isinstance(obj, WorkflowJobTemplateNode) and
            isinstance(getattr(obj, 'unified_job_template'), WorkflowApprovalTemplate)
        ):
            new_approval_template, sub_objs = CopyAPIView.copy_model_obj(
                None, None, WorkflowApprovalTemplate,
                obj.unified_job_template, creater
            )
            create_kwargs['unified_job_template'] = new_approval_template

        new_obj = model.objects.create(**create_kwargs)
        logger.debug('Deep copy: Created new object {}({})'.format(
            new_obj, model
        ))
        # Need to save separatedly because Djang-crum get_current_user would
        # not work properly in non-request-response-cycle context.
        new_obj.created_by = creater
        new_obj.save()
        from awx.main.signals import disable_activity_stream
        with disable_activity_stream():
            for m2m in m2m_to_preserve:
                for related_obj in m2m_to_preserve[m2m].all():
                    getattr(new_obj, m2m).add(related_obj)
        if not old_parent:
            sub_objects = []
            for o2m in o2m_to_preserve:
                for sub_obj in o2m_to_preserve[o2m].all():
                    sub_model = type(sub_obj)
                    sub_objects.append((sub_model.__module__, sub_model.__name__, sub_obj.pk))
            return new_obj, sub_objects
        ret = {obj: new_obj}
        for o2m in o2m_to_preserve:
            for sub_obj in o2m_to_preserve[o2m].all():
                ret.update(CopyAPIView.copy_model_obj(obj, new_obj, type(sub_obj), sub_obj, creater))
        return ret

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(obj.__class__, 'read', obj):
            raise PermissionDenied()
        create_kwargs = self._build_create_dict(obj)
        for key in create_kwargs:
            create_kwargs[key] = getattr(create_kwargs[key], 'pk', None) or create_kwargs[key]
        try:
            can_copy = request.user.can_access(self.model, 'add', create_kwargs) and \
                request.user.can_access(self.model, 'copy_related', obj)
        except PermissionDenied:
            return Response({'can_copy': False})
        return Response({'can_copy': can_copy})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        create_kwargs = self._build_create_dict(obj)
        create_kwargs_check = {}
        for key in create_kwargs:
            create_kwargs_check[key] = getattr(create_kwargs[key], 'pk', None) or create_kwargs[key]
        if not request.user.can_access(self.model, 'add', create_kwargs_check):
            raise PermissionDenied()
        if not request.user.can_access(self.model, 'copy_related', obj):
            raise PermissionDenied()
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_obj, sub_objs = CopyAPIView.copy_model_obj(
            None, None, self.model, obj, request.user, create_kwargs=create_kwargs,
            copy_name=serializer.validated_data.get('name', '')
        )
        if hasattr(new_obj, 'admin_role') and request.user not in new_obj.admin_role.members.all():
            new_obj.admin_role.members.add(request.user)
        if sub_objs:
            # store the copied object dict into cache, because it's
            # often too large for postgres' notification bus
            # (which has a default maximum message size of 8k)
            key = 'deep-copy-{}'.format(str(uuid.uuid4()))
            cache.set(key, sub_objs, timeout=3600)
            permission_check_func = None
            if hasattr(type(self), 'deep_copy_permission_check_func'):
                permission_check_func = (
                    type(self).__module__, type(self).__name__, 'deep_copy_permission_check_func'
                )
            trigger_delayed_deep_copy(
                self.model.__module__, self.model.__name__,
                obj.pk, new_obj.pk, request.user.pk, key,
                permission_check_func=permission_check_func
            )
        serializer = self._get_copy_return_serializer(new_obj)
        headers = {'Location': new_obj.get_absolute_url(request=request)}
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BaseUsersList(SubListCreateAttachDetachAPIView):
    def post(self, request, *args, **kwargs):
        ret = super(BaseUsersList, self).post( request, *args, **kwargs)
        if ret.status_code != 201:
            return ret
        try:
            if ret.data is not None and request.data.get('is_system_auditor', False):
                # This is a faux-field that just maps to checking the system
                # auditor role member list.. unfortunately this means we can't
                # set it on creation, and thus needs to be set here.
                user = User.objects.get(id=ret.data['id'])
                user.is_system_auditor = request.data['is_system_auditor']
                ret.data['is_system_auditor'] = request.data['is_system_auditor']
        except AttributeError as exc:
            print(exc)
            pass
        return ret
