# Copyright (c) 2012 Andy Davidoff http://www.disruptek.com/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import xml.sax
import hashlib
import base64
import string
from boto.connection import AWSQueryConnection
from boto.mws.exception import ResponseErrorFactory
from boto.mws.response import ResponseFactory, ResponseElement
from boto.handler import XmlHandler
import boto.mws.response

__all__ = ['MWSConnection']

api_version_path = {
    'Feeds':        ('2009-01-01', 'Merchant', '/'),
    'Reports':      ('2009-01-01', 'Merchant', '/'),
    'Orders':       ('2011-01-01', 'SellerId', '/Orders/2011-01-01'),
    'Products':     ('2011-10-01', 'SellerId', '/Products/2011-10-01'),
    'Sellers':      ('2011-07-01', 'SellerId', '/Sellers/2011-07-01'),
    'Inbound':      ('2010-10-01', 'SellerId',
                     '/FulfillmentInboundShipment/2010-10-01'),
    'Outbound':     ('2010-10-01', 'SellerId',
                     '/FulfillmentOutboundShipment/2010-10-01'),
    'Inventory':    ('2010-10-01', 'SellerId',
                     '/FulfillmentInventory/2010-10-01'),
}
content_md5 = lambda c: base64.encodestring(hashlib.md5(c).digest()).strip()
decorated_attrs = ('action', 'response', 'section',
                   'quota', 'restore', 'version')
api_call_map = {}


def add_attrs_from(func, to):
    for attr in decorated_attrs:
        setattr(to, attr, getattr(func, attr, None))
    return to


