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
import ast
import json
import sys

from datetime import datetime
from xml.dom import minidom
from azure import (
    WindowsAzureData,
    WindowsAzureError,
    xml_escape,
    _create_entry,
    _general_error_handler,
    _get_entry_properties,
    _get_child_nodes,
    _get_children_from_path,
    _get_first_child_node_value,
    _ERROR_MESSAGE_NOT_PEEK_LOCKED_ON_DELETE,
    _ERROR_MESSAGE_NOT_PEEK_LOCKED_ON_UNLOCK,
    _ERROR_QUEUE_NOT_FOUND,
    _ERROR_TOPIC_NOT_FOUND,
    )
from azure.http import HTTPError

# default rule name for subscription
DEFAULT_RULE_NAME = '$Default'

#-----------------------------------------------------------------------------
# Constants for Azure app environment settings.
AZURE_SERVICEBUS_NAMESPACE = 'AZURE_SERVICEBUS_NAMESPACE'
AZURE_SERVICEBUS_ACCESS_KEY = 'AZURE_SERVICEBUS_ACCESS_KEY'
AZURE_SERVICEBUS_ISSUER = 'AZURE_SERVICEBUS_ISSUER'

# namespace used for converting rules to objects
XML_SCHEMA_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'


class Queue(WindowsAzureData):

    ''' Queue class corresponding to Queue Description:
    http://msdn.microsoft.com/en-us/library/windowsazure/hh780773'''

    def __init__(self, lock_duration=None, max_size_in_megabytes=None,
                 requires_duplicate_detection=None, requires_session=None,
                 default_message_time_to_live=None,
                 dead_lettering_on_message_expiration=None,
                 duplicate_detection_history_time_window=None,
                 max_delivery_count=None, enable_batched_operations=None,
                 size_in_bytes=None, message_count=None):

        self.lock_duration = lock_duration
        self.max_size_in_megabytes = max_size_in_megabytes
        self.requires_duplicate_detection = requires_duplicate_detection
        self.requires_session = requires_session
        self.default_message_time_to_live = default_message_time_to_live
        self.dead_lettering_on_message_expiration = \
            dead_lettering_on_message_expiration
        self.duplicate_detection_history_time_window = \
            duplicate_detection_history_time_window
        self.max_delivery_count = max_delivery_count
        self.enable_batched_operations = enable_batched_operations
        self.size_in_bytes = size_in_bytes
        self.message_count = message_count


class Topic(WindowsAzureData):

    ''' Topic class corresponding to Topic Description:
    http://msdn.microsoft.com/en-us/library/windowsazure/hh780749. '''

    def __init__(self, default_message_time_to_live=None,
                 max_size_in_megabytes=None, requires_duplicate_detection=None,
                 duplicate_detection_history_time_window=None,
                 enable_batched_operations=None, size_in_bytes=None):

        self.default_message_time_to_live = default_message_time_to_live
        self.max_size_in_megabytes = max_size_in_megabytes
        self.requires_duplicate_detection = requires_duplicate_detection
        self.duplicate_detection_history_time_window = \
            duplicate_detection_history_time_window
        self.enable_batched_operations = enable_batched_operations
        self.size_in_bytes = size_in_bytes

    @property
    def max_size_in_mega_bytes(self):
        import warnings
        warnings.warn(
            'This attribute has been changed to max_size_in_megabytes.')
        return self.max_size_in_megabytes

    @max_size_in_mega_bytes.setter
    def max_size_in_mega_bytes(self, value):
        self.max_size_in_megabytes = value


class Subscription(WindowsAzureData):

    ''' Subscription class corresponding to Subscription Description:
    http://msdn.microsoft.com/en-us/library/windowsazure/hh780763. '''

    def __init__(self, lock_duration=None, requires_session=None,
                 default_message_time_to_live=None,
                 dead_lettering_on_message_expiration=None,
                 dead_lettering_on_filter_evaluation_exceptions=None,
                 enable_batched_operations=None, max_delivery_count=None,
                 message_count=None):

        self.lock_duration = lock_duration
        self.requires_session = requires_session
        self.default_message_time_to_live = default_message_time_to_live
        self.dead_lettering_on_message_expiration = \
            dead_lettering_on_message_expiration
        self.dead_lettering_on_filter_evaluation_exceptions = \
            dead_lettering_on_filter_evaluation_exceptions
        self.enable_batched_operations = enable_batched_operations
        self.max_delivery_count = max_delivery_count
        self.message_count = message_count


