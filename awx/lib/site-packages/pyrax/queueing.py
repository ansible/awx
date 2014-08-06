#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c)2012 Rackspace US, Inc.

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
import os
import re
from six.moves import urllib_parse as urlparse

import pyrax
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils

# The hard-coded maximum number of messages returned in a single call.
MSG_LIMIT = 10
# Pattern for extracting the marker value from an href link.
marker_pat = re.compile(r".+\bmarker=(\d+).*")


def _parse_marker(body):
    marker = None
    links = body.get("links", [])
    next_links = [link for link in links if link.get("rel") == "next"]
    try:
        next_link = next_links[0]["href"]
    except IndexError:
        next_link = ""
    mtch = marker_pat.match(next_link)
    if mtch:
        marker = mtch.groups()[0]
    return marker


def assure_queue(fnc):
    """
    Converts a queue ID or name passed as the 'queue' parameter to a Queue
    object.
    """
    @wraps(fnc)
    def _wrapped(self, queue, *args, **kwargs):
        if not isinstance(queue, Queue):
            # Must be the ID
            queue = self._manager.get(queue)
        return fnc(self, queue, *args, **kwargs)
    return _wrapped



class BaseQueueManager(BaseManager):
    """
    This class attempts to add in all the common deviations from the API
    standards that the regular base classes are based on.
    """
    def _list(self, uri, obj_class=None, body=None, return_raw=False):
        try:
            return super(BaseQueueManager, self)._list(uri, obj_class=None,
                    body=None, return_raw=return_raw)
        except (exc.NotFound, AttributeError):
            return []



class Queue(BaseResource):
    """
    This class represents a Queue.
    """
    def __init__(self, manager, info, key=None, loaded=False):
        # Queues are often returned with no info
        info = info or {"queue": {}}
        super(Queue, self).__init__(manager, info, key=key, loaded=loaded)
        self._repr_properties = ["id"]
        self._message_manager = QueueMessageManager(self.manager.api,
                resource_class=QueueMessage, response_key="",
                plural_response_key="messages",
                uri_base="queues/%s/messages" % self.id)
        self._claim_manager = QueueClaimManager(self.manager.api,
                resource_class=QueueClaim, response_key="",
                plural_response_key="claims",
                uri_base="queues/%s/claims" % self.id)
        self._claim_manager._message_manager = self._message_manager


    def get_message(self, msg_id):
        """
        Returns the message whose ID matches the supplied msg_id from this
        queue.
        """
        return self._message_manager.get(msg_id)


    def delete_message(self, msg_id, claim_id=None):
        """
        Deletes the message whose ID matches the supplied msg_id from the
        specified queue. If the message has been claimed, the ID of that claim
        must be passed as the 'claim_id' parameter.
        """
        return self._message_manager.delete(msg_id, claim_id=claim_id)


    def list(self, include_claimed=False, echo=False, marker=None, limit=None):
        """
        Returns a list of messages for this queue.

        By default only unclaimed messages are returned; if you want claimed
        messages included, pass `include_claimed=True`. Also, the requester's
        own messages are not returned by default; if you want them included,
        pass `echo=True`.

        The 'marker' and 'limit' parameters are used to control pagination of
        results. 'Marker' is the ID of the last message returned, while 'limit'
        controls the number of messages returned per reuqest (default=20).
        """
        return self._message_manager.list(include_claimed=include_claimed,
                echo=echo, marker=marker, limit=limit)


    def list_by_ids(self, ids):
        """
        If you wish to retrieve a list of messages from this queue and know the
        IDs of those messages, you can pass in a list of those IDs, and only
        the matching messages will be returned. This avoids pulling down all
        the messages in a queue and filtering on the client side.
        """
        return self._message_manager.list_by_ids(ids)


    def delete_by_ids(self, ids):
        """
        Deletes the messages whose IDs are passed in from this queue.
        """
        return self._message_manager.delete_by_ids(ids)


    def list_by_claim(self, claim):
        """
        Returns a list of all the messages from this queue that have been
        claimed by the specified claim. The claim can be either a claim ID or a
        QueueClaim object.
        """
        if not isinstance(claim, QueueClaim):
            claim = self._claim_manager.get(claim)
        return claim.messages


    def post_message(self, body, ttl):
        """
        Create a message in this queue. The value of ttl must be between 60 and
        1209600 seconds (14 days).
        """
        return self._message_manager.create(body, ttl)


    def claim_messages(self, ttl, grace, count=None):
        """
        Claims up to `count` unclaimed messages from this queue. If count is
        not specified, the default is to claim 10 messages.

        The `ttl` parameter specifies how long the server should wait before
        releasing the claim. The ttl value MUST be between 60 and 43200 seconds.

        The `grace` parameter is the message grace period in seconds. The value
        of grace MUST be between 60 and 43200 seconds. The server extends the
        lifetime of claimed messages to be at least as long as the lifetime of
        the claim itself, plus a specified grace period to deal with crashed
        workers (up to 1209600 or 14 days including claim lifetime). If a
        claimed message would normally live longer than the grace period, its
        expiration will not be adjusted.

        Returns a QueueClaim object, whose 'messages' attribute contains the
        list of QueueMessage objects representing the claimed messages.
        """
        return self._claim_manager.claim(ttl, grace, count=count)


    def get_claim(self, claim):
        """
        Returns a QueueClaim object with information about the specified claim.
        If no such claim exists, a NotFound exception is raised.
        """
        return self._claim_manager.get(claim)


    def update_claim(self, claim, ttl=None, grace=None):
        """
        Updates the specified claim with either a new TTL or grace period, or
        both.
        """
        return self._claim_manager.update(claim, ttl=ttl, grace=grace)


    def release_claim(self, claim):
        """
        Releases the specified claim and makes any messages previously claimed
        by this claim as available for processing by other workers.
        """
        return self._claim_manager.delete(claim)


    @property
    def id(self):
        return self.name

    @id.setter
    def id(self, val):
        self.name = val



