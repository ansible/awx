#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from functools import wraps
import json
import re
import time

import pyrax
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils

# How long (in seconds) to wait for a response from async operations
DEFAULT_TIMEOUT = 5
# How long (in seconds) to wait in between checks for async completion
DEFAULT_DELAY = 0.5


def assure_domain(fnc):
    @wraps(fnc)
    def _wrapped(self, domain, *args, **kwargs):
        if not isinstance(domain, CloudDNSDomain):
            # Must be the ID
            domain = self._manager.get(domain)
        return fnc(self, domain, *args, **kwargs)
    return _wrapped



class CloudDNSRecord(BaseResource):
    """
    This class represents a domain record.
    """
    GET_DETAILS = False
    # Initialize the supported attributes.
    type = None
    name = None
    data = None
    priority = None
    ttl = None
    comment = None


    def update(self, data=None, priority=None, ttl=None, comment=None):
        """
        Modifies this record.
        """
        return self.manager.update_record(self.domain_id, self, data=data,
                priority=priority, ttl=ttl, comment=comment)


    def get(self):
        """
        Gets the full information for an existing record for this domain.
        """
        return self.manager.get_record(self.domain_id, self)


    def delete(self):
        """
        Deletes an existing record for this domain.
        """
        return self.manager.delete_record(self.domain_id, self)