class Rule(WindowsAzureData):

    ''' Rule class corresponding to Rule Description:
    http://msdn.microsoft.com/en-us/library/windowsazure/hh780753. '''

    def __init__(self, filter_type=None, filter_expression=None,
                 action_type=None, action_expression=None):
        self.filter_type = filter_type
        self.filter_expression = filter_expression
        self.action_type = action_type
        self.action_expression = action_type


class Message(WindowsAzureData):

    ''' Message class that used in send message/get mesage apis. '''

    def __init__(self, body=None, service_bus_service=None, location=None,
                 custom_properties=None,
                 type='application/atom+xml;type=entry;charset=utf-8',
                 broker_properties=None):
        self.body = body
        self.location = location
        self.broker_properties = broker_properties
        self.custom_properties = custom_properties
        self.type = type
        self.service_bus_service = service_bus_service
        self._topic_name = None
        self._subscription_name = None
        self._queue_name = None

        if not service_bus_service:
            return

        # if location is set, then extracts the queue name for queue message and
        # extracts the topic and subscriptions name if it is topic message.
        if location:
            if '/subscriptions/' in location:
                pos = location.find(service_bus_service.host_base.lower())+1
                pos1 = location.find('/subscriptions/')
                self._topic_name = location[pos+len(service_bus_service.host_base):pos1]
                pos = pos1 + len('/subscriptions/')
                pos1 = location.find('/', pos)
                self._subscription_name = location[pos:pos1]
            elif '/messages/' in location:
                pos = location.find(service_bus_service.host_base.lower())+1
                pos1 = location.find('/messages/')
                self._queue_name = location[pos+len(service_bus_service.host_base):pos1]

    def delete(self):
        ''' Deletes itself if find queue name or topic name and subscription
        name. '''
        if self._queue_name:
            self.service_bus_service.delete_queue_message(
                self._queue_name,
                self.broker_properties['SequenceNumber'],
                self.broker_properties['LockToken'])
        elif self._topic_name and self._subscription_name:
            self.service_bus_service.delete_subscription_message(
                self._topic_name,
                self._subscription_name,
                self.broker_properties['SequenceNumber'],
                self.broker_properties['LockToken'])
        else:
            raise WindowsAzureError(_ERROR_MESSAGE_NOT_PEEK_LOCKED_ON_DELETE)

    def unlock(self):
        ''' Unlocks itself if find queue name or topic name and subscription
        name. '''
        if self._queue_name:
            self.service_bus_service.unlock_queue_message(
                self._queue_name,
                self.broker_properties['SequenceNumber'],
                self.broker_properties['LockToken'])
        elif self._topic_name and self._subscription_name:
            self.service_bus_service.unlock_subscription_message(
                self._topic_name,
                self._subscription_name,
                self.broker_properties['SequenceNumber'],
                self.broker_properties['LockToken'])
        else:
            raise WindowsAzureError(_ERROR_MESSAGE_NOT_PEEK_LOCKED_ON_UNLOCK)

    def add_headers(self, request):
        ''' add addtional headers to request for message request.'''

        # Adds custom properties
        if self.custom_properties:
            for name, value in self.custom_properties.items():
                if sys.version_info < (3,) and isinstance(value, unicode):
                    request.headers.append(
                        (name, '"' + value.encode('utf-8') + '"'))
                elif isinstance(value, str):
                    request.headers.append((name, '"' + str(value) + '"'))
                elif isinstance(value, datetime):
                    request.headers.append(
                        (name, '"' + value.strftime('%a, %d %b %Y %H:%M:%S GMT') + '"'))
                else:
                    request.headers.append((name, str(value).lower()))

        # Adds content-type
        request.headers.append(('Content-Type', self.type))

        # Adds BrokerProperties
        if self.broker_properties:
            request.headers.append(
                ('BrokerProperties', str(self.broker_properties)))

        return request.headers