class QueueMessage(BaseResource):
    """
    This class represents a Message posted to a Queue.
    """
    def __init__(self, *args, **kwargs):
        self.id = None
        self.age = None
        self.body = None
        self.href = None
        self.ttl = None
        self.claim_id = None
        super(QueueMessage, self).__init__(*args, **kwargs)


    def _add_details(self, info):
        """
        The 'id' and 'claim_id' attributes are not supplied directly, but
        included as part of the 'href' value.
        """
        super(QueueMessage, self)._add_details(info)
        if self.href is None:
            return
        parsed = urlparse.urlparse(self.href)
        self.id = parsed.path.rsplit("/", 1)[-1]
        query = parsed.query
        if query:
            self.claim_id = query.split("claim_id=")[-1]


    def delete(self, claim_id=None):
        """
        Deletes this message from its queue. If the message has been claimed,
        the ID of that claim must be passed as the 'claim_id' parameter.
        """
        return self.manager.delete(self, claim_id=claim_id)



class QueueClaim(BaseResource):
    """
    This class represents a Claim for a Message posted by a consumer.
    """
    id = None
    messages = None
    href = ""

    def _add_details(self, info):
        """
        The 'id' attribute is not supplied directly, but included as part of
        the 'href' value. Also, convert the dicts for messages into
        QueueMessage objects.
        """
        msg_dicts = info.pop("messages", [])
        super(QueueClaim, self)._add_details(info)
        parsed = urlparse.urlparse(self.href)
        self.id = parsed.path.rsplit("/", 1)[-1]
        self.messages = [QueueMessage(self.manager._message_manager, item)
                for item in msg_dicts]



