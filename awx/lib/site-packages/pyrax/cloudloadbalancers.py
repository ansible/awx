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

import six

import pyrax
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


def assure_parent(fnc):
    @wraps(fnc)
    def wrapped(self, *args, **kwargs):
        lb = self.parent
        if not lb:
            exc_class = {Node: exc.UnattachedNode,
                    VirtualIP: exc.UnattachedVirtualIP}[self.__class__]
            raise exc_class("No parent Load Balancer for this node could "
                    "be determined.")
        return fnc(self, *args, **kwargs)
    return wrapped


def assure_loadbalancer(fnc):
    @wraps(fnc)
    def _wrapped(self, loadbalancer, *args, **kwargs):
        if not isinstance(loadbalancer, CloudLoadBalancer):
            # Must be the ID
            loadbalancer = self._manager.get(loadbalancer)
        return fnc(self, loadbalancer, *args, **kwargs)
    return _wrapped



class CloudLoadBalancer(BaseResource):
    """Represents a Cloud Load Balancer instance."""
    def __init__(self, *args, **kwargs):
        self._connection_logging = None
        self._content_caching = None
        self._session_persistence = None
        self._non_display = ["nodes", "virtual_ips"]
        super(CloudLoadBalancer, self).__init__(*args, **kwargs)


    def add_nodes(self, nodes):
        """Adds the nodes to this load balancer."""
        return self.manager.add_nodes(self, nodes)


    def add_virtualip(self, vip):
        """Adds the virtual IP to this load balancer."""
        return self.manager.add_virtualip(self, vip)


    def get_usage(self, start=None, end=None):
        """
        Return the usage records for this load balancer. You may optionally
        include a start datetime or an end datetime, or both, which will limit
        the records to those on or after the start time, and those before or on
        the end time. These times should be Python datetime.datetime objects,
        Python datetime.date objects, or strings in the format:
        "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD".
        """
        return self.manager.get_usage(self, start=start, end=end)


    def _add_details(self, info):
        """Override the base behavior to add Nodes, VirtualIPs, etc."""
        for (key, val) in info.iteritems():
            if key == "nodes":
                val = [Node(parent=self, **nd) for nd in val]
            elif key == "sessionPersistence":
                val = val['persistenceType']
            elif key == "cluster":
                val = val['name']
            elif key == "virtualIps":
                key = "virtual_ips"
                val = [VirtualIP(parent=self, **vip) for vip in val]
            setattr(self, key, val)


    def update(self, name=None, algorithm=None, protocol=None, halfClosed=None,
            port=None, timeout=None, httpsRedirect=None):
        """
        Provides a way to modify the following attributes of a load balancer:
            - name
            - algorithm
            - protocol
            - halfClosed
            - port
            - timeout
            - httpsRedirect
        """
        return self.manager.update(self, name=name, algorithm=algorithm,
                protocol=protocol, halfClosed=halfClosed, port=port,
                timeout=timeout, httpsRedirect=httpsRedirect)


    def delete_node(self, node):
        """Removes the node from the load balancer."""
        return self.manager.delete_node(self, node)


    def update_node(self, node, diff=None):
        """Updates the node's attributes."""
        return self.manager.update_node(node, diff=diff)


    def delete_virtualip(self, vip):
        """Deletes the VirtualIP from its load balancer."""
        return self.manager.delete_virtualip(self, vip)


    def get_access_list(self):
        """
        Returns the current access list for the load balancer.
        """
        return self.manager.get_access_list(self)


    def add_access_list(self, access_list):
        """
        Adds the access list provided to the load balancer.

        The 'access_list' should be a dict in the following format:

            {"accessList": [
                {"address": "192.0.43.10", "type": "DENY"},
                {"address": "192.0.43.11", "type": "ALLOW"},
                ...
                {"address": "192.0.43.99", "type": "DENY"},
                ]
            }

        If no access list exists, it is created. If an access list
        already exists, it is updated with the provided list.
        """
        return self.manager.add_access_list(self, access_list)


    def delete_access_list(self):
        """
        Removes the access list from this load balancer.
        """
        return self.manager.delete_access_list(self)


    def delete_access_list_items(self, item_ids):
        """
        Removes the item(s) from the load balancer's access list
        that match the provided IDs. 'item_ids' should be one or
        more access list item IDs.
        """
        return self.manager.delete_access_list_items(self, item_ids)


    def get_health_monitor(self):
        """
        Returns a dict representing the health monitor for the load
        balancer. If no monitor has been configured, returns an
        empty dict.
        """
        return self.manager.get_health_monitor(self)


    def add_health_monitor(self, type, delay=10, timeout=10,
            attemptsBeforeDeactivation=3, path="/", statusRegex=None,
            bodyRegex=None, hostHeader=None):
        """
        Adds a health monitor to the load balancer. If a monitor already
        exists, it is updated with the supplied settings.
        """
        abd = attemptsBeforeDeactivation
        return self.manager.add_health_monitor(self, type=type, delay=delay,
                timeout=timeout, attemptsBeforeDeactivation=abd,
                path=path, statusRegex=statusRegex, bodyRegex=bodyRegex,
                hostHeader=hostHeader)


    def delete_health_monitor(self):
        """
        Deletes the health monitor for the load balancer.
        """
        return self.manager.delete_health_monitor(self)


    def get_connection_throttle(self):
        """
        Returns a dict representing the connection throttling information
        for the load balancer. If no connection throttle has been configured,
        returns an empty dict.
        """
        return self.manager.get_connection_throttle(self)


    def add_connection_throttle(self, maxConnectionRate=None,
            maxConnections=None, minConnections=None, rateInterval=None):
        """
        Updates the connection throttling information for the load balancer with
        the supplied values. At least one of the parameters must be supplied.
        """
        if not any((maxConnectionRate, maxConnections, minConnections,
                rateInterval)):
            # Pointless call
            return
        return self.manager.add_connection_throttle(self,
                maxConnectionRate=maxConnectionRate, maxConnections=maxConnections,
                minConnections=minConnections, rateInterval=rateInterval)


    def delete_connection_throttle(self):
        """
        Deletes all connection throttling settings for the load balancer.
        """
        return self.manager.delete_connection_throttle(self)


    def get_ssl_termination(self):
        """
        Returns a dict representing the SSL termination configuration
        for the load balancer. If SSL termination has not been configured,
        returns an empty dict.
        """
        return self.manager.get_ssl_termination(self)


    def add_ssl_termination(self, securePort, privatekey, certificate,
            intermediateCertificate=None, enabled=True,
            secureTrafficOnly=False):
        """
        Adds SSL termination information to the load balancer. If SSL
        termination has already been configured, it is updated with the
        supplied settings.
        """
        return self.manager.add_ssl_termination(self, securePort=securePort,
                privatekey=privatekey, certificate=certificate,
                intermediateCertificate=intermediateCertificate,
                enabled=enabled, secureTrafficOnly=secureTrafficOnly)


    def update_ssl_termination(self, securePort=None, enabled=None,
            secureTrafficOnly=None):
        """
        Updates existing SSL termination information for the load balancer
        without affecting the existing certificates/keys.
        """
        return self.manager.update_ssl_termination(self, securePort=securePort,
                enabled=enabled, secureTrafficOnly=secureTrafficOnly)


    def delete_ssl_termination(self):
        """
        Removes SSL termination for the load balancer.
        """
        return self.manager.delete_ssl_termination(self)


    def get_metadata(self):
        """
        Returns the current metadata for the load balancer.
        """
        return self.manager.get_metadata(self)


    def set_metadata(self, metadata):
        """
        Sets the metadata for the load balancer to the supplied dictionary
        of values. Any existing metadata is cleared.
        """
        return self.manager.set_metadata(self, metadata)


    def update_metadata(self, metadata):
        """
        Updates the existing metadata for the load balancer with
        the supplied dictionary.
        """
        return self.manager.update_metadata(self, metadata)


    def delete_metadata(self, keys=None):
        """
        Deletes metadata items specified by the 'keys' parameter for
        this load balancer. If no value for 'keys' is provided, all
        metadata is deleted.
        """
        return self.manager.delete_metadata(self, keys=keys)


    def get_metadata_for_node(self, node):
        """
        Returns the current metadata for the specified node.
        """
        return self.manager.get_metadata(self, node=node)


    def set_metadata_for_node(self, node, metadata):
        """
        Sets the metadata for the specified node to the supplied dictionary
        of values. Any existing metadata is cleared.
        """
        return self.manager.set_metadata(self, metadata, node=node)


    def update_metadata_for_node(self, node, metadata):
        """
        Updates the existing metadata for the specified node with
        the supplied dictionary.
        """
        return self.manager.update_metadata(self, metadata, node=node)


    def delete_metadata_for_node(self, node, keys=None):
        """
        Deletes metadata items specified by the 'keys' parameter for
        the specified node. If no value for 'keys' is provided, all
        metadata is deleted.
        """
        return self.manager.delete_metadata(self, keys=keys, node=node)


    def get_error_page(self):
        """
        Returns the current error page for the load balancer.

        Load balancers all have a default error page that is shown to
        an end user who is attempting to access a load balancer node
        that is offline/unavailable.
        """
        return self.manager.get_error_page(self)


    def set_error_page(self, html):
        """
        Sets a custom error page for the load balancer.

        A single custom error page may be added per account load balancer
        with an HTTP protocol. Page updates will override existing content.
        If a custom error page is deleted, or the load balancer is changed
        to a non-HTTP protocol, the default error page will be restored.
        """
        return self.manager.set_error_page(self, html)


    def clear_error_page(self):
        """
        Resets the error page to the default.
        """
        return self.manager.clear_error_page(self)


    # BEGIN - property definitions ##
    def _get_connection_logging(self):
        if self._connection_logging is None:
            self._connection_logging = self.manager.get_connection_logging(self)
        return self._connection_logging

    def _set_connection_logging(self, val):
        self.manager.set_connection_logging(self, val)
        self._connection_logging = val


    def _get_content_caching(self):
        if self._content_caching is None:
            self._content_caching = self.manager.get_content_caching(self)
        return self._content_caching

    def _set_content_caching(self, val):
        self.manager.set_content_caching(self, val)
        self._content_caching = val


    def _get_session_persistence(self):
        if self._session_persistence is None:
            self._session_persistence = self.manager.get_session_persistence(self)
        return self._session_persistence

    def _set_session_persistence(self, val):
        if val:
            if not isinstance(val, six.string_types) or (val.upper() not in
                    ("HTTP_COOKIE", "SOURCE_IP")):
                raise exc.InvalidSessionPersistenceType("Session Persistence "
                        "must be one of 'HTTP_COOKIE' or 'SOURCE_IP'. '%s' is "
                        "not a valid setting." % val)
            self.manager.set_session_persistence(self, val)
            self._session_persistence = val.upper()
        else:
            self.manager.delete_session_persistence(self)
            self._session_persistence = ""


    connection_logging = property(_get_connection_logging,
            _set_connection_logging, None, "The current state of connection "
            "logging. Possible values are True or False.")
    content_caching = property(_get_content_caching, _set_content_caching,
            None, "The current state of content caching. Possible values are "
            "True or False.")
    session_persistence = property(_get_session_persistence,
            _set_session_persistence, None, "The current state of session "
            "persistence. Possible values are either 'HTTP_COOKIE' or "
            "'SOURCE_IP', depending on the type of load balancing.")
    # END - property definitions ##