def _create_message(response, service_instance):
    ''' Create message from response.

    response: response from service bus cloud server.
    service_instance: the service bus client.
    '''
    respbody = response.body
    custom_properties = {}
    broker_properties = None
    message_type = None
    message_location = None

    # gets all information from respheaders.
    for name, value in response.headers:
        if name.lower() == 'brokerproperties':
            broker_properties = json.loads(value)
        elif name.lower() == 'content-type':
            message_type = value
        elif name.lower() == 'location':
            message_location = value
        elif name.lower() not in ['content-type',
                                  'brokerproperties',
                                  'transfer-encoding',
                                  'server',
                                  'location',
                                  'date']:
            if '"' in value:
                value = value[1:-1]
                try:
                    custom_properties[name] = datetime.strptime(
                        value, '%a, %d %b %Y %H:%M:%S GMT')
                except ValueError:
                    custom_properties[name] = value
            else:  # only int, float or boolean
                if value.lower() == 'true':
                    custom_properties[name] = True
                elif value.lower() == 'false':
                    custom_properties[name] = False
                # int('3.1') doesn't work so need to get float('3.14') first
                elif str(int(float(value))) == value:
                    custom_properties[name] = int(value)
                else:
                    custom_properties[name] = float(value)

    if message_type == None:
        message = Message(
            respbody, service_instance, message_location, custom_properties,
            'application/atom+xml;type=entry;charset=utf-8', broker_properties)
    else:
        message = Message(respbody, service_instance, message_location,
                          custom_properties, message_type, broker_properties)
    return message

# convert functions


def _convert_response_to_rule(response):
    return _convert_xml_to_rule(response.body)


def _convert_xml_to_rule(xmlstr):
    ''' Converts response xml to rule object.

    The format of xml for rule:
<entry xmlns='http://www.w3.org/2005/Atom'>
<content type='application/xml'>
<RuleDescription
    xmlns:i="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">
    <Filter i:type="SqlFilterExpression">
        <SqlExpression>MyProperty='XYZ'</SqlExpression>
    </Filter>
    <Action i:type="SqlFilterAction">
        <SqlExpression>set MyProperty2 = 'ABC'</SqlExpression>
    </Action>
</RuleDescription>
</content>
</entry>
    '''
    xmldoc = minidom.parseString(xmlstr)
    rule = Rule()

    for rule_desc in _get_children_from_path(xmldoc,
                                             'entry',
                                             'content',
                                             'RuleDescription'):
        for xml_filter in _get_child_nodes(rule_desc, 'Filter'):
            filter_type = xml_filter.getAttributeNS(
                XML_SCHEMA_NAMESPACE, 'type')
            setattr(rule, 'filter_type', str(filter_type))
            if xml_filter.childNodes:

                for expr in _get_child_nodes(xml_filter, 'SqlExpression'):
                    setattr(rule, 'filter_expression',
                            expr.firstChild.nodeValue)

        for xml_action in _get_child_nodes(rule_desc, 'Action'):
            action_type = xml_action.getAttributeNS(
                XML_SCHEMA_NAMESPACE, 'type')
            setattr(rule, 'action_type', str(action_type))
            if xml_action.childNodes:
                action_expression = xml_action.childNodes[0].firstChild
                if action_expression:
                    setattr(rule, 'action_expression',
                            action_expression.nodeValue)

    # extract id, updated and name value from feed entry and set them of rule.
    for name, value in _get_entry_properties(xmlstr, True, '/rules').items():
        setattr(rule, name, value)

    return rule


def _convert_response_to_queue(response):
    return _convert_xml_to_queue(response.body)


def _parse_bool(value):
    if value.lower() == 'true':
        return True
    return False