class QueueMessageManager(BaseQueueManager):
    """
    Manager class for a Queue Message.
    """
    def _create_body(self, msg, ttl):
        """
        Used to create the dict required to create a new message.
        """
        body = [{
                "body": msg,
                "ttl": ttl,
                }]
        return body


    def list(self, include_claimed=False, echo=False, marker=None, limit=None):
        """
        Need to form the URI differently, so we can't use the default list().
        """
        return self._iterate_list(include_claimed=include_claimed, echo=echo,
                marker=marker, limit=limit)


    def _iterate_list(self, include_claimed, echo, marker, limit):
        """
        Recursive method to work around the hard limit of 10 items per call.
        """
        ret = []
        if limit is None:
            this_limit = MSG_LIMIT
        else:
            this_limit = min(MSG_LIMIT, limit)
            limit = limit - this_limit
        uri = "/%s?include_claimed=%s&echo=%s" % (self.uri_base,
                json.dumps(include_claimed), json.dumps(echo))
        qs_parts = []
        if marker is not None:
            qs_parts.append("marker=%s" % marker)
        if this_limit is not None:
            qs_parts.append("limit=%s" % this_limit)
        if qs_parts:
            uri = "%s&%s" % (uri, "&".join(qs_parts))
        resp, resp_body = self._list(uri, return_raw=True)
        if not resp_body:
            return ret
        messages = resp_body.get(self.plural_response_key, [])
        ret = [QueueMessage(manager=self, info=item) for item in messages]
        marker = _parse_marker(resp_body)

        loop = 0
        if ((limit is None) or limit > 0) and marker:
            loop += 1
            ret.extend(self._iterate_list(include_claimed, echo, marker, limit))
        return ret


    def delete(self, msg, claim_id=None):
        """
        Deletes the specified message from its queue. If the message has been
        claimed, the ID of that claim must be passed as the 'claim_id'
        parameter.
        """
        msg_id = utils.get_id(msg)
        if claim_id:
            uri = "/%s/%s?claim_id=%s" % (self.uri_base, msg_id, claim_id)
        else:
            uri = "/%s/%s" % (self.uri_base, msg_id)
        return self._delete(uri)


    def list_by_ids(self, ids):
        """
        If you wish to retrieve a list of messages from this queue and know the
        IDs of those messages, you can pass in a list of those IDs, and only
        the matching messages will be returned. This avoids pulling down all
        the messages in a queue and filtering on the client side.
        """
        ids = utils.coerce_string_to_list(ids)
        uri = "/%s?ids=%s" % (self.uri_base, ",".join(ids))
        # The API is not consistent in how it returns message lists, so this
        # workaround is needed.
        curr_prkey = self.plural_response_key
        self.plural_response_key = ""
        # BROKEN: API returns a list, not a dict.
        ret = self._list(uri)
        self.plural_response_key = curr_prkey
        return ret


    def delete_by_ids(self, ids):
        """
        Deletes the messages whose IDs are passed in from this queue.
        """
        ids = utils.coerce_string_to_list(ids)
        uri = "/%s?ids=%s" % (self.uri_base, ",".join(ids))
        return self.api.method_delete(uri)



class QueueClaimManager(BaseQueueManager):
    """
    Manager class for a Queue Claims.
    """
    def claim(self, ttl, grace, count=None):
        """
        Claims up to `count` unclaimed messages from this queue. If count is
        not specified, the default is to claim 10 messages.

        The `ttl` parameter specifies how long the server should wait before
        releasing the claim. The ttl value MUST be between 60 and 43200 seconds.

        The `grace` parameter is the message grace period in seconds. The value
        of grace MUST be between 60 and 43200 seconds. The server extends the
        lifetime of claimed messages to be at least as long as the lifetime of
        the claim itself, plus a specified grace period to deal with crashed
        workers (up to 1209600 or 14 days including claim lifetime). If a
        claimed message would normally live longer than the grace period, its
        expiration will not be adjusted.

        bReturns a QueueClaim object, whose 'messages' attribute contains the
        list of QueueMessage objects representing the claimed messages.
        """
        if count is None:
            qs = ""
        else:
            qs = "?limit=%s" % count
        uri = "/%s%s" % (self.uri_base, qs)
        body = {"ttl": ttl,
                "grace": grace,
                }
        resp, resp_body = self.api.method_post(uri, body=body)
        if resp.status_code == 204:
            # Nothing available to claim
            return None
        # Get the claim ID from the first message in the list.
        href = resp_body[0]["href"]
        claim_id = href.split("claim_id=")[-1]
        return self.get(claim_id)


    def update(self, claim, ttl=None, grace=None):
        """
        Updates the specified claim with either a new TTL or grace period, or
        both.
        """
        body = {}
        if ttl is not None:
            body["ttl"] = ttl
        if grace is not None:
            body["grace"] = grace
        if not body:
            raise exc.MissingClaimParameters("You must supply a value for "
                    "'ttl' or 'grace' when calling 'update()'")
        uri = "/%s/%s" % (self.uri_base, utils.get_id(claim))
        resp, resp_body = self.api.method_patch(uri, body=body)



