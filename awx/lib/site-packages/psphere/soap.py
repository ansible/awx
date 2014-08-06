"""
A leaky wrapper for the underlying suds library.
"""

# Copyright 2010 Jonathan Kinred
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at:
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import logging
import urllib2
import suds

from pprint import pprint

logger = logging.getLogger(__name__)

class VimFault(Exception):
    def __init__(self, fault):
        self.fault = fault
        self.fault_type = fault.__class__.__name__
        self._fault_dict = {}
        for attr in fault:
            self._fault_dict[attr[0]] = attr[1]

        Exception.__init__(self, "%s: %s" % (self.fault_type, self._fault_dict))


def get_client(url):
    client = suds.client.Client(url + "/vimService.wsdl")
    client.set_options(location=url)
    return client


def create(client, _type, **kwargs):
    """Create a suds object of the requested _type."""
    obj = client.factory.create("ns0:%s" % _type)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    return obj


def invoke(client, method, **kwargs):
    """Invoke a method on the underlying soap service."""
    try:
        # Proxy the method to the suds service
        result = getattr(client.service, method)(**kwargs)
    except AttributeError, e:
        logger.critical("Unknown method: %s", method)
        raise
    except urllib2.URLError, e:
        logger.debug(pprint(e))
        logger.debug("A URL related error occurred while invoking the '%s' "
              "method on the VIM server, this can be caused by "
              "name resolution or connection problems.", method)
        logger.debug("The underlying error is: %s", e.reason[1])
        raise
    except suds.client.TransportError, e:
        logger.debug(pprint(e))
        logger.debug("TransportError: %s", e)
    except suds.WebFault, e:
        # Get the type of fault
        logger.critical("SUDS Fault: %s" % e.fault.faultstring)
        if len(e.fault.faultstring) > 0:
            raise

        detail = e.document.childAtPath("/Envelope/Body/Fault/detail")
        fault_type = detail.getChildren()[0].name
        fault = create(fault_type)
        if isinstance(e.fault.detail[0], list):
            for attr in e.fault.detail[0]:
                setattr(fault, attr[0], attr[1])
        else:
            fault["text"] = e.fault.detail[0]

        raise VimFault(fault)

    return result


class ManagedObjectReference(suds.sudsobject.Property):
    """Custom class to replace the suds generated class, which lacks _type."""
    def __init__(self, _type, value):
        suds.sudsobject.Property.__init__(self, value)
        self._type = _type