def _convert_xml_to_queue(xmlstr):
    ''' Converts xml response to queue object.

    The format of xml response for queue:
<QueueDescription
    xmlns=\"http://schemas.microsoft.com/netservices/2010/10/servicebus/connect\">
    <MaxSizeInBytes>10000</MaxSizeInBytes>
    <DefaultMessageTimeToLive>PT5M</DefaultMessageTimeToLive>
    <LockDuration>PT2M</LockDuration>
    <RequiresGroupedReceives>False</RequiresGroupedReceives>
    <SupportsDuplicateDetection>False</SupportsDuplicateDetection>
    ...
</QueueDescription>

    '''
    xmldoc = minidom.parseString(xmlstr)
    queue = Queue()

    invalid_queue = True
    # get node for each attribute in Queue class, if nothing found then the
    # response is not valid xml for Queue.
    for desc in _get_children_from_path(xmldoc,
                                        'entry',
                                        'content',
                                        'QueueDescription'):
        node_value = _get_first_child_node_value(desc, 'LockDuration')
        if node_value is not None:
            queue.lock_duration = node_value
            invalid_queue = False

        node_value = _get_first_child_node_value(desc, 'MaxSizeInMegabytes')
        if node_value is not None:
            queue.max_size_in_megabytes = int(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(
            desc, 'RequiresDuplicateDetection')
        if node_value is not None:
            queue.requires_duplicate_detection = _parse_bool(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(desc, 'RequiresSession')
        if node_value is not None:
            queue.requires_session = _parse_bool(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(
            desc, 'DefaultMessageTimeToLive')
        if node_value is not None:
            queue.default_message_time_to_live = node_value
            invalid_queue = False

        node_value = _get_first_child_node_value(
            desc, 'DeadLetteringOnMessageExpiration')
        if node_value is not None:
            queue.dead_lettering_on_message_expiration = _parse_bool(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(
            desc, 'DuplicateDetectionHistoryTimeWindow')
        if node_value is not None:
            queue.duplicate_detection_history_time_window = node_value
            invalid_queue = False

        node_value = _get_first_child_node_value(
            desc, 'EnableBatchedOperations')
        if node_value is not None:
            queue.enable_batched_operations = _parse_bool(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(desc, 'MaxDeliveryCount')
        if node_value is not None:
            queue.max_delivery_count = int(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(desc, 'MessageCount')
        if node_value is not None:
            queue.message_count = int(node_value)
            invalid_queue = False

        node_value = _get_first_child_node_value(desc, 'SizeInBytes')
        if node_value is not None:
            queue.size_in_bytes = int(node_value)
            invalid_queue = False

    if invalid_queue:
        raise WindowsAzureError(_ERROR_QUEUE_NOT_FOUND)

    # extract id, updated and name value from feed entry and set them of queue.
    for name, value in _get_entry_properties(xmlstr, True).items():
        setattr(queue, name, value)

    return queue


def _convert_response_to_topic(response):
    return _convert_xml_to_topic(response.body)


def _convert_xml_to_topic(xmlstr):
    '''Converts xml response to topic

    The xml format for topic:
<entry xmlns='http://www.w3.org/2005/Atom'>
    <content type='application/xml'>
    <TopicDescription
        xmlns:i="http://www.w3.org/2001/XMLSchema-instance"
        xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">
        <DefaultMessageTimeToLive>P10675199DT2H48M5.4775807S</DefaultMessageTimeToLive>
        <MaxSizeInMegabytes>1024</MaxSizeInMegabytes>
        <RequiresDuplicateDetection>false</RequiresDuplicateDetection>
        <DuplicateDetectionHistoryTimeWindow>P7D</DuplicateDetectionHistoryTimeWindow>
        <DeadLetteringOnFilterEvaluationExceptions>true</DeadLetteringOnFilterEvaluationExceptions>
    </TopicDescription>
    </content>
</entry>
    '''
    xmldoc = minidom.parseString(xmlstr)
    topic = Topic()

    invalid_topic = True

    # get node for each attribute in Topic class, if nothing found then the
    # response is not valid xml for Topic.
    for desc in _get_children_from_path(xmldoc,
                                        'entry',
                                        'content',
                                        'TopicDescription'):
        invalid_topic = True
        node_value = _get_first_child_node_value(
            desc, 'DefaultMessageTimeToLive')
        if node_value is not None:
            topic.default_message_time_to_live = node_value
            invalid_topic = False
        node_value = _get_first_child_node_value(desc, 'MaxSizeInMegabytes')
        if node_value is not None:
            topic.max_size_in_megabytes = int(node_value)
            invalid_topic = False
        node_value = _get_first_child_node_value(
            desc, 'RequiresDuplicateDetection')
        if node_value is not None:
            topic.requires_duplicate_detection = _parse_bool(node_value)
            invalid_topic = False
        node_value = _get_first_child_node_value(
            desc, 'DuplicateDetectionHistoryTimeWindow')
        if node_value is not None:
            topic.duplicate_detection_history_time_window = node_value
            invalid_topic = False
        node_value = _get_first_child_node_value(
            desc, 'EnableBatchedOperations')
        if node_value is not None:
            topic.enable_batched_operations = _parse_bool(node_value)
            invalid_topic = False
        node_value = _get_first_child_node_value(desc, 'SizeInBytes')
        if node_value is not None:
            topic.size_in_bytes = int(node_value)
            invalid_topic = False

    if invalid_topic:
        raise WindowsAzureError(_ERROR_TOPIC_NOT_FOUND)

    # extract id, updated and name value from feed entry and set them of topic.
    for name, value in _get_entry_properties(xmlstr, True).items():
        setattr(topic, name, value)
    return topic


def _convert_response_to_subscription(response):
    return _convert_xml_to_subscription(response.body)


def _convert_xml_to_subscription(xmlstr):
    '''Converts xml response to subscription

    The xml format for subscription:
<entry xmlns='http://www.w3.org/2005/Atom'>
    <content type='application/xml'>
    <SubscriptionDescription
        xmlns:i="http://www.w3.org/2001/XMLSchema-instance"
        xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">
        <LockDuration>PT5M</LockDuration>
        <RequiresSession>false</RequiresSession>
        <DefaultMessageTimeToLive>P10675199DT2H48M5.4775807S</DefaultMessageTimeToLive>
        <DeadLetteringOnMessageExpiration>false</DeadLetteringOnMessageExpiration>
        <DeadLetteringOnFilterEvaluationExceptions>true</DeadLetteringOnFilterEvaluationExceptions>
    </SubscriptionDescription>
    </content>
</entry>
    '''
    xmldoc = minidom.parseString(xmlstr)
    subscription = Subscription()

    for desc in _get_children_from_path(xmldoc,
                                        'entry',
                                        'content',
                                        'SubscriptionDescription'):
        node_value = _get_first_child_node_value(desc, 'LockDuration')
        if node_value is not None:
            subscription.lock_duration = node_value

        node_value = _get_first_child_node_value(
            desc, 'RequiresSession')
        if node_value is not None:
            subscription.requires_session = _parse_bool(node_value)

        node_value = _get_first_child_node_value(
            desc, 'DefaultMessageTimeToLive')
        if node_value is not None:
            subscription.default_message_time_to_live = node_value

        node_value = _get_first_child_node_value(
            desc, 'DeadLetteringOnFilterEvaluationExceptions')
        if node_value is not None:
            subscription.dead_lettering_on_filter_evaluation_exceptions = \
                _parse_bool(node_value)

        node_value = _get_first_child_node_value(
            desc, 'DeadLetteringOnMessageExpiration')
        if node_value is not None:
            subscription.dead_lettering_on_message_expiration = \
                _parse_bool(node_value)

        node_value = _get_first_child_node_value(
            desc, 'EnableBatchedOperations')
        if node_value is not None:
            subscription.enable_batched_operations = _parse_bool(node_value)

        node_value = _get_first_child_node_value(
            desc, 'MaxDeliveryCount')
        if node_value is not None:
            subscription.max_delivery_count = int(node_value)

        node_value = _get_first_child_node_value(
            desc, 'MessageCount')
        if node_value is not None:
            subscription.message_count = int(node_value)

    for name, value in _get_entry_properties(xmlstr,
                                             True,
                                             '/subscriptions').items():
        setattr(subscription, name, value)

    return subscription


def _convert_subscription_to_xml(subscription):
    '''
    Converts a subscription object to xml to send.  The order of each field of
    subscription in xml is very important so we can't simple call
    convert_class_to_xml.

    subscription: the subsciption object to be converted.
    '''

    subscription_body = '<SubscriptionDescription xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">'
    if subscription:
        if subscription.lock_duration is not None:
            subscription_body += ''.join(
                ['<LockDuration>',
                 str(subscription.lock_duration),
                 '</LockDuration>'])

        if subscription.requires_session is not None:
            subscription_body += ''.join(
                ['<RequiresSession>',
                 str(subscription.requires_session).lower(),
                 '</RequiresSession>'])

        if subscription.default_message_time_to_live is not None:
            subscription_body += ''.join(
                ['<DefaultMessageTimeToLive>',
                 str(subscription.default_message_time_to_live),
                 '</DefaultMessageTimeToLive>'])

        if subscription.dead_lettering_on_message_expiration is not None:
            subscription_body += ''.join(
                ['<DeadLetteringOnMessageExpiration>',
                 str(subscription.dead_lettering_on_message_expiration).lower(),
                 '</DeadLetteringOnMessageExpiration>'])

        if subscription.dead_lettering_on_filter_evaluation_exceptions is not None:
            subscription_body += ''.join(
                ['<DeadLetteringOnFilterEvaluationExceptions>',
                 str(subscription.dead_lettering_on_filter_evaluation_exceptions).lower(),
                 '</DeadLetteringOnFilterEvaluationExceptions>'])

        if subscription.enable_batched_operations is not None:
            subscription_body += ''.join(
                ['<EnableBatchedOperations>',
                 str(subscription.enable_batched_operations).lower(),
                 '</EnableBatchedOperations>'])

        if subscription.max_delivery_count is not None:
            subscription_body += ''.join(
                ['<MaxDeliveryCount>',
                 str(subscription.max_delivery_count),
                 '</MaxDeliveryCount>'])

        if subscription.message_count is not None:
            subscription_body += ''.join(
                ['<MessageCount>',
                 str(subscription.message_count),
                 '</MessageCount>'])

    subscription_body += '</SubscriptionDescription>'
    return _create_entry(subscription_body)


def _convert_rule_to_xml(rule):
    '''
    Converts a rule object to xml to send.  The order of each field of rule
    in xml is very important so we cann't simple call convert_class_to_xml.

    rule: the rule object to be converted.
    '''
    rule_body = '<RuleDescription xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">'
    if rule:
        if rule.filter_type:
            rule_body += ''.join(
                ['<Filter i:type="',
                 xml_escape(rule.filter_type),
                 '">'])
            if rule.filter_type == 'CorrelationFilter':
                rule_body += ''.join(
                    ['<CorrelationId>',
                     xml_escape(rule.filter_expression),
                     '</CorrelationId>'])
            else:
                rule_body += ''.join(
                    ['<SqlExpression>',
                     xml_escape(rule.filter_expression),
                     '</SqlExpression>'])
                rule_body += '<CompatibilityLevel>20</CompatibilityLevel>'
            rule_body += '</Filter>'
        if rule.action_type:
            rule_body += ''.join(
                ['<Action i:type="',
                 xml_escape(rule.action_type),
                 '">'])
            if rule.action_type == 'SqlRuleAction':
                rule_body += ''.join(
                    ['<SqlExpression>',
                     xml_escape(rule.action_expression),
                     '</SqlExpression>'])
                rule_body += '<CompatibilityLevel>20</CompatibilityLevel>'
            rule_body += '</Action>'
    rule_body += '</RuleDescription>'

    return _create_entry(rule_body)


def _convert_topic_to_xml(topic):
    '''
    Converts a topic object to xml to send.  The order of each field of topic
    in xml is very important so we cann't simple call convert_class_to_xml.

    topic: the topic object to be converted.
    '''

    topic_body = '<TopicDescription xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">'
    if topic:
        if topic.default_message_time_to_live is not None:
            topic_body += ''.join(
                ['<DefaultMessageTimeToLive>',
                 str(topic.default_message_time_to_live),
                 '</DefaultMessageTimeToLive>'])

        if topic.max_size_in_megabytes is not None:
            topic_body += ''.join(
                ['<MaxSizeInMegabytes>',
                 str(topic.max_size_in_megabytes),
                 '</MaxSizeInMegabytes>'])

        if topic.requires_duplicate_detection is not None:
            topic_body += ''.join(
                ['<RequiresDuplicateDetection>',
                 str(topic.requires_duplicate_detection).lower(),
                 '</RequiresDuplicateDetection>'])

        if topic.duplicate_detection_history_time_window is not None:
            topic_body += ''.join(
                ['<DuplicateDetectionHistoryTimeWindow>',
                 str(topic.duplicate_detection_history_time_window),
                 '</DuplicateDetectionHistoryTimeWindow>'])

        if topic.enable_batched_operations is not None:
            topic_body += ''.join(
                ['<EnableBatchedOperations>',
                 str(topic.enable_batched_operations).lower(),
                 '</EnableBatchedOperations>'])

        if topic.size_in_bytes is not None:
            topic_body += ''.join(
                ['<SizeInBytes>',
                 str(topic.size_in_bytes),
                 '</SizeInBytes>'])

    topic_body += '</TopicDescription>'

    return _create_entry(topic_body)


def _convert_queue_to_xml(queue):
    '''
    Converts a queue object to xml to send.  The order of each field of queue
    in xml is very important so we cann't simple call convert_class_to_xml.

    queue: the queue object to be converted.
    '''
    queue_body = '<QueueDescription xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/netservices/2010/10/servicebus/connect">'
    if queue:
        if queue.lock_duration:
            queue_body += ''.join(
                ['<LockDuration>',
                 str(queue.lock_duration),
                 '</LockDuration>'])

        if queue.max_size_in_megabytes is not None:
            queue_body += ''.join(
                ['<MaxSizeInMegabytes>',
                 str(queue.max_size_in_megabytes),
                 '</MaxSizeInMegabytes>'])

        if queue.requires_duplicate_detection is not None:
            queue_body += ''.join(
                ['<RequiresDuplicateDetection>',
                 str(queue.requires_duplicate_detection).lower(),
                 '</RequiresDuplicateDetection>'])

        if queue.requires_session is not None:
            queue_body += ''.join(
                ['<RequiresSession>',
                 str(queue.requires_session).lower(),
                 '</RequiresSession>'])

        if queue.default_message_time_to_live is not None:
            queue_body += ''.join(
                ['<DefaultMessageTimeToLive>',
                 str(queue.default_message_time_to_live),
                 '</DefaultMessageTimeToLive>'])

        if queue.dead_lettering_on_message_expiration is not None:
            queue_body += ''.join(
                ['<DeadLetteringOnMessageExpiration>',
                 str(queue.dead_lettering_on_message_expiration).lower(),
                 '</DeadLetteringOnMessageExpiration>'])

        if queue.duplicate_detection_history_time_window is not None:
            queue_body += ''.join(
                ['<DuplicateDetectionHistoryTimeWindow>',
                 str(queue.duplicate_detection_history_time_window),
                 '</DuplicateDetectionHistoryTimeWindow>'])

        if queue.max_delivery_count is not None:
            queue_body += ''.join(
                ['<MaxDeliveryCount>',
                 str(queue.max_delivery_count),
                 '</MaxDeliveryCount>'])

        if queue.enable_batched_operations is not None:
            queue_body += ''.join(
                ['<EnableBatchedOperations>',
                 str(queue.enable_batched_operations).lower(),
                 '</EnableBatchedOperations>'])

        if queue.size_in_bytes is not None:
            queue_body += ''.join(
                ['<SizeInBytes>',
                 str(queue.size_in_bytes),
                 '</SizeInBytes>'])

        if queue.message_count is not None:
            queue_body += ''.join(
                ['<MessageCount>',
                 str(queue.message_count),
                 '</MessageCount>'])

    queue_body += '</QueueDescription>'
    return _create_entry(queue_body)


def _service_bus_error_handler(http_error):
    ''' Simple error handler for service bus service. '''
    return _general_error_handler(http_error)

from azure.servicebus.servicebusservice import ServiceBusService