class CloudLoadBalancerManager(BaseManager):
    def update(self, lb, name=None, algorithm=None, protocol=None,
            halfClosed=None, port=None, timeout=None, httpsRedirect=None):
        """
        Provides a way to modify the following attributes of a load balancer:
            - name
            - algorithm
            - protocol
            - halfClosed
            - port
            - timeout
            - httpsRedirect
        """
        body = {}
        if name is not None:
            body["name"] = name
        if algorithm is not None:
            body["algorithm"] = algorithm
        if protocol is not None:
            body["protocol"] = protocol
        if halfClosed is not None:
            body["halfClosed"] = halfClosed
        if port is not None:
            body["port"] = port
        if timeout is not None:
            body["timeout"] = timeout
        if httpsRedirect is not None:
            body["httpsRedirect"] = httpsRedirect
        if not body:
            # Nothing passed
            return
        body = {"loadBalancer": body}
        uri = "/loadbalancers/%s" % utils.get_id(lb)
        try:
            resp, resp_body = self.api.method_put(uri, body=body)
        except exc.ClientException as e:
            message = e.message
            details = e.details
            if message and details:
                errmsg = "%s - %s" % (message, details)
            else:
                errmsg = message
            raise exc.InvalidLoadBalancerParameters(errmsg)
        return resp, resp_body


    def _create_body(self, name, port=None, protocol=None, nodes=None,
            virtual_ips=None, algorithm=None, halfClosed=None, accessList=None,
            connectionLogging=None, connectionThrottle=None, healthMonitor=None,
            metadata=None, timeout=None, sessionPersistence=None,
            httpsRedirect=None):
        """
        Used to create the dict required to create a load balancer instance.
        """
        required = (virtual_ips, port, protocol)
        if not all(required):
            raise exc.MissingLoadBalancerParameters("Load Balancer creation "
                "requires at least one virtual IP, a protocol, and a port.")
        nodes = utils.coerce_string_to_list(nodes)
        virtual_ips = utils.coerce_string_to_list(virtual_ips)
        bad_conditions = [node.condition for node in nodes
                if node.condition.upper() not in ("ENABLED", "DISABLED")]
        if bad_conditions:
            raise exc.InvalidNodeCondition("Nodes for new load balancer must be "
                    "created in either 'ENABLED' or 'DISABLED' condition; "
                    "received the following invalid conditions: %s" %
                    ", ".join(set(bad_conditions)))
        node_dicts = [nd.to_dict() for nd in nodes]
        vip_dicts = [vip.to_dict() for vip in virtual_ips]
        body = {"loadBalancer": {
                "name": name,
                "port": port,
                "protocol": protocol,
                "nodes": node_dicts,
                "virtualIps": vip_dicts,
                "algorithm": algorithm or "RANDOM",
                "halfClosed": halfClosed,
                "accessList": accessList,
                "connectionLogging": connectionLogging,
                "connectionThrottle": connectionThrottle,
                "healthMonitor": healthMonitor,
                "metadata": metadata,
                "timeout": timeout,
                "sessionPersistence": sessionPersistence,
                "httpsRedirect": httpsRedirect,
                }}
        return body


    def add_nodes(self, lb, nodes):
        """Adds the list of nodes to the specified load balancer."""
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        node_dicts = [nd.to_dict() for nd in nodes]
        resp, body = self.api.method_post("/loadbalancers/%s/nodes" % lb.id,
                body={"nodes": node_dicts})
        return resp, body


    def delete_node(self, loadbalancer, node):
        """Removes the node from its load balancer."""
        lb = node.parent
        if not lb:
            raise exc.UnattachedNode("No parent Load Balancer for this node "
                    "could be determined.")
        resp, body = self.api.method_delete("/loadbalancers/%s/nodes/%s" %
                (lb.id, node.id))
        return resp, body


    def update_node(self, node, diff=None):
        """Updates the node's attributes."""
        lb = node.parent
        if not lb:
            raise exc.UnattachedNode("No parent Load Balancer for this node "
                    "could be determined.")
        if diff is None:
            diff = node._diff()
        req_body = {"node": diff}
        resp, body = self.api.method_put("/loadbalancers/%s/nodes/%s" %
                (lb.id, node.id), body=req_body)
        return resp, body


    def add_virtualip(self, lb, vip):
        """Adds the VirtualIP to the specified load balancer."""
        resp, body = self.api.method_post("/loadbalancers/%s/virtualips" % lb.id,
                body=vip.to_dict())
        return resp, body


    def delete_virtualip(self, loadbalancer, vip):
        """Deletes the VirtualIP from its load balancer."""
        lb = vip.parent
        if not lb:
            raise exc.UnattachedVirtualIP("No parent Load Balancer for this "
                    "VirtualIP could be determined.")
        resp, body = self.api.method_delete("/loadbalancers/%s/virtualips/%s" %
                (lb.id, vip.id))
        return resp, body


    def get_access_list(self, loadbalancer):
        """
        Returns the current access list for the load balancer.
        """
        uri = "/loadbalancers/%s/accesslist" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        return body.get("accessList")


    def add_access_list(self, loadbalancer, access_list):
        """
        Adds the access list provided to the load balancer.

        The 'access_list' should be a list of dicts in the following format:

            [{"address": "192.0.43.10", "type": "DENY"},
             {"address": "192.0.43.11", "type": "ALLOW"},
             ...
             {"address": "192.0.43.99", "type": "DENY"},
            ]

        If no access list exists, it is created. If an access list
        already exists, it is updated with the provided list.
        """
        req_body = {"accessList": access_list}
        uri = "/loadbalancers/%s/accesslist" % utils.get_id(loadbalancer)
        resp, body = self.api.method_post(uri, body=req_body)
        return body


    def delete_access_list(self, loadbalancer):
        """
        Removes the access list from this load balancer.
        """
        uri = "/loadbalancers/%s/accesslist" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)
        return body


    def delete_access_list_items(self, loadbalancer, item_ids):
        """
        Removes the item(s) from the load balancer's access list
        that match the provided IDs. 'item_ids' should be one or
        more access list item IDs.
        """
        if not isinstance(item_ids, (list, tuple)):
            item_ids = [item_ids]
        valid_ids = [itm["id"] for itm in self.get_access_list(loadbalancer)]
        bad_ids = [str(itm) for itm in item_ids if itm not in valid_ids]
        if bad_ids:
            raise exc.AccessListIDNotFound("The following ID(s) are not valid "
                    "Access List items: %s" % ", ".join(bad_ids))
        items = "&".join(["id=%s" % item_id for item_id in item_ids])
        uri = "/loadbalancers/%s/accesslist?%s" % (
                utils.get_id(loadbalancer), items)
        # TODO: add the item ids
        resp, body = self.api.method_delete(uri)
        return body


    def get_health_monitor(self, loadbalancer):
        """
        Returns a dict representing the health monitor for the load
        balancer. If no monitor has been configured, returns an
        empty dict.
        """
        uri = "/loadbalancers/%s/healthmonitor" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        return body.get("healthMonitor", {})


    def add_health_monitor(self, loadbalancer, type, delay=10, timeout=10,
            attemptsBeforeDeactivation=3, path="/", statusRegex=None,
            bodyRegex=None, hostHeader=None):
        """
        Adds a health monitor to the load balancer. If a monitor already
        exists, it is updated with the supplied settings.
        """
        uri = "/loadbalancers/%s/healthmonitor" % utils.get_id(loadbalancer)
        req_body = {"healthMonitor": {
                "type": type,
                "delay": delay,
                "timeout": timeout,
                "attemptsBeforeDeactivation": attemptsBeforeDeactivation,
                }}
        uptype = type.upper()
        if uptype.startswith("HTTP"):
            lb = self._get_lb(loadbalancer)
            if uptype != lb.protocol:
                raise exc.ProtocolMismatch("Cannot set the Health Monitor type "
                        "to '%s' when the Load Balancer's protocol is '%s'." %
                        (type, lb.protocol))
            if not all((path, statusRegex, bodyRegex)):
                raise exc.MissingHealthMonitorSettings("When creating an HTTP(S) "
                        "monitor, you must provide the 'path', 'statusRegex' and "
                        "'bodyRegex' parameters.")
            body_hm = req_body["healthMonitor"]
            body_hm["path"] = path
            body_hm["statusRegex"] = statusRegex
            body_hm["bodyRegex"] = bodyRegex
            if hostHeader:
                body_hm["hostHeader"] = hostHeader
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def delete_health_monitor(self, loadbalancer):
        """
        Deletes the health monitor for the load balancer.
        """
        uri = "/loadbalancers/%s/healthmonitor" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)


    def get_connection_throttle(self, loadbalancer):
        """
        Returns a dict representing the connection throttling information
        for the load balancer. If no connection throttle has been configured,
        returns an empty dict.
        """
        uri = "/loadbalancers/%s/connectionthrottle" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        return body.get("connectionThrottle", {})


    def add_connection_throttle(self, loadbalancer, maxConnectionRate=None,
            maxConnections=None, minConnections=None, rateInterval=None):
        """
        Creates or updates the connection throttling information for the load
        balancer. When first creating the connection throttle, all 4 parameters
        must be supplied. When updating an existing connection throttle, at
        least one of the parameters must be supplied.
        """
        settings = {}
        if maxConnectionRate:
            settings["maxConnectionRate"] = maxConnectionRate
        if maxConnections:
            settings["maxConnections"] = maxConnections
        if minConnections:
            settings["minConnections"] = minConnections
        if rateInterval:
            settings["rateInterval"] = rateInterval
        req_body = {"connectionThrottle": settings}
        uri = "/loadbalancers/%s/connectionthrottle" % utils.get_id(loadbalancer)
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def delete_connection_throttle(self, loadbalancer):
        """
        Deletes all connection throttling settings for the load balancer.
        """
        uri = "/loadbalancers/%s/connectionthrottle" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)


    def get_ssl_termination(self, loadbalancer):
        """
        Returns a dict representing the SSL termination configuration
        for the load balancer. If SSL termination has not been configured,
        returns an empty dict.
        """
        uri = "/loadbalancers/%s/ssltermination" % utils.get_id(loadbalancer)
        try:
            resp, body = self.api.method_get(uri)
        except exc.NotFound:
            # For some reason, instead of returning an empty dict like the
            # other API GET calls, this raises a 404.
            return {}
        return body.get("sslTermination", {})


    def add_ssl_termination(self, loadbalancer, securePort, privatekey, certificate,
            intermediateCertificate, enabled=True, secureTrafficOnly=False):
        """
        Adds SSL termination information to the load balancer. If SSL termination
        has already been configured, it is updated with the supplied settings.
        """
        uri = "/loadbalancers/%s/ssltermination" % utils.get_id(loadbalancer)
        req_body = {"sslTermination": {
                "certificate": certificate,
                "enabled": enabled,
                "secureTrafficOnly": secureTrafficOnly,
                "privatekey": privatekey,
                "intermediateCertificate": intermediateCertificate,
                "securePort": securePort,
                }}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def update_ssl_termination(self, loadbalancer, securePort=None, enabled=None,
            secureTrafficOnly=None):
        """
        Updates existing SSL termination information for the load balancer
        without affecting the existing certificates/keys.
        """
        ssl_info = self.get_ssl_termination(loadbalancer)
        if not ssl_info:
            raise exc.NoSSLTerminationConfiguration("You must configure SSL "
                    "termination on this load balancer before attempting "
                    "to update it.")
        if securePort is None:
            securePort = ssl_info["securePort"]
        if enabled is None:
            enabled = ssl_info["enabled"]
        if secureTrafficOnly is None:
            secureTrafficOnly = ssl_info["secureTrafficOnly"]
        uri = "/loadbalancers/%s/ssltermination" % utils.get_id(loadbalancer)
        req_body = {"sslTermination": {
                "enabled": enabled,
                "secureTrafficOnly": secureTrafficOnly,
                "securePort": securePort,
                }}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def delete_ssl_termination(self, loadbalancer):
        """
        Deletes the SSL Termination configuration for the load balancer.
        """
        uri = "/loadbalancers/%s/ssltermination" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)


    def get_metadata(self, loadbalancer, node=None, raw=False):
        """
        Returns the current metadata for the load balancer. If 'node' is
        provided, returns the current metadata for that node.
        """
        if node:
            uri = "/loadbalancers/%s/nodes/%s/metadata" % (
                    utils.get_id(loadbalancer), utils.get_id(node))
        else:
            uri = "/loadbalancers/%s/metadata" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        meta = body.get("metadata", [])
        if raw:
            return meta
        ret = dict([(itm["key"], itm["value"]) for itm in meta])
        return ret


    def set_metadata(self, loadbalancer, metadata, node=None):
        """
        Sets the metadata for the load balancer to the supplied dictionary
        of values. Any existing metadata is cleared. If 'node' is provided,
        the metadata for that node is set instead of for the load balancer.
        """
        # Delete any existing metadata
        self.delete_metadata(loadbalancer, node=node)
        # Convert the metadata dict into the list format
        metadata_list = [{"key": key, "value": val}
                for key, val in metadata.items()]
        if node:
            uri = "/loadbalancers/%s/nodes/%s/metadata" % (
                    utils.get_id(loadbalancer), utils.get_id(node))
        else:
            uri = "/loadbalancers/%s/metadata" % utils.get_id(loadbalancer)
        req_body = {"metadata": metadata_list}
        resp, body = self.api.method_post(uri, body=req_body)
        return body


    def update_metadata(self, loadbalancer, metadata, node=None):
        """
        Updates the existing metadata with the supplied dictionary. If
        'node' is supplied, the metadata for that node is updated instead
        of for the load balancer.
        """
        # Get the existing metadata
        md = self.get_metadata(loadbalancer, raw=True)
        id_lookup = dict([(itm["key"], itm["id"]) for itm in md])
        metadata_list = []
        # Updates must be done individually
        for key, val in metadata.items():
            try:
                meta_id = id_lookup[key]
                if node:
                    uri = "/loadbalancers/%s/nodes/%s/metadata/%s" % (
                            utils.get_id(loadbalancer), utils.get_id(node),
                            meta_id)
                else:
                    uri = "/loadbalancers/%s/metadata" % utils.get_id(loadbalancer)
                req_body = {"meta": {"value": val}}
                resp, body = self.api.method_put(uri, body=req_body)
            except KeyError:
                # Not an existing key; add to metadata_list
                metadata_list.append({"key": key, "value": val})
        if metadata_list:
            # New items; POST them
            if node:
                uri = "/loadbalancers/%s/nodes/%s/metadata" % (
                        utils.get_id(loadbalancer), utils.get_id(node))
            else:
                uri = "/loadbalancers/%s/metadata" % utils.get_id(loadbalancer)
            req_body = {"metadata": metadata_list}
            resp, body = self.api.method_post(uri, body=req_body)


    def delete_metadata(self, loadbalancer, keys=None, node=None):
        """
        Deletes metadata items specified by the 'keys' parameter. If no value
        for 'keys' is provided, all metadata is deleted. If 'node' is supplied,
        the metadata for that node is deleted instead of the load balancer.
        """
        if keys and not isinstance(keys, (list, tuple)):
            keys = [keys]
        md = self.get_metadata(loadbalancer, node=node, raw=True)
        if keys:
            md = [dct for dct in md if dct["key"] in keys]
        if not md:
            # Nothing to do; log it? Raise an error?
            return
        id_list = "&".join(["id=%s" % itm["id"] for itm in md])
        if node:
            uri = "/loadbalancers/%s/nodes/%s/metadata?%s" % (
                    utils.get_id(loadbalancer), utils.get_id(node), id_list)
        else:
            uri = "/loadbalancers/%s/metadata?%s" % (
                    utils.get_id(loadbalancer), id_list)
        resp, body = self.api.method_delete(uri)
        return body


    def get_error_page(self, loadbalancer):
        """
        Load Balancers all have a default error page that is shown to
        an end user who is attempting to access a load balancer node
        that is offline/unavailable.
        """
        uri = "/loadbalancers/%s/errorpage" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        return body


    def set_error_page(self, loadbalancer, html):
        """
        A single custom error page may be added per account load balancer
        with an HTTP protocol. Page updates will override existing content.
        If a custom error page is deleted, or the load balancer is changed
        to a non-HTTP protocol, the default error page will be restored.
        """
        uri = "/loadbalancers/%s/errorpage" % utils.get_id(loadbalancer)
        req_body = {"errorpage": {"content": html}}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def clear_error_page(self, loadbalancer):
        """
        Resets the error page to the default.
        """
        uri = "/loadbalancers/%s/errorpage" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)
        return body


    def get_usage(self, loadbalancer=None, start=None, end=None):
        """
        Return the load balancer usage records for this account. If 'loadbalancer'
        is None, records for all load balancers are returned. You may optionally
        include a start datetime or an end datetime, or both, which will limit
        the records to those on or after the start time, and those before or on the
        end time. These times should be Python datetime.datetime objects, Python
        datetime.date objects, or strings in the format: "YYYY-MM-DD HH:MM:SS" or
        "YYYY-MM-DD".
        """
        if start is end is None:
            period = None
        else:
            parts = []
            startStr = utils.iso_time_string(start)
            if startStr:
                parts.append("startTime=%s" % startStr)
            endStr = utils.iso_time_string(end)
            if endStr:
                parts.append("endTime=%s" % endStr)
            period = "&".join(parts).strip("&")
        if loadbalancer is None:
            uri = "/loadbalancers/usage"
        else:
            uri = "/loadbalancers/%s/usage" % utils.get_id(loadbalancer)
        if period:
            uri = "%s?%s" % (uri, period)
        resp, body = self.api.method_get(uri)
        return body


    def get_stats(self, loadbalancer):
        """
        Returns statistics for the given load balancer.
        """
        uri = "/loadbalancers/%s/stats" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        return body


    def get_session_persistence(self, loadbalancer):
        """
        Returns the session persistence setting for the given load balancer.
        """
        uri = "/loadbalancers/%s/sessionpersistence" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        ret = body["sessionPersistence"].get("persistenceType", "")
        return ret


    def set_session_persistence(self, loadbalancer, val):
        """
        Sets the session persistence for the given load balancer.
        """
        val = val.upper()
        uri = "/loadbalancers/%s/sessionpersistence" % utils.get_id(loadbalancer)
        req_body = {"sessionPersistence": {
                "persistenceType": val,
                }}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def delete_session_persistence(self, loadbalancer):
        """
        Removes the session persistence setting for the given load balancer.
        """
        uri = "/loadbalancers/%s/sessionpersistence" % utils.get_id(loadbalancer)
        resp, body = self.api.method_delete(uri)
        return body


    def get_connection_logging(self, loadbalancer):
        """
        Returns the connection logging setting for the given load balancer.
        """
        uri = "/loadbalancers/%s/connectionlogging" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        ret = body.get("connectionLogging", {}).get("enabled", False)
        return ret


    def set_connection_logging(self, loadbalancer, val):
        """
        Sets the connection logging for the given load balancer.
        """
        uri = "/loadbalancers/%s/connectionlogging" % utils.get_id(loadbalancer)
        val = str(val).lower()
        req_body = {"connectionLogging": {
                "enabled": val,
                }}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def get_content_caching(self, loadbalancer):
        """
        Returns the content caching setting for the given load balancer.
        """
        uri = "/loadbalancers/%s/contentcaching" % utils.get_id(loadbalancer)
        resp, body = self.api.method_get(uri)
        ret = body.get("contentCaching", {}).get("enabled", False)
        return ret


    def set_content_caching(self, loadbalancer, val):
        """
        Sets the content caching for the given load balancer.
        """
        uri = "/loadbalancers/%s/contentcaching" % utils.get_id(loadbalancer)
        val = str(val).lower()
        req_body = {"contentCaching": {
                "enabled": val,
                }}
        resp, body = self.api.method_put(uri, body=req_body)
        return body


    def _get_lb(self, lb_or_id):
        """
        Accepts either a loadbalancer or the ID of a loadbalancer, and returns
        the CloudLoadBalancer instance.
        """
        if isinstance(lb_or_id, CloudLoadBalancer):
            ret = lb_or_id
        else:
            ret = self.get(lb_or_id)
        return ret



