# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Abiquo Utilities Module for the Abiquo Driver.

Common utilities needed by the :class:`AbiquoNodeDriver`.
"""
import base64

from libcloud.common.base import ConnectionUserAndKey, PollingConnection
from libcloud.common.base import XmlResponse
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import b
from libcloud.compute.base import NodeState


def get_href(element, rel):
    """
    Search a RESTLink element in the :class:`AbiquoResponse`.

    Abiquo, as a REST API, it offers self-discovering functionality.
    That means that you could walk through the whole API only
    navigating from the links offered by the entities.

    This is a basic method to find the 'relations' of an entity searching into
    its links.

    For instance, a Rack entity serialized as XML as the following::

        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <rack>
         <link href="http://host/api/admin/datacenters/1"
            type="application/vnd.abiquo.datacenter+xml" rel="datacenter"/>
         <link href="http://host/api/admin/datacenters/1/racks/1"
            type="application/vnd.abiquo.rack+xml" rel="edit"/>
         <link href="http://host/api/admin/datacenters/1/racks/1/machines"
            type="application/vnd.abiquo.machines+xml" rel="machines"/>
         <haEnabled>false</haEnabled>
         <id>1</id>
         <longDescription></longDescription>
         <name>racacaca</name>
         <nrsq>10</nrsq>
         <shortDescription></shortDescription>
         <vlanIdMax>4094</vlanIdMax>
         <vlanIdMin>2</vlanIdMin>
         <vlanPerVdcReserved>1</vlanPerVdcReserved>
         <vlansIdAvoided></vlansIdAvoided>
        </rack>

    offers link to datacenters (rel='datacenter'), to itself (rel='edit') and
    to the machines defined in it (rel='machines')

    A call to this method with the 'rack' element using 'datacenter' as 'rel'
    will return:

    'http://10.60.12.7:80/api/admin/datacenters/1'

    :type  element: :class:`xml.etree.ElementTree`
    :param element: Xml Entity returned by Abiquo API (required)
    :type      rel: ``str``
    :param     rel: relation link name
    :rtype:         ``str``
    :return:        the 'href' value according to the 'rel' input parameter
    """
    links = element.findall('link')
    for link in links:
        if link.attrib['rel'] == rel:
            href = link.attrib['href']
            # href is something like:
            #
            # 'http://localhost:80/api/admin/enterprises'
            #
            # we are only interested in '/admin/enterprises/' part
            needle = '/api/'
            url_path = urlparse.urlparse(href).path
            index = url_path.find(needle)
            result = url_path[index + len(needle) - 1:]
            return result


class AbiquoResponse(XmlResponse):
    """
    Abiquo XML Response.

    Wraps the response in XML bodies or extract the error data in
    case of error.
    """

    # Map between abiquo state and Libcloud State
    NODE_STATE_MAP = {
        'NOT_ALLOCATED': NodeState.TERMINATED,
        'ALLOCATED': NodeState.PENDING,
        'CONFIGURED': NodeState.PENDING,
        'ON': NodeState.RUNNING,
        'PAUSED': NodeState.PENDING,
        'OFF': NodeState.PENDING,
        'LOCKED': NodeState.PENDING,
        'UNKNOWN': NodeState.UNKNOWN
    }

    def parse_error(self):
        """
        Parse the error messages.

        Response body can easily be handled by this class parent
        :class:`XmlResponse`, but there are use cases which Abiquo API
        does not respond an XML but an HTML. So we need to
        handle these special cases.
        """
        if self.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError(driver=self.connection.driver)
        elif self.status == httplib.FORBIDDEN:
            raise ForbiddenError(self.connection.driver)
        else:
            errors = self.parse_body().findall('error')
            # Most of the exceptions only have one error
            raise LibcloudError(errors[0].findtext('message'))

    def success(self):
        """
        Determine if the request was successful.

        Any of the 2XX HTTP response codes are accepted as successfull requests

        :rtype:  ``bool``
        :return: successful request or not.
        """
        return self.status in [httplib.OK, httplib.CREATED, httplib.NO_CONTENT,
                               httplib.ACCEPTED]

    def async_success(self):
        """
        Determinate if async request was successful.

        An async_request retrieves for a task object that can be successfully
        retrieved (self.status == OK), but the asyncronous task (the body of
        the HTTP response) which we are asking for has finished with an error.
        So this method checks if the status code is 'OK' and if the task
        has finished successfully.

        :rtype:  ``bool``
        :return: successful asynchronous request or not
        """
        if self.success():
            # So we have a 'task' object in the body
            task = self.parse_body()
            return task.findtext('state') == 'FINISHED_SUCCESSFULLY'
        else:
            return False


class AbiquoConnection(ConnectionUserAndKey, PollingConnection):
    """
    A Connection to Abiquo API.

    Basic :class:`ConnectionUserAndKey` connection with
    :class:`PollingConnection` features for asynchronous tasks.
    """

    responseCls = AbiquoResponse

    def __init__(self, user_id, key, secure=True, host=None, port=None,
                 url=None, timeout=None):
        super(AbiquoConnection, self).__init__(user_id=user_id, key=key,
                                               secure=secure,
                                               host=host, port=port,
                                               url=url, timeout=timeout)

        # This attribute stores data cached across multiple request
        self.cache = {}

    def add_default_headers(self, headers):
        """
        Add Basic Authentication header to all the requests.

        It injects the 'Authorization: Basic Base64String===' header
        in each request

        :type  headers: ``dict``
        :param headers: Default input headers
        :rtype          ``dict``
        :return:        Default input headers with the 'Authorization'
                        header
        """
        b64string = b('%s:%s' % (self.user_id, self.key))
        encoded = base64.b64encode(b64string).decode('utf-8')

        authorization = 'Basic ' + encoded

        headers['Authorization'] = authorization
        return headers

    def get_poll_request_kwargs(self, response, context, request_kwargs):
        """
        Manage polling request arguments.

        Return keyword arguments which are passed to the
        :class:`NodeDriver.request` method when polling for the job status. The
        Abiquo Asynchronous Response returns and 'acceptedrequest' XmlElement
        as the following::

            <acceptedrequest>
                <link href="http://uri/to/task" rel="status"/>
                <message>You can follow the progress in the link</message>
            </acceptedrequest>

        We need to extract the href URI to poll.

        :type    response:       :class:`xml.etree.ElementTree`
        :keyword response:       Object returned by poll request.
        :type    request_kwargs: ``dict``
        :keyword request_kwargs: Default request arguments and headers
        :rtype:                  ``dict``
        :return:                 Modified keyword arguments
        """
        accepted_request_obj = response.object
        link_poll = get_href(accepted_request_obj, 'status')

        # Override just the 'action' and 'method' keys of the previous dict
        request_kwargs['action'] = link_poll
        request_kwargs['method'] = 'GET'
        return request_kwargs

    def has_completed(self, response):
        """
        Decide if the asynchronous job has ended.

        :type  response: :class:`xml.etree.ElementTree`
        :param response: Response object returned by poll request
        :rtype:          ``bool``
        :return:         Whether the job has completed
        """
        task = response.object
        task_state = task.findtext('state')
        return task_state in ['FINISHED_SUCCESSFULLY', 'ABORTED',
                              'FINISHED_UNSUCCESSFULLY']


class ForbiddenError(LibcloudError):
    """
    Exception used when credentials are ok but user has not permissions.
    """

    def __init__(self, driver):
        message = 'User has not permission to perform this task.'
        super(LibcloudError, self).__init__(message, driver)