class QueueManager(BaseQueueManager):
    """
    Manager class for a Queue.
    """
    def _create_body(self, name, metadata=None):
        """
        Used to create the dict required to create a new queue
        """
        if metadata is None:
            body = {}
        else:
            body = {"metadata": metadata}
        return body


    def get(self, id_):
        """
        Need to customize, since Queues are not returned with normal response
        bodies.
        """
        if self.api.queue_exists(id_):
            return Queue(self, {"queue": {"name": id_, "id_": id_}}, key="queue")
        raise exc.NotFound("The queue '%s' does not exist." % id_)


    def create(self, name):
        uri = "/%s/%s" % (self.uri_base, name)
        resp, resp_body = self.api.method_put(uri)
        if resp.status_code == 201:
            return Queue(self, {"name": name})
        elif resp.status_code == 400:
            # Most likely an invalid name
            raise exc.InvalidQueueName("Queue names must not exceed 64 bytes "
                    "in length, and are limited to US-ASCII letters, digits, "
                    "underscores, and hyphens. Submitted: '%s'." % name)


    def get_stats(self, queue):
        """
        Returns the message stats for the specified queue.
        """
        uri = "/%s/%s/stats" % (self.uri_base, utils.get_id(queue))
        resp, resp_body = self.api.method_get(uri)
        return resp_body.get("messages")


    def get_metadata(self, queue):
        """
        Returns the metadata for the specified queue.
        """
        uri = "/%s/%s/metadata" % (self.uri_base, utils.get_id(queue))
        resp, resp_body = self.api.method_get(uri)
        return resp_body


    def set_metadata(self, queue, metadata, clear=False):
        """
        Accepts a dictionary and adds that to the specified queue's metadata.
        If the 'clear' argument is passed as True, any existing metadata is
        replaced with the new metadata.
        """
        uri = "/%s/%s/metadata" % (self.uri_base, utils.get_id(queue))
        if clear:
            curr = {}
        else:
            curr = self.get_metadata(queue)
        curr.update(metadata)
        resp, resp_body = self.api.method_put(uri, body=curr)



class QueueClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Queues.
    """
    name = "Cloud Queues"
    client_id = None


    def _configure_manager(self):
        """
        Create the manager to handle queues.
        """
        self._manager = QueueManager(self,
                resource_class=Queue, response_key="queue",
                uri_base="queues")


    def _add_custom_headers(self, dct):
        """
        Add the Client-ID header required by Cloud Queues
        """
        if self.client_id is None:
            self.client_id = os.environ.get("CLOUD_QUEUES_ID")
        if self.client_id:
            dct["Client-ID"] = self.client_id


    def _api_request(self, uri, method, **kwargs):
        """
        Any request that involves messages must define the client ID. This
        handles all failures due to lack of client ID and raises the
        appropriate exception.
        """
        try:
            return super(QueueClient, self)._api_request(uri, method, **kwargs)
        except exc.BadRequest as e:
            if ((e.code == "400") and
                    (e.message == 'The "Client-ID" header is required.')):
                raise exc.QueueClientIDNotDefined("You must supply a client ID "
                        "to work with Queue messages.")
            else:
                raise


    def get_home_document(self):
        """
        You should never need to use this method; it is included for
        completeness. It is meant to be used for API clients that need to
        explore the API with no prior knowledge. This knowledge is already
        included in the SDK, so it should never be necessary to work at this
        basic a level, as all the functionality is exposed through normal
        Python methods in the client.

        If you are curious about the 'Home Document' concept, here is the
        explanation from the Cloud Queues documentation:

        The entire API is discoverable from a single starting point - the home
        document. You do not need to know any more than this one URI in order
        to explore the entire API. This document is cacheable.

        The home document lets you write clients using a "follow-your-nose"
        style so clients do not have to construct their own URLs. You can click
        through and view the JSON doc in your browser.

        For more information about home documents, see
        http://tools.ietf.org/html/draft-nottingham-json-home-02.
        """
        uri = self.management_url.rsplit("/", 1)[0]
        return self.method_get(uri)


    def queue_exists(self, name):
        """
        Returns True or False, depending on the existence of the named queue.
        """
        try:
            queue = self._manager.head(name)
            return True
        except exc.NotFound:
            return False


    def create(self, name):
        """
        Cloud Queues works differently, in that they use the name as the ID for
        the resource. So for create(), we need to check if a queue by that name
        exists already, and raise an exception if it does. If not, create the
        queue and return a reference object for it.
        """
        if self.queue_exists(name):
            raise exc.DuplicateQueue("The queue '%s' already exists." % name)
        return self._manager.create(name)


    def get_stats(self, queue):
        """
        Returns the message stats for the specified queue.
        """
        return self._manager.get_stats(queue)


    def get_metadata(self, queue):
        """
        Returns the metadata for the specified queue.
        """
        return self._manager.get_metadata(queue)


    def set_metadata(self, queue, metadata, clear=False):
        """
        Accepts a dictionary and adds that to the specified queue's metadata.
        If the 'clear' argument is passed as True, any existing metadata is
        replaced with the new metadata.
        """
        return self._manager.set_metadata(queue, metadata, clear=clear)


    @assure_queue
    def get_message(self, queue, msg_id):
        """
        Returns the message whose ID matches the supplied msg_id from the
        specified queue.
        """
        return queue.get_message(msg_id)


    @assure_queue
    def delete_message(self, queue, msg_id, claim_id=None):
        """
        Deletes the message whose ID matches the supplied msg_id from the
        specified queue. If the message has been claimed, the ID of that claim
        must be passed as the 'claim_id' parameter.
        """
        return queue.delete_message(msg_id, claim_id=claim_id)


    @assure_queue
    def list_messages(self, queue, include_claimed=False, echo=False,
            marker=None, limit=None):
        """
        Returns a list of messages for the specified queue.

        By default only unclaimed messages are returned; if you want claimed
        messages included, pass `include_claimed=True`. Also, the requester's
        own messages are not returned by default; if you want them included,
        pass `echo=True`.

        The 'marker' and 'limit' parameters are used to control pagination of
        results. 'Marker' is the ID of the last message returned, while 'limit'
        controls the number of messages returned per reuqest (default=20).
        """
        return queue.list(include_claimed=include_claimed, echo=echo,
                marker=marker, limit=limit)


    @assure_queue
    def list_messages_by_ids(self, queue, ids):
        """
        If you wish to retrieve a list of messages from a queue and know the
        IDs of those messages, you can pass in a list of those IDs, and only
        the matching messages will be returned. This avoids pulling down all
        the messages in a queue and filtering on the client side.
        """
        return queue.list_by_ids(ids)


    @assure_queue
    def delete_messages_by_ids(self, queue, ids):
        """
        Deletes the messages whose IDs are passed in from the specified queue.
        """
        return queue.delete_by_ids(ids)


    @assure_queue
    def list_messages_by_claim(self, queue, claim):
        """
        Returns a list of all the messages from the specified queue that have
        been claimed by the specified claim. The claim can be either a claim ID
        or a QueueClaim object.
        """
        return queue.list_by_claim(claim)


    @assure_queue
    def post_message(self, queue, body, ttl):
        """
        Create a message in the specified queue. The value of ttl must be
        between 60 and 1209600 seconds (14 days).
        """
        return queue.post_message(body, ttl)


    @assure_queue
    def claim_messages(self, queue, ttl, grace, count=None):
        """
        Claims up to `count` unclaimed messages from the specified queue. If
        count is not specified, the default is to claim 10 messages.

        The `ttl` parameter specifies how long the server should wait before
        releasing the claim. The ttl value MUST be between 60 and 43200 seconds.

        The `grace` parameter is the message grace period in seconds. The value
        of grace MUST be between 60 and 43200 seconds. The server extends the
        lifetime of claimed messages to be at least as long as the lifetime of
        the claim itself, plus a specified grace period to deal with crashed
        workers (up to 1209600 or 14 days including claim lifetime). If a
        claimed message would normally live longer than the grace period, its
        expiration will not be adjusted.

        Returns a QueueClaim object, whose 'messages' attribute contains the
        list of QueueMessage objects representing the claimed messages.
        """
        return queue.claim_messages(ttl, grace, count=count)


    @assure_queue
    def get_claim(self, queue, claim):
        """
        Returns a QueueClaim object with information about the specified claim.
        If no such claim exists, a NotFound exception is raised.
        """
        return queue.get_claim(claim)


    @assure_queue
    def update_claim(self, queue, claim, ttl=None, grace=None):
        """
        Updates the specified claim with either a new TTL or grace period, or
        both.
        """
        return queue.update_claim(claim, ttl=ttl, grace=grace)


    @assure_queue
    def release_claim(self, queue, claim):
        """
        Releases the specified claim and makes any messages previously claimed
        by this claim as available for processing by other workers.
        """
        return queue.release_claim(claim)
