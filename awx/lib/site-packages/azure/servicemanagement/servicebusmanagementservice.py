#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
from azure import (
    MANAGEMENT_HOST,
    _convert_response_to_feeds,
    _str,
    _validate_not_none,
    _convert_xml_to_windows_azure_object,
)
from azure.servicemanagement import (
    _ServiceBusManagementXmlSerializer,
    QueueDescription,
    TopicDescription,
    NotificationHubDescription,
    RelayDescription,
    MetricProperties,
    MetricValues,
    MetricRollups,
)
from azure.servicemanagement.servicemanagementclient import (
    _ServiceManagementClient,
)

from functools import partial

X_MS_VERSION = '2012-03-01'

class ServiceBusManagementService(_ServiceManagementClient):

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST, request_session=None):
        '''
        Initializes the service bus management service.

        subscription_id: Subscription to manage.
        cert_file:
            Path to .pem certificate file (httplib), or location of the
            certificate in your Personal certificate store (winhttp) in the
            CURRENT_USER\my\CertificateName format.
            If a request_session is specified, then this is unused.
        host: Live ServiceClient URL. Defaults to Azure public cloud.
        request_session:
            Session object to use for http requests. If this is specified, it
            replaces the default use of httplib or winhttp. Also, the cert_file
            parameter is unused when a session is passed in.
            The session object handles authentication, and as such can support
            multiple types of authentication: .pem certificate, oauth.
            For example, you can pass in a Session instance from the requests
            library. To use .pem certificate authentication with requests
            library, set the path to the .pem file on the session.cert
            attribute.
        '''
        super(ServiceBusManagementService, self).__init__(
            subscription_id, cert_file, host, request_session)
        self.x_ms_version = X_MS_VERSION

    # Operations for service bus ----------------------------------------
    def get_regions(self):
        '''
        Get list of available service bus regions.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Regions/', None),
            None)

        return _convert_response_to_feeds(
            response,
            _ServiceBusManagementXmlSerializer.xml_to_region)

    def list_namespaces(self):
        '''
        List the service bus namespaces defined on the account.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Namespaces/', None),
            None)

        return _convert_response_to_feeds(
            response,
            _ServiceBusManagementXmlSerializer.xml_to_namespace)

    def get_namespace(self, name):
        '''
        Get details about a specific namespace.

        name: Name of the service bus namespace.
        '''
        response = self._perform_get(
            self._get_path('services/serviceBus/Namespaces', name),
            None)

        return _ServiceBusManagementXmlSerializer.xml_to_namespace(
            response.body)

    def create_namespace(self, name, region):
        '''
        Create a new service bus namespace.

        name: Name of the service bus namespace to create.
        region: Region to create the namespace in.
        '''
        _validate_not_none('name', name)

        return self._perform_put(
            self._get_path('services/serviceBus/Namespaces', name),
            _ServiceBusManagementXmlSerializer.namespace_to_xml(region))

    def delete_namespace(self, name):
        '''
        Delete a service bus namespace.

        name: Name of the service bus namespace to delete.
        '''
        _validate_not_none('name', name)

        return self._perform_delete(
            self._get_path('services/serviceBus/Namespaces', name),
            None)

    def check_namespace_availability(self, name):
        '''
        Checks to see if the specified service bus namespace is available, or
        if it has already been taken.

        name: Name of the service bus namespace to validate.
        '''
        _validate_not_none('name', name)

        response = self._perform_get(
            self._get_path('services/serviceBus/CheckNamespaceAvailability',
                           None) + '/?namespace=' + _str(name), None)

        return _ServiceBusManagementXmlSerializer.xml_to_namespace_availability(
            response.body)

    def list_queues(self, name):
        '''
        Enumerates the queues in the service namespace.

        name: Name of the service bus namespace.
        '''
        _validate_not_none('name', name)

        response = self._perform_get(
            self._get_list_queues_path(name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_convert_xml_to_windows_azure_object,
                                                  azure_type=QueueDescription))

    def list_topics(self, name):
        '''
        Retrieves the topics in the service namespace.

        name: Name of the service bus namespace.
        '''
        response = self._perform_get(
            self._get_list_topics_path(name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_convert_xml_to_windows_azure_object,
                                                  azure_type=TopicDescription))

    def list_notification_hubs(self, name):
        '''
        Retrieves the notification hubs in the service namespace.

        name: Name of the service bus namespace.
        '''
        response = self._perform_get(
            self._get_list_notification_hubs_path(name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_convert_xml_to_windows_azure_object,
                                                  azure_type=NotificationHubDescription))

    def list_relays(self, name):
        '''
        Retrieves the relays in the service namespace.

        name: Name of the service bus namespace.
        '''
        response = self._perform_get(
            self._get_list_relays_path(name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_convert_xml_to_windows_azure_object,
                                                  azure_type=RelayDescription))

    def get_supported_metrics_queue(self, name, queue_name):
        '''
        Retrieves the list of supported metrics for this namespace and queue

        name: Name of the service bus namespace.
        queue_name: Name of the service bus queue in this namespace.
        '''
        response = self._perform_get(
            self._get_get_supported_metrics_queue_path(name, queue_name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricProperties))

    def get_supported_metrics_topic(self, name, topic_name):
        '''
        Retrieves the list of supported metrics for this namespace and topic

        name: Name of the service bus namespace.
        topic_name: Name of the service bus queue in this namespace.
        '''
        response = self._perform_get(
            self._get_get_supported_metrics_topic_path(name, topic_name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricProperties))

    def get_supported_metrics_notification_hub(self, name, hub_name):
        '''
        Retrieves the list of supported metrics for this namespace and topic

        name: Name of the service bus namespace.
        hub_name: Name of the service bus notification hub in this namespace.
        '''
        response = self._perform_get(
            self._get_get_supported_metrics_hub_path(name, hub_name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricProperties))

    def get_supported_metrics_relay(self, name, relay_name):
        '''
        Retrieves the list of supported metrics for this namespace and relay

        name: Name of the service bus namespace.
        relay_name: Name of the service bus relay in this namespace.
        '''
        response = self._perform_get(
            self._get_get_supported_metrics_relay_path(name, relay_name),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricProperties))

    def get_metrics_data_queue(self, name, queue_name, metric, rollup, filter_expresssion):
        '''
        Retrieves the list of supported metrics for this namespace and queue

        name: Name of the service bus namespace.
        queue_name: Name of the service bus queue in this namespace.
        metric: name of a supported metric
        rollup: name of a supported rollup
        filter_expression: filter, for instance "$filter=Timestamp gt datetime'2014-10-01T00:00:00Z'"
        '''
        response = self._perform_get(
            self._get_get_metrics_data_queue_path(name, queue_name, metric, rollup, filter_expresssion),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricValues))

    def get_metrics_data_topic(self, name, topic_name, metric, rollup, filter_expresssion):
        '''
        Retrieves the list of supported metrics for this namespace and topic

        name: Name of the service bus namespace.
        topic_name: Name of the service bus queue in this namespace.
        metric: name of a supported metric
        rollup: name of a supported rollup
        filter_expression: filter, for instance "$filter=Timestamp gt datetime'2014-10-01T00:00:00Z'"
        '''
        response = self._perform_get(
            self._get_get_metrics_data_topic_path(name, topic_name, metric, rollup, filter_expresssion),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricValues))

    def get_metrics_data_notification_hub(self, name, hub_name, metric, rollup, filter_expresssion):
        '''
        Retrieves the list of supported metrics for this namespace and topic

        name: Name of the service bus namespace.
        hub_name: Name of the service bus notification hub in this namespace.
        metric: name of a supported metric
        rollup: name of a supported rollup
        filter_expression: filter, for instance "$filter=Timestamp gt datetime'2014-10-01T00:00:00Z'"
        '''
        response = self._perform_get(
            self._get_get_metrics_data_hub_path(name, hub_name, metric, rollup, filter_expresssion),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricValues))

    def get_metrics_data_relay(self, name, relay_name, metric, rollup, filter_expresssion):
        '''
        Retrieves the list of supported metrics for this namespace and relay

        name: Name of the service bus namespace.
        relay_name: Name of the service bus relay in this namespace.
        metric: name of a supported metric
        rollup: name of a supported rollup
        filter_expression: filter, for instance "$filter=Timestamp gt datetime'2014-10-01T00:00:00Z'"
        '''
        response = self._perform_get(
            self._get_get_metrics_data_relay_path(name, relay_name, metric, rollup, filter_expresssion),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricValues))

    def get_metrics_rollups_queue(self, name, queue_name, metric):
        '''
        This operation gets rollup data for Service Bus metrics queue.
        Rollup data includes the time granularity for the telemetry aggregation as well as
        the retention settings for each time granularity.

        name: Name of the service bus namespace.
        queue_name: Name of the service bus queue in this namespace.
        metric: name of a supported metric
        '''
        response = self._perform_get(
            self._get_get_metrics_rollup_queue_path(name, queue_name, metric),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricRollups))

    def get_metrics_rollups_topic(self, name, topic_name, metric):
        '''
        This operation gets rollup data for Service Bus metrics topic.
        Rollup data includes the time granularity for the telemetry aggregation as well as
        the retention settings for each time granularity.

        name: Name of the service bus namespace.
        topic_name: Name of the service bus queue in this namespace.
        metric: name of a supported metric
        '''
        response = self._perform_get(
            self._get_get_metrics_rollup_topic_path(name, topic_name, metric),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricRollups))

    def get_metrics_rollups_notification_hub(self, name, hub_name, metric):
        '''
        This operation gets rollup data for Service Bus metrics notification hub.
        Rollup data includes the time granularity for the telemetry aggregation as well as
        the retention settings for each time granularity.

        name: Name of the service bus namespace.
        hub_name: Name of the service bus notification hub in this namespace.
        metric: name of a supported metric
        '''
        response = self._perform_get(
            self._get_get_metrics_rollup_hub_path(name, hub_name, metric),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricRollups))

    def get_metrics_rollups_relay(self, name, relay_name, metric):
        '''
        This operation gets rollup data for Service Bus metrics relay.
        Rollup data includes the time granularity for the telemetry aggregation as well as
        the retention settings for each time granularity.

        name: Name of the service bus namespace.
        relay_name: Name of the service bus relay in this namespace.
        metric: name of a supported metric
        '''
        response = self._perform_get(
            self._get_get_metrics_rollup_relay_path(name, relay_name, metric),
            None)

        return _convert_response_to_feeds(response,
                                          partial(_ServiceBusManagementXmlSerializer.xml_to_metrics,
                                                  object_type=MetricRollups))


    # Helper functions --------------------------------------------------
    def _get_list_queues_path(self, namespace_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Queues'

    def _get_list_topics_path(self, namespace_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Topics'

    def _get_list_notification_hubs_path(self, namespace_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/NotificationHubs'

    def _get_list_relays_path(self, namespace_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Relays'

    def _get_get_supported_metrics_queue_path(self, namespace_name, queue_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Queues/' + _str(queue_name) + '/Metrics'

    def _get_get_supported_metrics_topic_path(self, namespace_name, topic_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Topics/' + _str(topic_name) + '/Metrics'

    def _get_get_supported_metrics_hub_path(self, namespace_name, hub_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/NotificationHubs/' + _str(hub_name) + '/Metrics'

    def _get_get_supported_metrics_relay_path(self, namespace_name, queue_name):
        return self._get_path('services/serviceBus/Namespaces/',
                              namespace_name) + '/Relays/' + _str(queue_name) + '/Metrics'

    def _get_get_metrics_data_queue_path(self, namespace_name, queue_name, metric, rollup, filter_expr):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Queues/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups/',
            _str(rollup),
            '/Values?',
            filter_expr
        ])

    def _get_get_metrics_data_topic_path(self, namespace_name, queue_name, metric, rollup, filter_expr):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Topics/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups/',
            _str(rollup),
            '/Values?',
            filter_expr
        ])

    def _get_get_metrics_data_hub_path(self, namespace_name, queue_name, metric, rollup, filter_expr):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/NotificationHubs/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups/',
            _str(rollup),
            '/Values?',
            filter_expr
        ])

    def _get_get_metrics_data_relay_path(self, namespace_name, queue_name, metric, rollup, filter_expr):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Relays/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups/',
            _str(rollup),
            '/Values?',
            filter_expr
        ])

    def _get_get_metrics_rollup_queue_path(self, namespace_name, queue_name, metric):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Queues/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups',
        ])

    def _get_get_metrics_rollup_topic_path(self, namespace_name, queue_name, metric):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Topics/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups',
        ])

    def _get_get_metrics_rollup_hub_path(self, namespace_name, queue_name, metric):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/NotificationHubs/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups',
        ])

    def _get_get_metrics_rollup_relay_path(self, namespace_name, queue_name, metric):
        return "".join([
            self._get_path('services/serviceBus/Namespaces/', namespace_name),
            '/Relays/',
            _str(queue_name),
            '/Metrics/',
            _str(metric),
            '/Rollups',
        ])