def structured_lists(*fields):

    def decorator(func):

        def wrapper(self, *args, **kw):
            for key, acc in [f.split('.') for f in fields]:
                if key in kw:
                    newkey = key + '.' + acc + (acc and '.' or '')
                    for i in range(len(kw[key])):
                        kw[newkey + str(i + 1)] = kw[key][i]
                    kw.pop(key)
            return func(self, *args, **kw)
        wrapper.__doc__ = "{0}\nLists: {1}".format(func.__doc__,
                                                   ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def http_body(field):

    def decorator(func):

        def wrapper(*args, **kw):
            if filter(lambda x: not x in kw, (field, 'content_type')):
                message = "{0} requires {1} and content_type arguments for " \
                          "building HTTP body".format(func.action, field)
                raise KeyError(message)
            kw['body'] = kw.pop(field)
            kw['headers'] = {
                'Content-Type': kw.pop('content_type'),
                'Content-MD5':  content_md5(kw['body']),
            }
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nRequired HTTP Body: " \
                          "{1}".format(func.__doc__, field)
        return add_attrs_from(func, to=wrapper)
    return decorator


def destructure_object(value, into={}, prefix=''):
    if isinstance(value, ResponseElement):
        for name, attr in value.__dict__.items():
            if name.startswith('_'):
                continue
            destructure_object(attr, into=into, prefix=prefix + '.' + name)
    elif filter(lambda x: isinstance(value, x), (list, set, tuple)):
        for index, element in [(prefix + '.' + str(i + 1), value[i])
                               for i in range(len(value))]:
            destructure_object(element, into=into, prefix=index)
    elif isinstance(value, bool):
        into[prefix] = str(value).lower()
    else:
        into[prefix] = value


def structured_objects(*fields):

    def decorator(func):

        def wrapper(*args, **kw):
            for field in filter(kw.has_key, fields):
                destructure_object(kw.pop(field), into=kw, prefix=field)
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nObjects: {1}".format(func.__doc__,
                                                     ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def requires(*groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda x: len(x) == len(filter(kw.has_key, x))
            if 1 != len(filter(hasgroup, groups)):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} requires {1} argument(s)" \
                          "".format(func.action, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\nRequired: {1}".format(func.__doc__,
                                                      message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def exclusive(*groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda x: len(x) == len(filter(kw.has_key, x))
            if len(filter(hasgroup, groups)) not in (0, 1):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} requires either {1}" \
                          "".format(func.action, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\nEither: {1}".format(func.__doc__,
                                                    message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def dependent(field, *groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda x: len(x) == len(filter(kw.has_key, x))
            if field in kw and 1 > len(filter(hasgroup, groups)):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} argument {1} requires {2}" \
                          "".format(func.action, field, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\n{1} requires: {2}".format(func.__doc__,
                                                          field,
                                                          message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def requires_some_of(*fields):

    def decorator(func):

        def wrapper(*args, **kw):
            if not filter(kw.has_key, fields):
                message = "{0} requires at least one of {1} argument(s)" \
                          "".format(func.action, ', '.join(fields))
                raise KeyError(message)
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nSome Required: {1}".format(func.__doc__,
                                                           ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def boolean_arguments(*fields):

    def decorator(func):

        def wrapper(*args, **kw):
            for field in filter(lambda x: isinstance(kw.get(x), bool), fields):
                kw[field] = str(kw[field]).lower()
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nBooleans: {1}".format(func.__doc__,
                                                      ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def api_action(section, quota, restore, *api):

    def decorator(func, quota=int(quota), restore=float(restore)):
        version, accesskey, path = api_version_path[section]
        action = ''.join(api or map(str.capitalize, func.func_name.split('_')))
        if hasattr(boto.mws.response, action + 'Response'):
            response = getattr(boto.mws.response, action + 'Response')
        else:
            response = ResponseFactory(action)
        response._action = action

        def wrapper(self, *args, **kw):
            kw.setdefault(accesskey, getattr(self, accesskey, None))
            if kw[accesskey] is None:
                message = "{0} requires {1} argument. Set the " \
                          "MWSConnection.{2} attribute?" \
                          "".format(action, accesskey, accesskey)
                raise KeyError(message)
            kw['Action'] = action
            kw['Version'] = version
            return func(self, path, response, *args, **kw)
        for attr in decorated_attrs:
            setattr(wrapper, attr, locals().get(attr))
        wrapper.__doc__ = "MWS {0}/{1} API call; quota={2} restore={3:.2f}\n" \
                          "{4}".format(action, version, quota, restore,
                                       func.__doc__)
        api_call_map[action] = func.func_name
        return wrapper
    return decorator


class MWSConnection(AWSQueryConnection):

    ResponseError = ResponseErrorFactory

    def __init__(self, *args, **kw):
        kw.setdefault('host', 'mws.amazonservices.com')
        self.Merchant = kw.pop('Merchant', None) or kw.get('SellerId')
        self.SellerId = kw.pop('SellerId', None) or self.Merchant
        super(MWSConnection, self).__init__(*args, **kw)

    def _required_auth_capability(self):
        return ['mws']

    def post_request(self, path, params, cls, body='', headers={}, isXML=True):
        """Make a POST request, optionally with a content body,
           and return the response, optionally as raw text.
           Modelled off of the inherited get_object/make_request flow.
        """
        request = self.build_base_http_request('POST', path, None, data=body,
                                               params=params, headers=headers,
                                               host=self.host)
        response = self._mexe(request, override_num_retries=None)
        body = response.read()
        boto.log.debug(body)
        if not body:
            boto.log.error('Null body %s' % body)
            raise self.ResponseError(response.status, response.reason, body)
        if response.status != 200:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)
        if not isXML:
            digest = response.getheader('Content-MD5')
            assert content_md5(body) == digest
            return body
        return self._parse_response(cls, body)

    def _parse_response(self, cls, body):
        obj = cls(self)
        h = XmlHandler(obj, self)
        xml.sax.parseString(body, h)
        return obj

    def method_for(self, name):
        """Return the MWS API method referred to in the argument.
           The named method can be in CamelCase or underlined_lower_case.
           This is the complement to MWSConnection.any_call.action
        """
        action = '_' in name and string.capwords(name, '_') or name
        if action in api_call_map:
            return getattr(self, api_call_map[action])
        return None

    def iter_call(self, call, *args, **kw):
        """Pass a call name as the first argument and a generator
           is returned for the initial response and any continuation
           call responses made using the NextToken.
        """
        method = self.method_for(call)
        assert method, 'No call named "{0}"'.format(call)
        return self.iter_response(method(*args, **kw))

    def iter_response(self, response):
        """Pass a call's response as the initial argument and a
           generator is returned for the initial response and any
           continuation call responses made using the NextToken.
        """
        yield response
        more = self.method_for(response._action + 'ByNextToken')
        while more and response._result.HasNext == 'true':
            response = more(NextToken=response._result.NextToken)
            yield response

    @boolean_arguments('PurgeAndReplace')
    @http_body('FeedContent')
    @structured_lists('MarketplaceIdList.Id')
    @requires(['FeedType'])
    @api_action('Feeds', 15, 120)
    def submit_feed(self, path, response, headers={}, body='', **kw):
        """Uploads a feed for processing by Amazon MWS.
        """
        return self.post_request(path, kw, response, body=body,
                                 headers=headers)

    @structured_lists('FeedSubmissionIdList.Id', 'FeedTypeList.Type',
                      'FeedProcessingStatusList.Status')
    @api_action('Feeds', 10, 45)
    def get_feed_submission_list(self, path, response, **kw):
        """Returns a list of all feed submissions submitted in the
           previous 90 days.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Feeds', 0, 0)
    def get_feed_submission_list_by_next_token(self, path, response, **kw):
        """Returns a list of feed submissions using the NextToken parameter.
        """
        return self.post_request(path, kw, response)

    @structured_lists('FeedTypeList.Type', 'FeedProcessingStatusList.Status')
    @api_action('Feeds', 10, 45)
    def get_feed_submission_count(self, path, response, **kw):
        """Returns a count of the feeds submitted in the previous 90 days.
        """
        return self.post_request(path, kw, response)

    @structured_lists('FeedSubmissionIdList.Id', 'FeedTypeList.Type')
    @api_action('Feeds', 10, 45)
    def cancel_feed_submissions(self, path, response, **kw):
        """Cancels one or more feed submissions and returns a
           count of the feed submissions that were canceled.
        """
        return self.post_request(path, kw, response)

    @requires(['FeedSubmissionId'])
    @api_action('Feeds', 15, 60)
    def get_feed_submission_result(self, path, response, **kw):
        """Returns the feed processing report.
        """
        return self.post_request(path, kw, response, isXML=False)

    def get_service_status(self, **kw):
        """Instruct the user on how to get service status.
        """
        sections = ', '.join(map(str.lower, api_version_path.keys()))
        message = "Use {0}.get_(section)_service_status(), " \
                  "where (section) is one of the following: " \
                  "{1}".format(self.__class__.__name__, sections)
        raise AttributeError(message)

    @structured_lists('MarketplaceIdList.Id')
    @boolean_arguments('ReportOptions=ShowSalesChannel')
    @requires(['ReportType'])
    @api_action('Reports', 15, 60)
    def request_report(self, path, response, **kw):
        """Creates a report request and submits the request to Amazon MWS.
        """
        return self.post_request(path, kw, response)

    @structured_lists('ReportRequestIdList.Id', 'ReportTypeList.Type',
                      'ReportProcessingStatusList.Status')
    @api_action('Reports', 10, 45)
    def get_report_request_list(self, path, response, **kw):
        """Returns a list of report requests that you can use to get the
           ReportRequestId for a report.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_request_list_by_next_token(self, path, response, **kw):
        """Returns a list of report requests using the NextToken,
           which was supplied by a previous request to either
           GetReportRequestListByNextToken or GetReportRequestList, where
           the value of HasNext was true in that previous request.
        """
        return self.post_request(path, kw, response)

    @structured_lists('ReportTypeList.Type',
                      'ReportProcessingStatusList.Status')
    @api_action('Reports', 10, 45)
    def get_report_request_count(self, path, response, **kw):
        """Returns a count of report requests that have been submitted
           to Amazon MWS for processing.
        """
        return self.post_request(path, kw, response)

    @api_action('Reports', 10, 45)
    def cancel_report_requests(self, path, response, **kw):
        """Cancel one or more report requests, returning the count of the
           canceled report requests and the report request information.
        """
        return self.post_request(path, kw, response)

    @boolean_arguments('Acknowledged')
    @structured_lists('ReportRequestIdList.Id', 'ReportTypeList.Type')
    @api_action('Reports', 10, 60)
    def get_report_list(self, path, response, **kw):
        """Returns a list of reports that were created in the previous
           90 days that match the query parameters.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_list_by_next_token(self, path, response, **kw):
        """Returns a list of reports using the NextToken, which
           was supplied by a previous request to either
           GetReportListByNextToken or GetReportList, where the
           value of HasNext was true in the previous call.
        """
        return self.post_request(path, kw, response)

    @boolean_arguments('Acknowledged')
    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_count(self, path, response, **kw):
        """Returns a count of the reports, created in the previous 90 days,
           with a status of _DONE_ and that are available for download.
        """
        return self.post_request(path, kw, response)

    @requires(['ReportId'])
    @api_action('Reports', 15, 60)
    def get_report(self, path, response, **kw):
        """Returns the contents of a report.
        """
        return self.post_request(path, kw, response, isXML=False)

    @requires(['ReportType', 'Schedule'])
    @api_action('Reports', 10, 45)
    def manage_report_schedule(self, path, response, **kw):
        """Creates, updates, or deletes a report request schedule for
           a specified report type.
        """
        return self.post_request(path, kw, response)

    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_schedule_list(self, path, response, **kw):
        """Returns a list of order report requests that are scheduled
           to be submitted to Amazon MWS for processing.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_schedule_list_by_next_token(self, path, response, **kw):
        """Returns a list of report requests using the NextToken,
           which was supplied by a previous request to either
           GetReportScheduleListByNextToken or GetReportScheduleList,
           where the value of HasNext was true in that previous request.
        """
        return self.post_request(path, kw, response)

    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_schedule_count(self, path, response, **kw):
        """Returns a count of order report requests that are scheduled
           to be submitted to Amazon MWS.
        """
        return self.post_request(path, kw, response)

    @boolean_arguments('Acknowledged')
    @requires(['ReportIdList'])
    @structured_lists('ReportIdList.Id')
    @api_action('Reports', 10, 45)
    def update_report_acknowledgements(self, path, response, **kw):
        """Updates the acknowledged status of one or more reports.
        """
        return self.post_request(path, kw, response)

    @requires(['ShipFromAddress', 'InboundShipmentPlanRequestItems'])
    @structured_objects('ShipFromAddress', 'InboundShipmentPlanRequestItems')
    @api_action('Inbound', 30, 0.5)
    def create_inbound_shipment_plan(self, path, response, **kw):
        """Returns the information required to create an inbound shipment.
        """
        return self.post_request(path, kw, response)

    @requires(['ShipmentId', 'InboundShipmentHeader', 'InboundShipmentItems'])
    @structured_objects('InboundShipmentHeader', 'InboundShipmentItems')
    @api_action('Inbound', 30, 0.5)
    def create_inbound_shipment(self, path, response, **kw):
        """Creates an inbound shipment.
        """
        return self.post_request(path, kw, response)

    @requires(['ShipmentId'])
    @structured_objects('InboundShipmentHeader', 'InboundShipmentItems')
    @api_action('Inbound', 30, 0.5)
    def update_inbound_shipment(self, path, response, **kw):
        """Updates an existing inbound shipment.  Amazon documentation
           is ambiguous as to whether the InboundShipmentHeader and
           InboundShipmentItems arguments are required.
        """
        return self.post_request(path, kw, response)

    @requires_some_of('ShipmentIdList', 'ShipmentStatusList')
    @structured_lists('ShipmentIdList.Id', 'ShipmentStatusList.Status')
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipments(self, path, response, **kw):
        """Returns a list of inbound shipments based on criteria that
           you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipments_by_next_token(self, path, response, **kw):
        """Returns the next page of inbound shipments using the NextToken
           parameter.
        """
        return self.post_request(path, kw, response)

    @requires(['ShipmentId'], ['LastUpdatedAfter', 'LastUpdatedBefore'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipment_items(self, path, response, **kw):
        """Returns a list of items in a specified inbound shipment, or a
           list of items that were updated within a specified time frame.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipment_items_by_next_token(self, path, response, **kw):
        """Returns the next page of inbound shipment items using the
           NextToken parameter.
        """
        return self.post_request(path, kw, response)

    @api_action('Inbound', 2, 300, 'GetServiceStatus')
    def get_inbound_service_status(self, path, response, **kw):
        """Returns the operational status of the Fulfillment Inbound
           Shipment API section.
        """
        return self.post_request(path, kw, response)

    @requires(['SellerSkus'], ['QueryStartDateTime'])
    @structured_lists('SellerSkus.member')
    @api_action('Inventory', 30, 0.5)
    def list_inventory_supply(self, path, response, **kw):
        """Returns information about the availability of a seller's
           inventory.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Inventory', 30, 0.5)
    def list_inventory_supply_by_next_token(self, path, response, **kw):
        """Returns the next page of information about the availability
           of a seller's inventory using the NextToken parameter.
        """
        return self.post_request(path, kw, response)

    @api_action('Inventory', 2, 300, 'GetServiceStatus')
    def get_inventory_service_status(self, path, response, **kw):
        """Returns the operational status of the Fulfillment Inventory
           API section.
        """
        return self.post_request(path, kw, response)

    @requires(['PackageNumber'])
    @api_action('Outbound', 30, 0.5)
    def get_package_tracking_details(self, path, response, **kw):
        """Returns delivery tracking information for a package in
           an outbound shipment for a Multi-Channel Fulfillment order.
        """
        return self.post_request(path, kw, response)

    @structured_objects('Address', 'Items')
    @requires(['Address', 'Items'])
    @api_action('Outbound', 30, 0.5)
    def get_fulfillment_preview(self, path, response, **kw):
        """Returns a list of fulfillment order previews based on items
           and shipping speed categories that you specify.
        """
        return self.post_request(path, kw, response)

    @structured_objects('DestinationAddress', 'Items')
    @requires(['SellerFulfillmentOrderId', 'DisplayableOrderId',
               'ShippingSpeedCategory',    'DisplayableOrderDateTime',
               'DestinationAddress',       'DisplayableOrderComment',
               'Items'])
    @api_action('Outbound', 30, 0.5)
    def create_fulfillment_order(self, path, response, **kw):
        """Requests that Amazon ship items from the seller's inventory
           to a destination address.
        """
        return self.post_request(path, kw, response)

    @requires(['SellerFulfillmentOrderId'])
    @api_action('Outbound', 30, 0.5)
    def get_fulfillment_order(self, path, response, **kw):
        """Returns a fulfillment order based on a specified
           SellerFulfillmentOrderId.
        """
        return self.post_request(path, kw, response)

    @api_action('Outbound', 30, 0.5)
    def list_all_fulfillment_orders(self, path, response, **kw):
        """Returns a list of fulfillment orders fulfilled after (or
           at) a specified date or by fulfillment method.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Outbound', 30, 0.5)
    def list_all_fulfillment_orders_by_next_token(self, path, response, **kw):
        """Returns the next page of inbound shipment items using the
           NextToken parameter.
        """
        return self.post_request(path, kw, response)

    @requires(['SellerFulfillmentOrderId'])
    @api_action('Outbound', 30, 0.5)
    def cancel_fulfillment_order(self, path, response, **kw):
        """Requests that Amazon stop attempting to fulfill an existing
           fulfillment order.
        """
        return self.post_request(path, kw, response)

    @api_action('Outbound', 2, 300, 'GetServiceStatus')
    def get_outbound_service_status(self, path, response, **kw):
        """Returns the operational status of the Fulfillment Outbound
           API section.
        """
        return self.post_request(path, kw, response)

    @requires(['CreatedAfter'], ['LastUpdatedAfter'])
    @exclusive(['CreatedAfter'], ['LastUpdatedAfter'])
    @dependent('CreatedBefore', ['CreatedAfter'])
    @exclusive(['LastUpdatedAfter'], ['BuyerEmail'], ['SellerOrderId'])
    @dependent('LastUpdatedBefore', ['LastUpdatedAfter'])
    @exclusive(['CreatedAfter'], ['LastUpdatedBefore'])
    @requires(['MarketplaceId'])
    @structured_objects('OrderTotal', 'ShippingAddress',
                        'PaymentExecutionDetail')
    @structured_lists('MarketplaceId.Id', 'OrderStatus.Status',
                      'FulfillmentChannel.Channel', 'PaymentMethod.')
    @api_action('Orders', 6, 60)
    def list_orders(self, path, response, **kw):
        """Returns a list of orders created or updated during a time
           frame that you specify.
        """
        toggle = set(('FulfillmentChannel.Channel.1',
                      'OrderStatus.Status.1', 'PaymentMethod.1',
                      'LastUpdatedAfter', 'LastUpdatedBefore'))
        for do, dont in {
            'BuyerEmail': toggle.union(['SellerOrderId']),
            'SellerOrderId': toggle.union(['BuyerEmail']),
        }.items():
            if do in kw and filter(kw.has_key, dont):
                message = "Don't include {0} when specifying " \
                          "{1}".format(' or '.join(dont), do)
                raise AssertionError(message)
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Orders', 6, 60)
    def list_orders_by_next_token(self, path, response, **kw):
        """Returns the next page of orders using the NextToken value
           that was returned by your previous request to either
           ListOrders or ListOrdersByNextToken.
        """
        return self.post_request(path, kw, response)

    @requires(['AmazonOrderId'])
    @structured_lists('AmazonOrderId.Id')
    @api_action('Orders', 6, 60)
    def get_order(self, path, response, **kw):
        """Returns an order for each AmazonOrderId that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['AmazonOrderId'])
    @api_action('Orders', 30, 2)
    def list_order_items(self, path, response, **kw):
        """Returns order item information for an AmazonOrderId that
           you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Orders', 30, 2)
    def list_order_items_by_next_token(self, path, response, **kw):
        """Returns the next page of order items using the NextToken
           value that was returned by your previous request to either
           ListOrderItems or ListOrderItemsByNextToken.
        """
        return self.post_request(path, kw, response)

    @api_action('Orders', 2, 300, 'GetServiceStatus')
    def get_orders_service_status(self, path, response, **kw):
        """Returns the operational status of the Orders API section.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'Query'])
    @api_action('Products', 20, 20)
    def list_matching_products(self, path, response, **kw):
        """Returns a list of products and their attributes, ordered
           by relevancy, based on a search query that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 20)
    def get_matching_product(self, path, response, **kw):
        """Returns a list of products and their attributes, based on
           a list of ASIN values that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'IdType', 'IdList'])
    @structured_lists('IdList.Id')
    @api_action('Products', 20, 20)
    def get_matching_product_for_id(self, path, response, **kw):
        """Returns a list of products and their attributes, based on
           a list of Product IDs that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'SellerSKUList'])
    @structured_lists('SellerSKUList.SellerSKU')
    @api_action('Products', 20, 10, 'GetCompetitivePricingForSKU')
    def get_competitive_pricing_for_sku(self, path, response, **kw):
        """Returns the current competitive pricing of a product,
           based on the SellerSKUs and MarketplaceId that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 10, 'GetCompetitivePricingForASIN')
    def get_competitive_pricing_for_asin(self, path, response, **kw):
        """Returns the current competitive pricing of a product,
           based on the ASINs and MarketplaceId that you specify.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'SellerSKUList'])
    @structured_lists('SellerSKUList.SellerSKU')
    @api_action('Products', 20, 5, 'GetLowestOfferListingsForSKU')
    def get_lowest_offer_listings_for_sku(self, path, response, **kw):
        """Returns the lowest price offer listings for a specific
           product by item condition and SellerSKUs.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 5, 'GetLowestOfferListingsForASIN')
    def get_lowest_offer_listings_for_asin(self, path, response, **kw):
        """Returns the lowest price offer listings for a specific
           product by item condition and ASINs.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'SellerSKU'])
    @api_action('Products', 20, 20, 'GetProductCategoriesForSKU')
    def get_product_categories_for_sku(self, path, response, **kw):
        """Returns the product categories that a SellerSKU belongs to.
        """
        return self.post_request(path, kw, response)

    @requires(['MarketplaceId', 'ASIN'])
    @api_action('Products', 20, 20, 'GetProductCategoriesForASIN')
    def get_product_categories_for_asin(self, path, response, **kw):
        """Returns the product categories that an ASIN belongs to.
        """
        return self.post_request(path, kw, response)

    @api_action('Products', 2, 300, 'GetServiceStatus')
    def get_products_service_status(self, path, response, **kw):
        """Returns the operational status of the Products API section.
        """
        return self.post_request(path, kw, response)

    @api_action('Sellers', 15, 60)
    def list_marketplace_participations(self, path, response, **kw):
        """Returns a list of marketplaces that the seller submitting
           the request can sell in, and a list of participations that
           include seller-specific information in that marketplace.
        """
        return self.post_request(path, kw, response)

    @requires(['NextToken'])
    @api_action('Sellers', 15, 60)
    def list_marketplace_participations_by_next_token(self, path, response,
                                                      **kw):
        """Returns the next page of marketplaces and participations
           using the NextToken value that was returned by your
           previous request to either ListMarketplaceParticipations
           or ListMarketplaceParticipationsByNextToken.
        """
        return self.post_request(path, kw, response)