class Node(object):
    """Represents a Node for a Load Balancer."""
    def __init__(self, address=None, port=None, condition=None, weight=None,
            status=None, parent=None, type=None, id=None):
        if condition is None:
            condition = "ENABLED"
        if not all((address, port)):
            raise exc.InvalidNodeParameters("You must include an address and a "
            "port when creating a node.")
        self.address = address
        self.port = port
        self.condition = condition
        if weight is None:
            weight = 1
        self.weight = weight
        self.status = status
        self.parent = parent
        self.type = type
        self.id = id
        self._original_state = self.to_dict()


    def __repr__(self):
        tmp = "<Node type=%s, condition=%s, id=%s, address=%s, port=%s weight=%s>"
        return tmp % (self.type, self.condition, self.id, self.address, self.port,
                self.weight)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        """Convert this Node to a dict representation for passing to the API."""
        return {"address": self.address,
                "port": self.port,
                "condition": self.condition,
                "type": self.type,
                "id": self.id,
                }


    def get_metadata(self):
        """
        Returns the current metadata for the node.
        """
        return self.manager.get_metadata(self, node=self)


    def set_metadata(self, metadata):
        """
        Sets the metadata for the node to the supplied dictionary
        of values. Any existing metadata is cleared.
        """
        return self.manager.set_metadata(self, metadata, node=self)


    def update_metadata(self, metadata):
        """
        Updates the existing metadata for the node with
        the supplied dictionary.
        """
        return self.manager.update_metadata(self, metadata, node=self)


    def delete_metadata(self, keys=None):
        """
        Deletes metadata items specified by the 'keys' parameter for
        this node. If no value for 'keys' is provided, all
        metadata is deleted.
        """
        return self.manager.delete_metadata(self, keys=keys, node=self)


    @assure_parent
    def delete(self):
        """Removes this Node from its Load Balancer."""
        self.parent.delete_node(self)


    def _diff(self):
        diff_dict = {}
        for att, val in self._original_state.items():
            curr = getattr(self, att)
            if curr != val:
                diff_dict[att] = curr
        return diff_dict


    @assure_parent
    def update(self):
        """
        Pushes any local changes to the object up to the actual load
        balancer node.
        """
        diff = self._diff()
        if not diff:
            # Nothing to do!
            return
        self.parent.update_node(self, diff)


    def get_device(self):
        """
        Returns a reference to the device that is represented by this node.
        Returns None if no such device can be determined.
        """
        addr = self.address
        servers = [server for server in pyrax.cloudservers.list()
                if addr in server.networks.get("private", "")]
        try:
            return servers[0]
        except IndexError:
            return None