class CloudDNSDomain(BaseResource):
    """
    This class represents a DNS domain.
    """
    def delete(self, delete_subdomains=False):
        """
        Deletes this domain and all of its resource records. If this domain has
        subdomains, each subdomain will now become a root domain. If you wish to
        also delete any subdomains, pass True to 'delete_subdomains'.
        """
        self.manager.delete(self, delete_subdomains=delete_subdomains)


    def changes_since(self, date_or_datetime):
        """
        Gets the changes for this domain since the specified date/datetime.
        The date can be one of:
            - a Python datetime object
            - a Python date object
            - a string in the format 'YYYY-MM-YY HH:MM:SS'
            - a string in the format 'YYYY-MM-YY'

        It returns a list of dicts, whose keys depend on the specific change
        that was made. A simple example of such a change dict:

            {u'accountId': 000000,
             u'action': u'update',
             u'changeDetails': [{u'field': u'serial_number',
               u'newValue': u'1354038941',
               u'originalValue': u'1354038940'},
              {u'field': u'updated_at',
               u'newValue': u'Tue Nov 27 17:55:41 UTC 2012',
               u'originalValue': u'Tue Nov 27 17:55:40 UTC 2012'}],
             u'domain': u'example.com',
             u'targetId': 00000000,
             u'targetType': u'Domain'}
        """
        return self.manager.changes_since(self, date_or_datetime)


    def export(self):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as such,
        does not provide subdomain information.

        Sample export:
            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. '
                'foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        return self.manager.export_domain(self)


    def update(self, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        entry:
            - email address
            - ttl setting
            - comment
        """
        return self.manager.update_domain(self, emailAddress=emailAddress,
                ttl=ttl, comment=comment)


    def list_subdomains(self, limit=None, offset=None):
        """
        Returns a list of all subdomains for this domain.
        """
        return self.manager.list_subdomains(self, limit=limit, offset=offset)


    def list_records(self, limit=None, offset=None):
        """
        Returns a list of all records configured for this domain.
        """
        return self.manager.list_records(self, limit=limit, offset=offset)


    def search_records(self, record_type, name=None, data=None):
        """
        Returns a list of all records configured for this domain that match
        the supplied search criteria.
        """
        return self.manager.search_records(self, record_type=record_type,
                name=name, data=data)


    def find_record(self, record_type, name=None, data=None):
        """
        Returns a single record for this domain that matches the supplied
        search criteria.

        If no record matches, a DomainRecordNotFound exception will be raised.
        If more than one matches, a DomainRecordNotUnique exception will
        be raised.
        """
        matches = self.manager.search_records(self, record_type=record_type,
                name=name, data=data)
        if not matches:
            raise exc.DomainRecordNotFound
        elif len(matches) > 1:
            raise exc.DomainRecordNotUnique
        return matches[0]


    def add_records(self, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            - type (required)
            - name (required)
            - data (required)
            - ttl (optional)
            - comment (optional)
            - priority (required for MX and SRV records; forbidden otherwise)
        """
        return self.manager.add_records(self, records)

    # Create an alias, so that adding a single record is more intuitive
    add_record = add_records


    def get_record(self, record):
        """
        Gets the full information for an existing record for this domain.
        """
        return self.manager.get_record(self, record)


    def update_record(self, record, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifies an existing record for this domain.
        """
        return self.manager.update_record(self, record, data=data,
                priority=priority, ttl=ttl, comment=comment)


    def delete_record(self, record):
        """
        Deletes an existing record for this domain.
        """
        return self.manager.delete_record(self, record)


class CloudDNSPTRRecord(object):
    """
    This represents a Cloud DNS PTR record (reverse DNS).
    """
    def __init__(self, data=None, device=None):
        self.type = self.id = self.data = self.name = None
        self.ttl = self.comment = None
        if data:
            for key, val in data.items():
                setattr(self, key, val)
        self.device = device


    def delete(self):
        """
        Deletes this PTR record from its device.
        """
        return pyrax.cloud_dns.delete_ptr_records(self.device, self.data)


    def __repr__(self):
        reprkeys = ("id", "data", "name", "ttl")
        info = ", ".join("%s=%s" % (key, getattr(self, key)) for key in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)



class CloudDNSManager(BaseManager):
    def __init__(self, api, resource_class=None, response_key=None,
            plural_response_key=None, uri_base=None):
        super(CloudDNSManager, self).__init__(api, resource_class=resource_class,
                response_key=response_key, plural_response_key=plural_response_key,
                uri_base=uri_base)
        self._paging = {"domain": {}, "subdomain": {}, "record": {}}
        self._reset_paging(service="all")
        self._timeout = DEFAULT_TIMEOUT
        self._delay = DEFAULT_DELAY


    def _set_timeout(self, timeout):
        """
        Changes the duration for which the program will wait for a response from
        the DNS system. Setting the timeout to zero will make that program wait
        an indefinite amount of time.
        """
        self._timeout = timeout


    def _set_delay(self, delay):
        """
        Changes the interval that the program will pause in between attempts to
        see if a request has completed.
        """
        self._delay = delay


    def _reset_paging(self, service, body=None):
        """
        Resets the internal attributes when there is no current paging request.
        """
        if service == "all":
            for svc in self._paging.keys():
                svc_dct = self._paging[svc]
                svc_dct["next_uri"] = svc_dct["prev_uri"] = None
                svc_dct["total_entries"] = None
            return
        svc_dct = self._paging[service]
        svc_dct["next_uri"] = svc_dct["prev_uri"] = None
        svc_dct["total_entries"] = None
        if not body:
            return
        svc_dct["total_entries"] = body.get("totalEntries")
        links = body.get("links")
        uri_base = self.uri_base
        if links:
            for link in links:
                href = link["href"]
                pos = href.index(uri_base)
                page_uri = href[pos - 1:]
                if link["rel"] == "next":
                    svc_dct["next_uri"] = page_uri
                elif link["rel"] == "previous":
                    svc_dct["prev_uri"] = page_uri


    def _get_pagination_qs(self, limit, offset):
        pagination_items = []
        if limit is not None:
            pagination_items.append("limit=%s" % limit)
        if offset is not None:
            pagination_items.append("offset=%s" % offset)
        qs = "&".join(pagination_items)
        qs = "?%s" % qs if qs else ""
        return qs


    def list(self, limit=None, offset=None):
        """Gets a list of all domains, or optionally a page of domains."""
        uri = "/%s%s" % (self.uri_base, self._get_pagination_qs(limit, offset))
        return self._list(uri)


    def _list(self, uri, obj_class=None, list_all=False):
        """
        Handles the communication with the API when getting
        a full listing of the resources managed by this class.
        """
        resp, resp_body = self.api.method_get(uri)
        if obj_class is None:
            obj_class = self.resource_class

        data = resp_body[self.plural_response_key]
        ret = [obj_class(self, res, loaded=False)
                for res in data if res]
        self._reset_paging("domain", resp_body)
        if list_all:
            dom_paging = self._paging.get("domain", {})
            while dom_paging.get("next_uri"):
                next_uri = dom_paging.get("next_uri")
                ret.extend(self._list(uri=next_uri, obj_class=obj_class,
                        list_all=False))
        return ret


    def list_previous_page(self):
        """
        When paging through results, this will return the previous page, using
        the same limit. If there are no more results, a NoMoreResults exception
        will be raised.
        """
        uri = self._paging.get("domain", {}).get("prev_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no previous pages of domains "
                    "to list.")
        return self._list(uri)


    def list_next_page(self):
        """
        When paging through results, this will return the next page, using the
        same limit. If there are no more results, a NoMoreResults exception
        will be raised.
        """
        uri = self._paging.get("domain", {}).get("next_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no more pages of domains to "
                    "list.")
        return self._list(uri)


    def _get(self, uri):
        """
        Handles the communication with the API when getting
        a specific resource managed by this class.

        Because DNS returns a different format for the body,
        the BaseManager method must be overridden here.
        """
        uri = "%s?showRecords=false&showSubdomains=false" % uri
        resp, body = self.api.method_get(uri)
        body["records"] = []
        return self.resource_class(self, body, loaded=True)


    def _async_call(self, uri, body=None, method="GET", error_class=None,
            has_response=True, *args, **kwargs):
        """
        Handles asynchronous call/responses for the DNS API.

        Returns the response headers and body if the call was successful.
        If an error status is returned, and the 'error_class' parameter is
        specified, that class of error will be raised with the details from
        the response. If no error class is specified, the response headers
        and body will be returned to the calling method, which will have
        to handle the result.
        """
        api_methods = {
                "GET": self.api.method_get,
                "POST": self.api.method_post,
                "PUT": self.api.method_put,
                "DELETE": self.api.method_delete,
                }
        api_method = api_methods[method]
        if body is None:
            resp, resp_body = api_method(uri, *args, **kwargs)
        else:
            resp, resp_body = api_method(uri, body=body, *args, **kwargs)
        callbackURL = resp_body["callbackUrl"].split("/status/")[-1]
        massagedURL = "/status/%s?showDetails=true" % callbackURL
        start = time.time()
        timed_out = False
        while (resp_body["status"] == "RUNNING") and not timed_out:
            resp, resp_body = self.api.method_get(massagedURL)
            if self._timeout:
                timed_out = ((time.time() - start) > self._timeout)
                time.sleep(self._delay)
        if error_class and (resp_body["status"] == "ERROR"):
            # This call will handle raising the error.
            self._process_async_error(resp_body, error_class)
        if timed_out:
            raise exc.DNSCallTimedOut("The API call to '%s' did not complete "
                    "after %s seconds." % (uri, self._timeout))
        if has_response:
            ret = resp, resp_body["response"]
        else:
            ret = resp, resp_body
        try:
            resp_body = json.loads(resp_body)
        except Exception:
            pass
        return ret


    def _process_async_error(self, resp_body, error_class):
        """
        The DNS API does not return a consistent format for their error
        messages. This abstracts out the differences in order to present
        a single unified message in the exception to be raised.
        """
        def _fmt_error(err):
            # Remove the cumbersome Java-esque message
            details = err["details"].replace("\n", " ")
            if not details:
                details = err["message"]
            return "%s (%s)" % (details, err["code"])

        error = resp_body["error"]
        if "failedItems" in error:
            # Multi-error response
            faults = error["failedItems"]["faults"]
            msgs = [_fmt_error(fault) for fault in faults]
            msg = "\n".join(msgs)
        else:
            msg = _fmt_error(error)
        raise error_class(msg)


    def _create(self, uri, body, records=None, subdomains=None,
            return_none=False, return_raw=False, **kwargs):
        """
        Handles the communication with the API when creating a new
        resource managed by this class.

        Since DNS works completely differently for create() than the other
        APIs, this method overrides the default BaseManager behavior.

        If 'records' are supplied, they should be a list of dicts. Each
        record dict should have the following format:

            {"name": "example.com",
            "type": "A",
            "data": "192.0.2.17",
            "ttl": 86400}

        If 'subdomains' are supplied, they should be a list of dicts. Each
        subdomain dict should have the following format:

            {"name": "sub1.example.com",
             "comment": "1st sample subdomain",
             "emailAddress": "sample@rackspace.com"}
        """
        self.run_hooks("modify_body_for_create", body, **kwargs)
        resp, resp_body = self._async_call(uri, body=body, method="POST",
                error_class=exc.DomainCreationFailed)
        response_body = resp_body[self.response_key][0]
        return self.resource_class(self, response_body)


    def delete(self, domain, delete_subdomains=False):
        """
        Deletes the specified domain and all of its resource records. If the
        domain has subdomains, each subdomain will now become a root domain. If
        you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        uri = "/%s/%s" % (self.uri_base, utils.get_id(domain))
        if delete_subdomains:
            uri = "%s?deleteSubdomains=true" % uri
        resp, resp_body = self._async_call(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)


    def findall(self, **kwargs):
        """
        Finds all items with attributes matching ``**kwargs``.

        Normally this isn't very efficient, since the default action is to
        load the entire list and then filter on the Python side, but the DNS
        API provides a more efficient search option when filtering on name.
        So if the filter is on name, use that; otherwise, use the default.
        """
        if (len(kwargs) == 1) and ("name" in kwargs):
            # Filtering on name; use the more efficient method.
            nm = kwargs["name"]
            uri = "/%s?name=%s" % (self.uri_base, nm)
            matches = self._list(uri, list_all=True)
            return [match for match in matches
                if match.name == nm]
        else:
            return super(CloudDNSManager, self).findall(**kwargs)


    def changes_since(self, domain, date_or_datetime):
        """
        Gets the changes for a domain since the specified date/datetime.
        The date can be one of:
            - a Python datetime object
            - a Python date object
            - a string in the format 'YYYY-MM-YY HH:MM:SS'
            - a string in the format 'YYYY-MM-YY'

        It returns a list of dicts, whose keys depend on the specific change
        that was made. A simple example of such a change dict:

            {u'accountId': 000000,
             u'action': u'update',
             u'changeDetails': [{u'field': u'serial_number',
               u'newValue': u'1354038941',
               u'originalValue': u'1354038940'},
              {u'field': u'updated_at',
               u'newValue': u'Tue Nov 27 17:55:41 UTC 2012',
               u'originalValue': u'Tue Nov 27 17:55:40 UTC 2012'}],
             u'domain': u'example.com',
             u'targetId': 00000000,
             u'targetType': u'Domain'}
        """
        domain_id = utils.get_id(domain)
        dt = utils.iso_time_string(date_or_datetime, show_tzinfo=True)
        uri = "/domains/%s/changes?since=%s" % (domain_id, dt)
        resp, body = self.api.method_get(uri)
        return body.get("changes", [])


    def export_domain(self, domain):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as
        such, does not provide subdomain information.

        Sample export:
            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. '
                'foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        uri = "/domains/%s/export" % utils.get_id(domain)
        resp, resp_body = self._async_call(uri, method="GET",
                error_class=exc.NotFound)
        return resp_body.get("contents", "")


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        uri = "/domains/import"
        body = {"domains": [{
                "contentType": "BIND_9",
                "contents": domain_data,
                }]}
        resp, resp_body = self._async_call(uri, method="POST", body=body,
                error_class=exc.DomainCreationFailed)
        return resp_body


    def update_domain(self, domain, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        if not any((emailAddress, ttl, comment)):
            raise exc.MissingDNSSettings(
                    "No settings provided to update_domain().")
        uri = "/domains/%s" % utils.get_id(domain)
        body = {"comment": comment,
                "ttl": ttl,
                "emailAddress": emailAddress,
                }
        none_keys = [key for key, val in body.items()
                if val is None]
        for none_key in none_keys:
            body.pop(none_key)
        resp, resp_body = self._async_call(uri, method="PUT", body=body,
                error_class=exc.DomainUpdateFailed, has_response=False)
        return resp_body


    def list_subdomains(self, domain, limit=None, offset=None):
        """
        Returns a list of all subdomains of the specified domain.
        """
        # The commented-out uri is the official API, but it is
        # horribly slow.
#        uri = "/domains/%s/subdomains" % utils.get_id(domain)
        uri = "/domains?name=%s" % domain.name
        page_qs = self._get_pagination_qs(limit, offset)
        if page_qs:
            uri = "%s&%s" % (uri, page_qs[1:])
        return self._list_subdomains(uri, domain.id)


    def _list_subdomains(self, uri, domain_id):
        resp, body = self.api.method_get(uri)
        self._reset_paging("subdomain", body)
        subdomains = body.get("domains", [])
        return [CloudDNSDomain(self, subdomain, loaded=False)
                for subdomain in subdomains
                if subdomain["id"] != domain_id]


    def list_subdomains_previous_page(self):
        """
        When paging through subdomain results, this will return the previous
        page, using the same limit. If there are no more results, a
        NoMoreResults exception will be raised.
        """
        uri = self._paging.get("subdomain", {}).get("prev_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no previous pages of subdomains "
                    "to list.")
        return self._list_subdomains(uri)


    def list_subdomains_next_page(self):
        """
        When paging through subdomain results, this will return the next page,
        using the same limit. If there are no more results, a NoMoreResults
        exception will be raised.
        """
        uri = self._paging.get("subdomain", {}).get("next_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no more pages of subdomains "
                    "to list.")
        return self._list_subdomains(uri)


    def list_records(self, domain, limit=None, offset=None):
        """
        Returns a list of all records configured for the specified domain.
        """
        uri = "/domains/%s/records%s" % (utils.get_id(domain),
                self._get_pagination_qs(limit, offset))
        return self._list_records(uri)


    def _list_records(self, uri):
        resp, body = self.api.method_get(uri)
        self._reset_paging("record", body)
        # The domain ID will be in the URL
        pat = "domains/([^/]+)/records"
        mtch = re.search(pat, uri)
        dom_id = mtch.groups()[0]
        records = body.get("records", [])
        for record in records:
            record["domain_id"] = dom_id
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def list_records_previous_page(self):
        """
        When paging through record results, this will return the previous page,
        using the same limit. If there are no more results, a NoMoreResults
        exception will be raised.
        """
        uri = self._paging.get("record", {}).get("prev_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no previous pages of records "
                    "to list.")
        return self._list_records(uri)


    def list_records_next_page(self):
        """
        When paging through record results, this will return the next page,
        using the same limit. If there are no more results, a NoMoreResults
        exception will be raised.
        """
        uri = self._paging.get("record", {}).get("next_uri")
        if uri is None:
            raise exc.NoMoreResults("There are no more pages of records to list.")
        return self._list_records(uri)


    def search_records(self, domain, record_type, name=None, data=None):
        """
        Returns a list of all records configured for the specified domain that
        match the supplied search criteria.
        """
        search_params = []
        if name:
            search_params.append("name=%s" % name)
        if data:
            search_params.append("data=%s" % data)
        query_string = "&".join(search_params)
        dom_id = utils.get_id(domain)
        uri = "/domains/%s/records?type=%s" % (dom_id, record_type)
        if query_string:
            uri = "%s&%s" % (uri, query_string)
        resp, body = self.api.method_get(uri)
        records = body.get("records", [])
        self._reset_paging("record", body)
        rec_paging = self._paging.get("record", {})
        while rec_paging.get("next_uri"):
            resp, body = self.api.method_get(rec_paging.get("next_uri"))
            self._reset_paging("record", body)
            records.extend(body.get("records", []))
        for record in records:
            record["domain_id"] = dom_id
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def add_records(self, domain, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            - type (required)
            - name (required)
            - data (required)
            - ttl (optional)
            - comment (optional)
            - priority (required for MX and SRV records; forbidden otherwise)
        """
        if isinstance(records, dict):
            # Single record passed
            records = [records]
        dom_id = utils.get_id(domain)
        uri = "/domains/%s/records" % dom_id
        body = {"records": records}
        resp, resp_body = self._async_call(uri, method="POST", body=body,
                error_class=exc.DomainRecordAdditionFailed, has_response=False)
        records = resp_body.get("response", {}).get("records", [])
        for record in records:
            record["domain_id"] = dom_id
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def get_record(self, domain, record):
        """
        Gets the full information for an existing record for this domain.
        """
        rec_id = utils.get_id(record)
        domain_id = utils.get_id(domain)
        uri = "/domains/%s/records/%s" % (domain_id, rec_id)
        resp, resp_body = self.api.method_get(uri)
        resp_body['domain_id'] = domain_id
        return CloudDNSRecord(self, resp_body, loaded=False)


    def update_record(self, domain, record, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifies an existing record for a domain.
        """
        rec_id = utils.get_id(record)
        uri = "/domains/%s/records/%s" % (utils.get_id(domain), rec_id)
        body = {"name": record.name}
        all_opts = (("data", data), ("priority", priority), ("ttl", ttl),
                ("comment", comment))
        opts = [(k, v) for k, v in all_opts if v is not None]
        body.update(dict(opts))
        resp, resp_body = self._async_call(uri, method="PUT", body=body,
                error_class=exc.DomainRecordUpdateFailed, has_response=False)
        return resp_body


    def delete_record(self, domain, record):
        """
        Deletes an existing record for a domain.
        """
        uri = "/domains/%s/records/%s" % (utils.get_id(domain),
                utils.get_id(record))
        resp, resp_body = self._async_call(uri, method="DELETE",
                error_class=exc.DomainRecordDeletionFailed, has_response=False)
        return resp_body


    def _get_ptr_details(self, device, device_type):
        """
        Takes a device and device type and returns the corresponding HREF link
        and service name for use with PTR record management.
        """
        if device_type.lower().startswith("load"):
            ep = pyrax._get_service_endpoint("load_balancer")
            svc = "loadbalancers"
            svc_name = "cloudLoadBalancers"
        else:
            ep = pyrax._get_service_endpoint("compute")
            svc = "servers"
            svc_name = "cloudServersOpenStack"
        href = "%s/%s/%s" % (ep, svc, utils.get_id(device))
        return (href, svc_name)


    def _resolve_device_type(self, device):
        """
        Given a device, determines if it is a CloudServer, a CloudLoadBalancer,
        or an invalid device.
        """
        try:
            from tests.unit import fakes
            server_types = (pyrax.CloudServer, fakes.FakeServer,
                fakes.FakeDNSDevice)
            lb_types = (pyrax.CloudLoadBalancer, fakes.FakeLoadBalancer)
        except ImportError:
            # Not running with tests
            server_types = (pyrax.CloudServer, )
            lb_types = (pyrax.CloudLoadBalancer, )
        if isinstance(device, server_types):
            device_type = "server"
        elif isinstance(device, lb_types):
            device_type = "loadbalancer"
        else:
            raise exc.InvalidDeviceType("The device '%s' must be a CloudServer "
                    "or a CloudLoadBalancer." % device)
        return device_type


    def list_ptr_records(self, device):
        """
        Returns a list of all PTR records configured for this device.
        """
        device_type = self._resolve_device_type(device)
        href, svc_name = self._get_ptr_details(device, device_type)
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        try:
            resp, resp_body = self.api.method_get(uri)
        except exc.NotFound:
            return []
        records = [CloudDNSPTRRecord(rec, device)
                for rec in resp_body.get("records", [])]
        return records


    def add_ptr_records(self, device, records):
        """
        Adds one or more PTR records to the specified device.
        """
        device_type = self._resolve_device_type(device)
        href, svc_name = self._get_ptr_details(device, device_type)
        if not isinstance(records, (list, tuple)):
            records = [records]
        body = {"recordsList": {
                    "records": records},
                "link": {
                    "content": "",
                    "href": href,
                    "rel": svc_name,
                }}
        uri = "/rdns"
        # This is a necessary hack, so here's why: if you attempt to add
        # PTR records to device, and you don't have rights to either the device
        # or the IP address, the DNS API will return a 401 - Unauthorized.
        # Unfortunately, the pyrax client interprets this as a bad auth token,
        # and there is no way to distinguish this from an actual authentication
        # failure. The client will attempt to re-authenticate as a result, and
        # will fail, due to the DNS API not having regional endpoints. The net
        # result is that an EndpointNotFound exception will be raised, which
        # we catch here and then raise a more meaningful exception.
        # The Rackspace DNS team is working on changing this to return a 403
        # instead; when that happens this kludge can go away.
        try:
            resp, resp_body = self._async_call(uri, body=body, method="POST",
                    error_class=exc.PTRRecordCreationFailed)
        except exc.EndpointNotFound:
            raise exc.InvalidPTRRecord("The domain/IP address information is not "
                    "valid for this device.")
        return resp_body.get("records")
        records = [CloudDNSPTRRecord(rec, device)
                for rec in resp_body.get("records", [])]
        return records


    def update_ptr_record(self, device, record, domain_name, data=None,
            ttl=None, comment=None):
        """
        Updates a PTR record with the supplied values.
        """
        device_type = self._resolve_device_type(device)
        href, svc_name = self._get_ptr_details(device, device_type)
        try:
            rec_id = record.id
        except AttributeError:
            rec_id = record
        rec = {"name": domain_name,
              "id": rec_id,
              "type": "PTR",
              "data": data,
            }
        if ttl is not None:
            # Minimum TTL is 300 seconds
            rec["ttl"] = max(300, ttl)
        if comment is not None:
            # Maximum comment length is 160 chars
            rec["comment"] = comment[:160]
        body = {"recordsList": {
                    "records": [rec]},
                "link": {
                    "content": "",
                    "href": href,
                    "rel": svc_name,
                }}
        uri = "/rdns"
        try:
            resp, resp_body = self._async_call(uri, body=body, method="PUT",
                    has_response=False, error_class=exc.PTRRecordUpdateFailed)
        except exc.EndpointNotFound as e:
            raise exc.InvalidPTRRecord("The record domain/IP address "
                    "information is not valid for this device.")
        return resp_body.get("status") == "COMPLETED"


    def delete_ptr_records(self, device, ip_address=None):
        """
        Deletes the PTR records for the specified device. If 'ip_address' is
        supplied, only the PTR records with that IP address will be deleted.
        """
        device_type = self._resolve_device_type(device)
        href, svc_name = self._get_ptr_details(device, device_type)
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        if ip_address:
            uri = "%s&ip=%s" % (uri, ip_address)
        resp, resp_body = self._async_call(uri, method="DELETE",
                has_response=False,
                error_class=exc.PTRRecordDeletionFailed)
        return resp_body.get("status") == "COMPLETED"



class CloudDNSClient(BaseClient):
    """
    This is the primary class for interacting with Cloud DNS.
    """
    name = "Cloud DNS"

    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = CloudDNSManager(self, resource_class=CloudDNSDomain,
                response_key="domains", plural_response_key="domains",
                uri_base="domains")


    def _create_body(self, name, emailAddress, ttl=3600, comment=None,
            subdomains=None, records=None):
        """
        Creates the appropriate dict for creating a new domain.
        """
        if subdomains is None:
            subdomains = []
        if records is None:
            records = []
        body = {"domains": [{
                "name": name,
                "emailAddress": emailAddress,
                "ttl": ttl,
                "comment": comment,
                "subdomains": {
                    "domains": subdomains
                    },
                "recordsList": {
                    "records": records
                    },
                }]}
        return body


    def set_timeout(self, timeout):
        """
        Sets the amount of time that calls will wait for a response from
        the DNS system before timing out. Setting the timeout to zero will
        cause execution to wait indefinitely until the call completes.
        """
        self._manager._set_timeout(timeout)


    def set_delay(self, delay):
        """
        Changes the interval that the program will pause in between attempts to
        see if a request has completed.
        """
        self._manager._set_delay(delay)


    def list(self, limit=None, offset=None):
        """Returns a list of all resources."""
        return self._manager.list(limit=limit, offset=offset)


    def list_previous_page(self):
        """Returns the previous page of results."""
        return self._manager.list_previous_page()


    def list_next_page(self):
        """Returns the next page of results."""
        return self._manager.list_next_page()


    def get_domain_iterator(self):
        """
        Returns an iterator that will return each available domain. If there are
        more than the limit of 100 domains, the iterator will continue to fetch
        domains from the API until all domains have been returned.
        """
        return DomainResultsIterator(self._manager)


    @assure_domain
    def changes_since(self, domain, date_or_datetime):
        """
        Gets the changes for a domain since the specified date/datetime.
        The date can be one of:
            - a Python datetime object
            - a Python date object
            - a string in the format 'YYYY-MM-YY HH:MM:SS'
            - a string in the format 'YYYY-MM-YY'

        It returns a list of dicts, whose keys depend on the specific change
        that was made. A simple example of such a change dict:

            {u'accountId': 000000,
             u'action': u'update',
             u'changeDetails': [{u'field': u'serial_number',
               u'newValue': u'1354038941',
               u'originalValue': u'1354038940'},
              {u'field': u'updated_at',
               u'newValue': u'Tue Nov 27 17:55:41 UTC 2012',
               u'originalValue': u'Tue Nov 27 17:55:40 UTC 2012'}],
             u'domain': u'example.com',
             u'targetId': 00000000,
             u'targetType': u'Domain'}
        """
        return domain.changes_since(date_or_datetime)


    @assure_domain
    def export_domain(self, domain):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as
        such, does not provide subdomain information.

        Sample export:

            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. '
                'foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        return domain.export()


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        return self._manager.import_domain(domain_data)


    @assure_domain
    def update_domain(self, domain, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        return domain.update(emailAddress=emailAddress,
                ttl=ttl, comment=comment)


    @assure_domain
    def delete(self, domain, delete_subdomains=False):
        """
        Deletes the specified domain and all of its resource records. If the
        domain has subdomains, each subdomain will now become a root domain. If
        you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        domain.delete(delete_subdomains=delete_subdomains)


    @assure_domain
    def list_subdomains(self, domain, limit=None, offset=None):
        """
        Returns a list of all subdomains for the specified domain.
        """
        return domain.list_subdomains(limit=limit, offset=offset)


    def get_subdomain_iterator(self, domain, limit=None, offset=None):
        """
        Returns an iterator that will return each available subdomain for the
        specified domain. If there are more than the limit of 100 subdomains,
        the iterator will continue to fetch subdomains from the API until all
        subdomains have been returned.
        """
        return SubdomainResultsIterator(self._manager, domain=domain)


    def list_subdomains_previous_page(self):
        """Returns the previous page of subdomain results."""
        return self._manager.list_subdomains_previous_page()


    def list_subdomains_next_page(self):
        """Returns the next page of subdomain results."""
        return self._manager.list_subdomains_next_page()


    @assure_domain
    def list_records(self, domain, limit=None, offset=None):
        """
        Returns a list of all records configured for the specified domain.
        """
        return domain.list_records(limit=limit, offset=offset)


    def get_record_iterator(self, domain):
        """
        Returns an iterator that will return each available DNS record for the
        specified domain. If there are more than the limit of 100 records, the
        iterator will continue to fetch records from the API until all records
        have been returned.
        """
        return RecordResultsIterator(self._manager, domain=domain)


    def list_records_previous_page(self):
        """Returns the previous page of record results."""
        return self._manager.list_records_previous_page()


    def list_records_next_page(self):
        """Returns the next page of record results."""
        return self._manager.list_records_next_page()


    @assure_domain
    def search_records(self, domain, record_type, name=None, data=None):
        """
        Returns a list of all records configured for the specified domain
        that match the supplied search criteria.
        """
        return domain.search_records(record_type=record_type,
                name=name, data=data)


    @assure_domain
    def find_record(self, domain, record_type, name=None, data=None):
        """
        Returns a single record for this domain that matches the supplied
        search criteria.

        If no record matches, a DomainRecordNotFound exception will be raised.
        If more than one matches, a DomainRecordNotUnique exception will
        be raised.
        """
        return domain.find_record(record_type=record_type,
                name=name, data=data)


    @assure_domain
    def add_records(self, domain, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            - type (required)
            - name (required)
            - data (required)
            - ttl (optional)
            - comment (optional)
            - priority (required for MX and SRV records; forbidden otherwise)
        """
        return domain.add_records(records)

    #Create an alias, so that adding a single record is more intuitive
    add_record = add_records


    @assure_domain
    def update_record(self, domain, record, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifies an existing record for a domain.
        """
        return domain.update_record(record, data=data,
                priority=priority, ttl=ttl, comment=comment)


    @assure_domain
    def delete_record(self, domain, record):
        """
        Deletes an existing record for this domain.
        """
        return domain.delete_record(record)


    def list_ptr_records(self, device):
        """
        Returns a list of all PTR records configured for this device.
        """
        return self._manager.list_ptr_records(device)


    def add_ptr_records(self, device, records):
        """
        Adds one or more PTR records to the specified device.
        """
        return self._manager.add_ptr_records(device, records)


    def update_ptr_record(self, device, record, domain_name, data=None,
            ttl=None, comment=None):
        """
        Updates a PTR record with the supplied values.
        """
        return self._manager.update_ptr_record(device, record, domain_name,
                data=data, ttl=ttl, comment=comment)


    def delete_ptr_records(self, device, ip_address=None):
        """
        Deletes the PTR records for the specified device. If 'ip_address'
        is supplied, only the PTR records with that IP address will be deleted.
        """
        return self._manager.delete_ptr_records(device, ip_address=ip_address)


    def get_absolute_limits(self):
        """
        Returns a dict with the absolute limits for the current account.
        """
        resp, body = self.method_get("/limits")
        absolute_limits = body.get("limits", {}).get("absolute")
        return absolute_limits


    def get_rate_limits(self):
        """
        Returns a dict with the current rate limit information for domain
        and status requests.
        """
        resp, body = self.method_get("/limits")
        rate_limits = body.get("limits", {}).get("rate")
        ret = []
        for rate_limit in rate_limits:
            limits = rate_limit["limit"]
            uri_limits = {"uri": rate_limit["uri"],
                    "limits": limits}
            ret.append(uri_limits)
        return ret



class ResultsIterator(object):
    """
    This object will iterate over all the results for a given
    type of listing, no matter how many items exist.

    This is an abstract class; subclasses must define the
    _init_methods() method.
    """
    def __init__(self, manager, domain=None):
        self.manager = manager
        self.domain = domain
        self.domain_id = utils.get_id(domain) if domain else None
        self.results = []
        self.next_uri = ""
        self.extra_args = tuple()
        self._init_methods()


    def _init_methods(self):
        """
        Must be implemented in subclasses.
        """
        raise NotImplementedError()


    def __iter__(self):
        return self


    def next(self):
        """
        Return the next available item. If there are no more items in the
        local 'results' list, check if there is a 'next_uri' value. If so,
        use that to get the next page of results from the API, and return
        the first item from that query.
        """
        try:
            return self.results.pop(0)
        except IndexError:
            if self.next_uri is None:
                raise StopIteration()
            else:
                if not self.next_uri:
                    if self.domain:
                        self.results = self.list_method(self.domain)
                    else:
                        self.results = self.list_method()
                else:
                    args = self.extra_args
                    self.results = self._list_method(self.next_uri, *args)
                self.next_uri = self.manager._paging.get(
                        self.paging_service, {}).get("next_uri")
        # We should have more results.
        try:
            return self.results.pop(0)
        except IndexError:
            raise StopIteration()


class DomainResultsIterator(ResultsIterator):
    """
    ResultsIterator subclass for iterating over all domains.
    """
    def _init_methods(self):
        self.list_method = self.manager.list
        self._list_method = self.manager._list
        self.paging_service = "domain"


class SubdomainResultsIterator(ResultsIterator):
    """
    ResultsIterator subclass for iterating over all subdomains.
    """
    def _init_methods(self):
        self.list_method = self.manager.list_subdomains
        self._list_method = self.manager._list_subdomains
        self.extra_args = (self.domain_id, )
        self.paging_service = "subdomain"


class RecordResultsIterator(ResultsIterator):
    """
    ResultsIterator subclass for iterating over all domain records.
    """
    def _init_methods(self):
        self.list_method = self.manager.list_records
        self._list_method = self.manager._list_records
        self.paging_service = "record"
