# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import dateutil
import logging
import requests

# Django
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.response import Response
from rest_framework import status


# AWX
from awx.main.utils.filters import SmartFilter
from awx.main.utils.insights import filter_insights_api_response
from awx.main.utils import decrypt_field

from awx.api.generics import (
    ParentMixin,
    GenericAPIView,
    SubDetailAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveAPIView,
    SubListCreateAttachDetachAPIView,
    SubListAPIView,
    SubListCreateAPIView,
    AdHocCommandList,
)
from awx.api.base import (
    BaseVariableData,
    BaseJobHostSummariesList,
    BaseJobEventsList,
    BaseAdHocCommandEventsList,
)
from awx.api.serializers import (
    EmptySerializer,
    FactSerializer,
    HostSerializer,
    FactVersionSerializer,
    AnsibleFactsSerializer,
    GroupSerializer,
    InventorySourceSerializer,
    InventorySerializer,
    ActivityStreamSerializer,
    HostVariableDataSerializer,
)
from awx.api.views.mixins import (
    ControlledByScmMixin,
    ActivityStreamEnforcementMixin,
    SystemTrackingEnforcementMixin,
)
from awx.main.models import (
    ActivityStream,
    Fact,
    Host,
    Group,
    Inventory,
    InventorySource,
)

logger = logging.getLogger('awx.api.views')


class HostList(ListCreateAPIView):

    always_allow_superuser = False
    model = Host
    serializer_class = HostSerializer
    capabilities_prefetch = ['inventory.admin']

    def get_queryset(self):
        qs = super(HostList, self).get_queryset()
        filter_string = self.request.query_params.get('host_filter', None)
        if filter_string:
            filter_qs = SmartFilter.query_from_string(filter_string)
            qs &= filter_qs
        return qs.distinct()

    def list(self, *args, **kwargs):
        try:
            return super(HostList, self).list(*args, **kwargs)
        except Exception as e:
            return Response(dict(error=_(unicode(e))), status=status.HTTP_400_BAD_REQUEST)


class HostDetail(ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    always_allow_superuser = False
    model = Host
    serializer_class = HostSerializer


class HostAnsibleFactsDetail(RetrieveAPIView):

    model = Host
    serializer_class = AnsibleFactsSerializer
    new_in_320 = True
    new_in_api_v2 = True


class HostGroupsList(ControlledByScmMixin, SubListCreateAttachDetachAPIView):
    ''' the list of groups a host is directly a member of '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(HostGroupsList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent host inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data['inventory'] = self.get_parent_object().inventory_id
        return super(HostGroupsList, self).create(request, *args, **kwargs)


class HostAllGroupsList(SubListAPIView):
    ''' the list of all groups of which the host is directly or indirectly a member '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct()
        sublist_qs = parent.all_groups.distinct()
        return qs & sublist_qs


class HostInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Host
    relationship = 'inventory_sources'
    new_in_148 = True


class HostSmartInventoriesList(SubListAPIView):
    model = Inventory
    serializer_class = InventorySerializer
    parent_model = Host
    relationship = 'smart_inventories'
    new_in_320 = True


class HostActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Host
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(host=parent) | Q(inventory=parent.inventory))


class HostFactVersionsList(SystemTrackingEnforcementMixin, ParentMixin, ListAPIView):

    model = Fact
    serializer_class = FactVersionSerializer
    parent_model = Host
    new_in_220 = True

    def get_queryset(self):
        from_spec = self.request.query_params.get('from', None)
        to_spec = self.request.query_params.get('to', None)
        module_spec = self.request.query_params.get('module', None)

        if from_spec:
            from_spec = dateutil.parser.parse(from_spec)
        if to_spec:
            to_spec = dateutil.parser.parse(to_spec)

        host_obj = self.get_parent_object()

        return Fact.get_timeline(host_obj.id, module=module_spec, ts_from=from_spec, ts_to=to_spec)

    def list(self, *args, **kwargs):
        queryset = self.get_queryset() or []
        return Response(dict(results=self.serializer_class(queryset, many=True).data))


class HostFactCompareView(SystemTrackingEnforcementMixin, SubDetailAPIView):

    model = Fact
    new_in_220 = True
    parent_model = Host
    serializer_class = FactSerializer

    def retrieve(self, request, *args, **kwargs):
        datetime_spec = request.query_params.get('datetime', None)
        module_spec = request.query_params.get('module', "ansible")
        datetime_actual = dateutil.parser.parse(datetime_spec) if datetime_spec is not None else now()

        host_obj = self.get_parent_object()

        fact_entry = Fact.get_host_fact(host_obj.id, module_spec, datetime_actual)
        if not fact_entry:
            return Response({'detail': _('Fact not found.')}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(instance=fact_entry).data)


class HostInsights(GenericAPIView):

    model = Host
    serializer_class = EmptySerializer
    new_in_320 = True
    new_in_api_v2 = True

    def _extract_insights_creds(self, credential):
        return (credential.inputs['username'], decrypt_field(credential, 'password'))

    def _get_insights(self, url, username, password):
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        headers = {'Content-Type': 'application/json'}
        return session.get(url, headers=headers, timeout=120)

    def get_insights(self, url, username, password):
        try:
            res = self._get_insights(url, username, password)
        except requests.exceptions.SSLError:
            return (dict(error=_('SSLError while trying to connect to {}').format(url)), status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.Timeout:
            return (dict(error=_('Request to {} timed out.').format(url)), status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return (dict(error=_('Unkown exception {} while trying to GET {}').format(e, url)), status.HTTP_502_BAD_GATEWAY)

        if res.status_code == 401:
            return (dict(error=_('Unauthorized access. Please check your Insights Credential username and password.')), status.HTTP_502_BAD_GATEWAY)
        elif res.status_code != 200:
            return (dict(error=_(
                'Failed to gather reports and maintenance plans from Insights API at URL {}. Server responded with {} status code and message {}'
            ).format(url, res.status_code, res.content)), status.HTTP_502_BAD_GATEWAY)

        try:
            filtered_insights_content = filter_insights_api_response(res.json())
            return (dict(insights_content=filtered_insights_content), status.HTTP_200_OK)
        except ValueError:
            return (dict(error=_('Expected JSON response from Insights but instead got {}').format(res.content)), status.HTTP_502_BAD_GATEWAY)

    def get(self, request, *args, **kwargs):
        host = self.get_object()
        cred = None

        if host.insights_system_id is None:
            return Response(dict(error=_('This host is not recognized as an Insights host.')), status=status.HTTP_404_NOT_FOUND)

        if host.inventory and host.inventory.insights_credential:
            cred = host.inventory.insights_credential
        else:
            return Response(dict(error=_('The Insights Credential for "{}" was not found.').format(host.inventory.name)), status=status.HTTP_404_NOT_FOUND)

        url = settings.INSIGHTS_URL_BASE + '/r/insights/v3/systems/{}/reports/'.format(host.insights_system_id)
        (username, password) = self._extract_insights_creds(cred)
        (msg, err_code) = self.get_insights(url, username, password)
        return Response(msg, status=err_code)


class HostVariableData(BaseVariableData):

    model = Host
    serializer_class = HostVariableDataSerializer


class HostJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Host


class HostJobEventsList(BaseJobEventsList):

    parent_model = Host

    def get_queryset(self):
        parent_obj = self.get_parent_object()
        self.check_parent_access(parent_obj)
        qs = self.request.user.get_queryset(self.model).filter(
            Q(host=parent_obj) | Q(hosts=parent_obj)).distinct()
        return qs


class HostAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Host
    relationship = 'ad_hoc_commands'


class HostAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = Host
    new_in_220 = True