class VirtualIP(object):
    """Represents a Virtual IP for a Load Balancer."""
    def __init__(self, type=None, address=None, ipVersion=None, id=None,
            parent=None):
        if type is None:
            type = "PUBLIC"
        if type.upper() not in ("PUBLIC", "SERVICENET"):
            raise exc.InvalidVirtualIPType("Virtual IPs must be one of "
                    "'PUBLIC' or 'SERVICENET' type; '%s' is not valid." % type)
        if not ipVersion:
            ipVersion = "IPV4"
        if not ipVersion.upper() in ("IPV4", "IPV6"):
            raise exc.InvalidVirtualIPVersion("Virtual IP versions must be one "
                    "of 'IPV4' or 'IPV6'; '%s' is not valid." % ipVersion)
        self.type = type
        self.address = address
        self.ip_version = ipVersion
        self.id = id
        self.parent = parent


    def __repr__(self):
        return "<VirtualIP type=%s, id=%s, address=%s version=%s>" % (
                self.type, self.id, self.address, self.ip_version)


    def to_dict(self):
        """
        Convert this VirtualIP to a dict representation for passing
        to the API.
        """
        if self.id:
            return {"id": self.id}
        return {"type": self.type, "ipVersion": self.ip_version}


    @assure_parent
    def delete(self):
        self.parent.delete_virtualip(self)



class CloudLoadBalancerClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Load Balancers.
    """
    name = "Cloud Load Balancers"

    def __init__(self, *args, **kwargs):
        # Bring these two classes into the Client namespace
        self.Node = Node
        self.VirtualIP = VirtualIP
        self._algorithms = None
        self._protocols = None
        self._allowed_domains = None
        super(CloudLoadBalancerClient, self).__init__(*args, **kwargs)


    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = CloudLoadBalancerManager(self,
                resource_class=CloudLoadBalancer,
                response_key="loadBalancer", uri_base="loadbalancers")


    def get_usage(self, loadbalancer=None, start=None, end=None):
        """
        Return the load balancer usage records for this account. If 'loadbalancer'
        is None, records for all load balancers are returned. You may optionally
        include a start datetime or an end datetime, or both, which will limit
        the records to those on or after the start time, and those before or on the
        end time. These times should be Python datetime.datetime objects, Python
        datetime.date objects, or strings in the format: "YYYY-MM-DD HH:MM:SS" or
        "YYYY-MM-DD".
        """
        return self._manager.get_usage(loadbalancer=loadbalancer, start=start,
                end=end)


    @property
    def allowed_domains(self):
        """
        This property lists the allowed domains for a load balancer.

        The allowed domains are restrictions set for the allowed domain names
        used for adding load balancer nodes. In order to submit a domain name
        as an address for the load balancer node to add, the user must verify
        that the domain is valid by using the List Allowed Domains call. Once
        verified, simply supply the domain name in place of the node's address
        in the add_nodes() call.
        """
        if self._allowed_domains is None:
            uri = "/loadbalancers/alloweddomains"
            resp, body = self.method_get(uri)
            dom_list = body["allowedDomains"]
            self._allowed_domains = [itm["allowedDomain"]["name"]
                    for itm in dom_list]
        return self._allowed_domains


    @property
    def algorithms(self):
        """
        Returns a list of available load balancing algorithms.
        """
        if self._algorithms is None:
            uri = "/loadbalancers/algorithms"
            resp, body = self.method_get(uri)
            self._algorithms = [alg["name"] for alg in body["algorithms"]]
        return self._algorithms


    @property
    def protocols(self):
        """
        Returns a list of available load balancing protocols.
        """
        if self._protocols is None:
            uri = "/loadbalancers/protocols"
            resp, body = self.method_get(uri)
            self._protocols = [proto["name"] for proto in body["protocols"]]
        return self._protocols


    @assure_loadbalancer
    def update(self, loadbalancer, name=None, algorithm=None, protocol=None,
            halfClosed=None, port=None, timeout=None, httpsRedirect=None):
        """
        Provides a way to modify the following attributes of a load balancer:
            - name
            - algorithm
            - protocol
            - halfClosed
            - port
            - timeout
            - httpsRedirect
        """
        return self._manager.update(loadbalancer, name=name,
                algorithm=algorithm, protocol=protocol, halfClosed=halfClosed,
                port=port, timeout=timeout, httpsRedirect=httpsRedirect)


    @assure_loadbalancer
    def add_nodes(self, loadbalancer, nodes):
        """Adds the nodes to this load balancer."""
        return loadbalancer.add_nodes(nodes)


    @assure_loadbalancer
    def add_virtualip(self, loadbalancer, vip):
        """Adds the virtual IP to this load balancer."""
        return loadbalancer.add_virtualip(vip)


    def delete_node(self, node):
        """Removes the node from its load balancer."""
        return node.delete()


    def update_node(self, node):
        """Updates the node's attributes."""
        return node.update()


    def delete_virtualip(self, vip):
        """Deletes the VirtualIP from its load balancer."""
        return vip.delete()


    @assure_loadbalancer
    def get_access_list(self, loadbalancer):
        """
        Returns the current access list for the load balancer.
        """
        return loadbalancer.get_access_list()


    @assure_loadbalancer
    def add_access_list(self, loadbalancer, access_list):
        """
        Adds the access list provided to the load balancer.

        The 'access_list' should be a dict in the following format:

            {"accessList": [
                {"address": "192.0.43.10", "type": "DENY"},
                {"address": "192.0.43.11", "type": "ALLOW"},
                ...
                {"address": "192.0.43.99", "type": "DENY"},
                ]
            }

        If no access list exists, it is created. If an access list
        already exists, it is updated with the provided list.
        """
        return loadbalancer.add_access_list(access_list)


    @assure_loadbalancer
    def delete_access_list(self, loadbalancer):
        """
        Removes the access list from this load balancer.
        """
        return loadbalancer.delete_access_list()


    @assure_loadbalancer
    def delete_access_list_items(self, loadbalancer, item_ids):
        """
        Removes the item(s) from the load balancer's access list
        that match the provided IDs. 'item_ids' should be one or
        more access list item IDs.
        """
        return loadbalancer.delete_access_list_items(item_ids)


    @assure_loadbalancer
    def get_health_monitor(self, loadbalancer):
        """
        Returns a dict representing the health monitor for the load
        balancer. If no monitor has been configured, returns an
        empty dict.
        """
        return loadbalancer.get_health_monitor()


    @assure_loadbalancer
    def add_health_monitor(self, loadbalancer, type, delay=10, timeout=10,
            attemptsBeforeDeactivation=3, path="/", statusRegex=None,
            bodyRegex=None, hostHeader=None):
        """
        Adds a health monitor to the load balancer. If a monitor already
        exists, it is updated with the supplied settings.
        """
        abd = attemptsBeforeDeactivation
        return loadbalancer.add_health_monitor(type=type, delay=delay,
                timeout=timeout, attemptsBeforeDeactivation=abd, path=path,
                statusRegex=statusRegex, bodyRegex=bodyRegex,
                hostHeader=hostHeader)


    @assure_loadbalancer
    def delete_health_monitor(self, loadbalancer):
        """
        Deletes the health monitor for the load balancer.
        """
        return loadbalancer.delete_health_monitor()


    @assure_loadbalancer
    def get_connection_throttle(self, loadbalancer):
        """
        Returns a dict representing the connection throttling information
        for the load balancer. If no connection throttle has been configured,
        returns an empty dict.
        """
        return loadbalancer.get_connection_throttle()


    @assure_loadbalancer
    def add_connection_throttle(self, loadbalancer, maxConnectionRate=None,
            maxConnections=None, minConnections=None, rateInterval=None):
        """
        Updates the connection throttling information for the load balancer with
        the supplied values. At least one of the parameters must be supplied.
        """
        return loadbalancer.add_connection_throttle(
                maxConnectionRate=maxConnectionRate, maxConnections=maxConnections,
                minConnections=minConnections, rateInterval=rateInterval)


    @assure_loadbalancer
    def delete_connection_throttle(self, loadbalancer):
        """
        Deletes all connection throttling settings for the load balancer.
        """
        return loadbalancer.delete_connection_throttle()


    @assure_loadbalancer
    def get_ssl_termination(self, loadbalancer):
        """
        Returns a dict representing the SSL termination configuration
        for the load balancer. If SSL termination has not been configured,
        returns an empty dict.
        """
        return loadbalancer.get_ssl_termination()


    @assure_loadbalancer
    def add_ssl_termination(self, loadbalancer, securePort, privatekey,
            certificate, intermediateCertificate, enabled=True,
            secureTrafficOnly=False):
        """
        Adds SSL termination information to the load balancer. If SSL termination
        has already been configured, it is updated with the supplied settings.
        """
        return loadbalancer.add_ssl_termination(securePort=securePort,
                privatekey=privatekey, certificate=certificate,
                intermediateCertificate=intermediateCertificate,
                enabled=enabled, secureTrafficOnly=secureTrafficOnly)


    @assure_loadbalancer
    def update_ssl_termination(self, loadbalancer, securePort=None, enabled=None,
            secureTrafficOnly=None):
        """
        Updates existing SSL termination information for the load balancer
        without affecting the existing certificates/keys.
        """
        return loadbalancer.update_ssl_termination(securePort=securePort,
                enabled=enabled, secureTrafficOnly=secureTrafficOnly)


    @assure_loadbalancer
    def delete_ssl_termination(self, loadbalancer):
        """
        Removes SSL termination for the load balancer.
        """
        return loadbalancer.delete_ssl_termination()


    @assure_loadbalancer
    def get_metadata(self, loadbalancer):
        """
        Returns the current metadata for the load balancer.
        """
        return loadbalancer.get_metadata()


    @assure_loadbalancer
    def set_metadata(self, loadbalancer, metadata):
        """
        Sets the metadata for the load balancer to the supplied dictionary
        of values. Any existing metadata is cleared.
        """
        return loadbalancer.set_metadata(metadata)


    @assure_loadbalancer
    def update_metadata(self, loadbalancer, metadata):
        """
        Updates the existing metadata for the load balancer with
        the supplied dictionary.
        """
        return loadbalancer.update_metadata(metadata)


    @assure_loadbalancer
    def delete_metadata(self, loadbalancer, keys=None):
        """
        Deletes metadata items specified by the 'keys' parameter for
        this load balancer. If no value for 'keys' is provided, all
        metadata is deleted.
        """
        return loadbalancer.delete_metadata(keys=keys)


    @assure_loadbalancer
    def get_metadata_for_node(self, loadbalancer, node):
        """
        Returns the current metadata for the specified node.
        """
        return loadbalancer.get_metadata_for_node(node)


    @assure_loadbalancer
    def set_metadata_for_node(self, loadbalancer, node, metadata):
        """
        Sets the metadata for the specified node to the supplied dictionary
        of values. Any existing metadata is cleared.
        """
        return loadbalancer.set_metadata_for_node(node, metadata)


    @assure_loadbalancer
    def update_metadata_for_node(self, loadbalancer, node, metadata):
        """
        Updates the existing metadata for the specified node with
        the supplied dictionary.
        """
        return loadbalancer.update_metadata_for_node(node, metadata)


    @assure_loadbalancer
    def delete_metadata_for_node(self, loadbalancer, node, keys=None):
        """
        Deletes metadata items specified by the 'keys' parameter for
        the specified node. If no value for 'keys' is provided, all
        metadata is deleted.
        """
        return loadbalancer.delete_metadata_for_node(node, keys=keys)


    @assure_loadbalancer
    def get_error_page(self, loadbalancer):
        """
        Load Balancers all have a default error page that is shown to
        an end user who is attempting to access a load balancer node
        that is offline/unavailable.
        """
        return loadbalancer.get_error_page()


    @assure_loadbalancer
    def set_error_page(self, loadbalancer, html):
        """
        A single custom error page may be added per account load balancer
        with an HTTP protocol. Page updates will override existing content.
        If a custom error page is deleted, or the load balancer is changed
        to a non-HTTP protocol, the default error page will be restored.
        """
        return loadbalancer.set_error_page(html)


    @assure_loadbalancer
    def clear_error_page(self, loadbalancer):
        """
        Resets the error page to the default.
        """
        return loadbalancer.clear_error_page()


    @assure_loadbalancer
    def get_connection_logging(self, loadbalancer):
        """
        Returns the current setting for connection logging for the load balancer.
        """
        return loadbalancer.connection_logging


    @assure_loadbalancer
    def set_connection_logging(self, loadbalancer, val):
        """
        Sets connection logging for the load balancer to either True
        or False.
        """
        loadbalancer.connection_logging = val


    @assure_loadbalancer
    def get_content_caching(self, loadbalancer):
        """
        Returns the current setting for content caching for the load balancer.
        """
        return loadbalancer.content_caching


    @assure_loadbalancer
    def set_content_caching(self, loadbalancer, val):
        """
        Sets content caching for the load balancer to either True
        or False.
        """
        loadbalancer.content_caching = val


    @assure_loadbalancer
    def get_session_persistence(self, loadbalancer):
        """
        Returns the current setting for session persistence for
        the load balancer.
        """
        return loadbalancer.session_persistence


    @assure_loadbalancer
    def set_session_persistence(self, loadbalancer, val):
        """
        Sets the type of session persistence for the load balancer. This
        must be one of either "HTTP_COOKIE" or "SOURCE_IP", depending
        on the type of load balancing.
        """
        loadbalancer.session_persistence = val

    # END pass-through methods ##
