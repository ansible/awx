# -*- coding: utf-8 -*-

# Copyright (c)2013 Rackspace US, Inc.

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
import re

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


_invalid_key_pat = re.compile(r"Validation error for key '([^']+)'")


def _params_to_dict(params, dct, local_dict):
    for param in params:
        val = local_dict.get(param)
        if val is None:
            continue
        dct[param] = val
    return dct


def assure_check(fnc):
    """
    Converts an checkID passed as the check to a CloudMonitorCheck object.
    """
    @wraps(fnc)
    def _wrapped(self, check, *args, **kwargs):
        if not isinstance(check, CloudMonitorCheck):
            # Must be the ID
            check = self._check_manager.get(check)
        return fnc(self, check, *args, **kwargs)
    return _wrapped


def assure_entity(fnc):
    """
    Converts an entityID passed as the entity to a CloudMonitorEntity object.
    """
    @wraps(fnc)
    def _wrapped(self, entity, *args, **kwargs):
        if not isinstance(entity, CloudMonitorEntity):
            # Must be the ID
            entity = self._entity_manager.get(entity)
        return fnc(self, entity, *args, **kwargs)
    return _wrapped



class CloudMonitorEntity(BaseResource):
    def __init__(self, *args, **kwargs):
        super(CloudMonitorEntity, self).__init__(*args, **kwargs)
        self._check_manager = CloudMonitorCheckManager(self.manager.api,
                uri_base="entities/%s/checks" % self.id,
                resource_class=CloudMonitorCheck, response_key=None,
                plural_response_key=None)
        self._alarm_manager = CloudMonitorAlarmManager(self.manager.api,
                uri_base="entities/%s/alarms" % self.id,
                resource_class=CloudMonitorAlarm, response_key=None,
                plural_response_key=None)


    def update(self, agent=None, metadata=None):
        """
        Only the agent_id and metadata are able to be updated via the API.
        """
        self.manager.update_entity(self, agent=agent, metadata=metadata)


    def get_check(self, check):
        """
        Returns an instance of the specified check.
        """
        chk = self._check_manager.get(check)
        chk.set_entity(self)
        return chk


    def list_checks(self, limit=None, marker=None, return_next=False):
        """
        Returns a list of the checks defined for this account. By default the
        number returned is limited to 100; you can define the number to return
        by optionally passing a value for the 'limit' parameter. The value for
        limit must be at least 1, and can be up to 1000.

        For pagination, you must also specify the 'marker' parameter. This is
        the ID of the first item to return. To get this, pass True for the
        'return_next' parameter, and the response will be a 2-tuple, with the
        first element being the list of checks, and the second the ID of the
        next item. If there is no next item, the second element will be None.
        """
        checks = self._check_manager.list(limit=limit, marker=marker,
                return_next=return_next)
        for check in checks:
            check.set_entity(self)
        return checks


    def find_all_checks(self, **kwargs):
        """
        Finds all checks for this entity with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        checks = self._check_manager.find_all_checks(**kwargs)
        for check in checks:
            check.set_entity(self)
        return checks


    def create_check(self, label=None, name=None, check_type=None,
            disabled=False, metadata=None, details=None,
            monitoring_zones_poll=None, timeout=None, period=None,
            target_alias=None, target_hostname=None, target_receiver=None,
            test_only=False, include_debug=False):
        """
        Creates a check on this entity with the specified attributes. The
        'details' parameter should be a dict with the keys as the option name,
        and the value as the desired setting.
        """
        return self._check_manager.create_check(label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)


    def update_check(self, check, label=None, name=None, disabled=None,
            metadata=None, monitoring_zones_poll=None, timeout=None,
            period=None, target_alias=None, target_hostname=None,
            target_receiver=None):
        """
        Updates an existing check with any of the parameters.
        """
        return self._check_manager.update(check, label=label, name=name,
                disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)


    def delete_check(self, check):
        """
        Deletes the specified check from this entity.
        """
        return self._check_manager.delete(check)


    @assure_check
    def list_metrics(self, check, limit=None, marker=None, return_next=False):
        """
        Returns a list of all the metrics associated with the specified check.
        """
        return check.list_metrics(limit=limit, marker=marker,
                return_next=return_next)


    @assure_check
    def get_metric_data_points(self, check, metric, start, end, points=None,
            resolution=None, stats=None):
        """
        Returns the data points for a given metric for the given period. The
        'start' and 'end' times must be specified; they can be be either Python
        date/datetime values, or a Unix timestamp.

        The 'points' parameter represents the number of points to return. The
        'resolution' parameter represents the granularity of the data. You must
        specify either 'points' or 'resolution'. The allowed values for
        resolution are:
            FULL
            MIN5
            MIN20
            MIN60
            MIN240
            MIN1440

        Finally, the 'stats' parameter specifies the stats you want returned.
        By default only the 'average' is returned. You omit this parameter,
        pass in a single value, or pass in a list of values. The allowed values
        are:
            average
            variance
            min
            max
        """
        return check.get_metric_data_points(metric, start, end, points=points,
                resolution=resolution, stats=stats)


    def create_alarm(self, check, notification_plan, criteria=None,
            disabled=False, label=None, name=None, metadata=None):
        """
        Creates an alarm that binds the check on this entity with a
        notification plan.
        """
        return self._alarm_manager.create(check, notification_plan,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)


    def update_alarm(self, alarm, criteria=None, disabled=False,
            label=None, name=None, metadata=None):
        """
        Updates an existing alarm on this entity.
        """
        return self._alarm_manager.update(alarm, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)


    def list_alarms(self, limit=None, marker=None, return_next=False):
        """
        Returns a list of all the alarms created on this entity.
        """
        return self._alarm_manager.list(limit=limit, marker=marker,
                return_next=return_next)


    def get_alarm(self, alarm):
        """
        Returns the alarm with the specified ID for this entity. If a
        CloudMonitorAlarm instance is passed, returns a new CloudMonitorAlarm
        object with the current state from the API.
        """
        return self._alarm_manager.get(alarm)


    def delete_alarm(self, alarm):
        """
        Deletes the specified alarm.
        """
        return self._alarm_manager.delete(alarm)


    @property
    def name(self):
        return self.label



class _PaginationManager(BaseManager):
    def list(self, limit=None, marker=None, return_next=False):
        """
        This is necessary to handle pagination correctly, as the Monitoring
        service defines 'marker' differently than most other services. For
        monitoring, 'marker' represents the first item in the next page,
        whereas other services define it as the ID of the last item in the
        current page.
        """
        kwargs = {}
        if return_next:
            kwargs["other_keys"] = "metadata"
        ret = super(_PaginationManager, self).list(limit=limit,
                marker=marker, **kwargs)
        if return_next:
            ents, meta = ret
            return (ents, meta[0].get("next_marker"))
        else:
            return ret



class CloudMonitorNotificationManager(_PaginationManager):
    """
    Handles all of the requests dealing with notifications.
    """
    def create(self, notification_type, label=None, name=None, details=None):
        """
        Defines a notification for handling an alarm.
        """
        uri = "/%s" % self.uri_base
        body = {"label": label or name,
                "type": utils.get_id(notification_type),
                "details": details,
                }
        resp, resp_body = self.api.method_post(uri, body=body)
        return self.get(resp.headers["x-object-id"])


    def test_notification(self, notification=None, notification_type=None,
            details=None):
        """
        This allows you to test either an existing notification, or a potential
        notification before creating it. The actual notification comes from the
        same server where the actual alert messages come from. This allow you
        to, among other things, verify that your firewall is configured
        properly.

        To test an existing notification, pass it as the 'notification'
        parameter and leave the other parameters empty. To pre-test a
        notification before creating it, leave 'notification' empty, but pass
        in the 'notification_type' and 'details'.
        """
        if notification:
            # Test an existing notification
            uri = "/%s/%s/test" % (self.uri_base, utils.get_id(notification))
            body = None
        else:
            uri = "/test-notification"
            body = {"type": utils.get_id(notification_type),
                    "details": details}
        resp, resp_body = self.api.method_post(uri, body=body)


    def update_notification(self, notification, details):
        """
        Updates the specified notification with the supplied details.
        """
        if isinstance(notification, CloudMonitorNotification):
            nid = notification.id
            ntyp = notification.type
        else:
            # Supplied an ID
            nfcn = self.get(notification)
            nid = notification
            ntyp = nfcn.type
        uri = "/%s/%s" % (self.uri_base, nid)
        body = {"type": ntyp,
                "details": details}
        resp, resp_body = self.api.method_put(uri, body=body)


    def list_types(self):
        """
        Returns a list of all available notification types.
        """
        uri = "/notification_types"
        resp, resp_body = self.api.method_get(uri)
        return [CloudMonitorNotificationType(self, info)
                for info in resp_body["values"]]


    def get_type(self, notification_type_id):
        """
        Returns a CloudMonitorNotificationType object for the given ID.
        """
        uri = "/notification_types/%s" % utils.get_id(notification_type_id)
        resp, resp_body = self.api.method_get(uri)
        return CloudMonitorNotificationType(self, resp_body)



class CloudMonitorNotificationPlanManager(_PaginationManager):
    """
    Handles all of the requests dealing with Notification Plans.
    """
    def create(self, label=None, name=None, critical_state=None, ok_state=None,
            warning_state=None):
        """
        Creates a notification plan to be executed when a monitoring check
        triggers an alarm. You can optionally label (or name) the plan.

        A plan consists of one or more notifications to be executed when an
        associated alarm is triggered. You can have different lists of actions
        for CRITICAL, WARNING or OK states.
        """
        uri = "/%s" % self.uri_base
        body = {"label": label or name}

        def make_list_of_ids(parameter):
            params = utils.coerce_to_list(parameter)
            return [utils.get_id(param) for param in params]

        if critical_state:
            critical_state = utils.coerce_to_list(critical_state)
            body["critical_state"] = make_list_of_ids(critical_state)
        if warning_state:
            warning_state = utils.coerce_to_list(warning_state)
            body["warning_state"] = make_list_of_ids(warning_state)
        if ok_state:
            ok_state = utils.coerce_to_list(ok_state)
            body["ok_state"] = make_list_of_ids(ok_state)
        resp, resp_body = self.api.method_post(uri, body=body)
        return self.get(resp.headers["x-object-id"])



class CloudMonitorMetricsManager(_PaginationManager):
    def get_metric_data_points(self, metric, start, end, points=None,
            resolution=None, stats=None):
        """
        Returns the data points for a given metric for the given period. The
        'start' and 'end' times must be specified; they can be be either Python
        date/datetime values, or a Unix timestamp.

        The 'points' parameter represents the number of points to return. The
        'resolution' parameter represents the granularity of the data. You must
        specify either 'points' or 'resolution'. The allowed values for
        resolution are:
            FULL
            MIN5
            MIN20
            MIN60
            MIN240
            MIN1440

        Finally, the 'stats' parameter specifies the stats you want returned.
        By default only the 'average' is returned. You omit this parameter,
        pass in a single value, or pass in a list of values. The allowed values
        are:
            average
            variance
            min
            max
        """
        allowed_resolutions = ("FULL", "MIN5", "MIN20", "MIN60", "MIN240",
                "MIN1440")
        if not (points or resolution):
            raise exc.MissingMonitoringCheckGranularity("You must specify "
                    "either the 'points' or 'resolution' parameter when "
                    "fetching metrics.")
        if resolution:
            if resolution.upper() not in allowed_resolutions:
                raise exc.InvalidMonitoringMetricsResolution("The specified "
                        "resolution '%s' is not valid. The valid values are: "
                        "%s." % (resolution, str(allowed_resolutions)))
        start_tm = utils.to_timestamp(start)
        end_tm = utils.to_timestamp(end)
        # NOTE: For some odd reason, the timestamps required for this must be
        # in milliseconds, instead of the UNIX standard for timestamps, which
        # is in seconds. So the values here are multiplied by 1000 to make it
        # work. If the API is ever corrected, the next two lines should be
        # removed. GitHub #176.
        start_tm *= 1000
        end_tm *= 1000
        qparms = []
        # Timestamps with fractional seconds currently cause a 408 (timeout)
        qparms.append("from=%s" % int(start_tm))
        qparms.append("to=%s" % int(end_tm))
        if points:
            qparms.append("points=%s" % points)
        if resolution:
            qparms.append("resolution=%s" % resolution.upper())
        if stats:
            stats = utils.coerce_to_list(stats)
            for stat in stats:
                qparms.append("select=%s" % stat)
        qparm = "&".join(qparms)
        uri = "/%s/%s/plot?%s" % (self.uri_base, metric, qparm)
        try:
            resp, resp_body = self.api.method_get(uri)
        except exc.BadRequest as e:
            msg = e.message
            dtls = e.details
            if msg.startswith("Validation error"):
                raise exc.InvalidMonitoringMetricsRequest("Your request was "
                        "invalid: '%s'" % dtls)
            else:
                raise
        return resp_body["values"]



class CloudMonitorAlarmManager(_PaginationManager):
    """
    Handles all of the alarm-specific requests.
    """
    def create(self, check, notification_plan, criteria=None,
            disabled=False, label=None, name=None, metadata=None):
        """
        Creates an alarm that binds the check on the given entity with a
        notification plan.

        Note that the 'criteria' parameter, if supplied, should be a string
        representing the DSL for describing alerting conditions and their
        output states. Pyrax does not do any validation of these criteria
        statements; it is up to you as the developer to understand the language
        and correctly form the statement. This alarm language is documented
        online in the Cloud Monitoring section of http://docs.rackspace.com.
        """
        uri = "/%s" % self.uri_base
        body = {"check_id": utils.get_id(check),
                "notification_plan_id": utils.get_id(notification_plan),
                }
        if criteria:
            body["criteria"] = criteria
        if disabled is not None:
            body["disabled"] = disabled
        label_name = label or name
        if label_name:
            body["label"] = label_name
        if metadata:
            body["metadata"] = metadata
        resp, resp_body = self.api.method_post(uri, body=body)
        if resp.status_code == 201:
            alarm_id = resp.headers["x-object-id"]
            return self.get(alarm_id)


    def update(self, alarm, criteria=None, disabled=False, label=None,
            name=None, metadata=None):
        """
        Updates an existing alarm. See the comments on the 'create()' method
        regarding the criteria parameter.
        """
        uri = "/%s/%s" % (self.uri_base, utils.get_id(alarm))
        body = {}
        if criteria:
            body["criteria"] = criteria
        if disabled is not None:
            body["disabled"] = disabled
        label_name = label or name
        if label_name:
            body["label"] = label_name
        if metadata:
            body["metadata"] = metadata
        resp, resp_body = self.api.method_put(uri, body=body)



class CloudMonitorCheckManager(_PaginationManager):
    """
    Handles all of the check-specific requests.
    """
    def create_check(self, label=None, name=None, check_type=None,
            details=None, disabled=False, metadata=None,
            monitoring_zones_poll=None, timeout=None, period=None,
            target_alias=None, target_hostname=None, target_receiver=None,
            test_only=False, include_debug=False):
        """
        Creates a check on the entity with the specified attributes. The
        'details' parameter should be a dict with the keys as the option name,
        and the value as the desired setting.

        If the 'test_only' parameter is True, then the check is not created;
        instead, the check is run and the results of the test run returned. If
        'include_debug' is True, additional debug information is returned.
        According to the current Cloud Monitoring docs:
            "Currently debug information is only available for the
            remote.http check and includes the response body."
        """
        if details is None:
            raise exc.MissingMonitoringCheckDetails("The required 'details' "
                    "parameter was not passed to the create_check() method.")
        if not (target_alias or target_hostname):
            raise exc.MonitoringCheckTargetNotSpecified("You must specify "
                    "either the 'target_alias' or 'target_hostname' when "
                    "creating a check.")
        ctype = utils.get_id(check_type)
        is_remote = ctype.startswith("remote")
        monitoring_zones_poll = utils.coerce_to_list(monitoring_zones_poll)
        monitoring_zones_poll = [utils.get_id(mzp)
                for mzp in monitoring_zones_poll]
        if is_remote and not monitoring_zones_poll:
            raise exc.MonitoringZonesPollMissing("You must specify the "
                    "'monitoring_zones_poll' parameter for remote checks.")
        body = {"label": label or name,
                "details": details,
                "disabled": disabled,
                "type": utils.get_id(check_type),
                }
        params = ("monitoring_zones_poll", "timeout", "period",
                "target_alias", "target_hostname", "target_receiver")
        body = _params_to_dict(params, body, locals())
        if test_only:
            uri = "/%s/test-check" % self.uri_base
            if include_debug:
                uri = "%s?debug=true" % uri
        else:
            uri = "/%s" % self.uri_base
        try:
            resp, resp_body = self.api.method_post(uri, body=body)
        except exc.BadRequest as e:
            msg = e.message
            dtls = e.details
            match = _invalid_key_pat.match(msg)
            if match:
                missing = match.groups()[0].replace("details.", "")
                if missing in details:
                    errcls = exc.InvalidMonitoringCheckDetails
                    errmsg = "".join(["The value passed for '%s' in the ",
                            "details parameter is not valid."]) % missing
                else:
                    errmsg = "".join(["The required value for the '%s' ",
                            "setting is missing from the 'details' ",
                            "parameter."]) % missing
                    utils.update_exc(e, errmsg)
                raise e
            else:
                if msg == "Validation error":
                    # Info is in the 'details'
                    raise exc.InvalidMonitoringCheckDetails("Validation "
                            "failed. Error: '%s'." % dtls)
        else:
            if resp.status_code == 201:
                check_id = resp.headers["x-object-id"]
                return self.get(check_id)


    def update(self, check, label=None, name=None, disabled=None,
            metadata=None, monitoring_zones_poll=None, timeout=None,
            period=None, target_alias=None, target_hostname=None,
            target_receiver=None):
        if monitoring_zones_poll:
            monitoring_zones_poll = utils.coerce_to_list(monitoring_zones_poll)
            monitoring_zones_poll = [utils.get_id(mzp)
                    for mzp in monitoring_zones_poll]
        body = {}
        local_dict = locals()
        label = label or name
        params = ("label", "disabled", "metadata", "monitoring_zones_poll",
                "timeout", "period", "target_alias", "target_hostname",
                "target_receiver")
        body = _params_to_dict(params, body, locals())
        entity = check.entity
        uri = "/%s/%s" % (self.uri_base, utils.get_id(check))
        try:
            resp, resp_body = self.api.method_put(uri, body=body)
        except exc.BadRequest as e:
            msg = e.message
            dtls = e.details
            if msg.startswith("Validation error"):
                raise exc.InvalidMonitoringCheckUpdate("The update failed "
                        "validation: %s: %s" % (msg, dtls))
            else:
                # Some other issue.
                raise
        return resp_body


    def find_all_checks(self, **kwargs):
        """
        Finds all checks for a given entity with attributes matching
        ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()
        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue
        return found



class _EntityFilteringManger(BaseManager):
    """
    Handles calls that can optionally filter requests based on an entity.
    """
    def list(self, entity=None):
        """
        Returns a dictionary of data, optionally filtered for a given entity.
        """
        uri = "/%s" % self.uri_base
        if entity:
            uri = "%s?entityId=%s" % (uri, utils.get_id(entity))
        resp, resp_body = self._list(uri, return_raw=True)
        return resp_body



class CloudMonitorEntityManager(_PaginationManager):
    """
    Handles all of the entity-specific requests.
    """
    def _create_body(self, name, label=None, agent=None, ip_addresses=None,
            metadata=None):
        """
        Used to create the dict required to create various resources. Accepts
        either 'label' or 'name' as the keyword parameter for the label
        attribute for entities.
        """
        label = label or name
        if ip_addresses is not None:
            body = {"label": label}
            if ip_addresses:
                body["ip_addresses"] = ip_addresses
            if agent:
                body["agent_id"] = utils.get_id(agent)
            if metadata:
                body["metadata"] = metadata
        return body


    def update_entity(self, entity, agent=None, metadata=None):
        """
        Updates the specified entity's values with the supplied parameters.
        """
        body = {}
        if agent:
            body["agent_id"] = utils.get_id(agent)
        if metadata:
            body["metadata"] = metadata
        if body:
            uri = "/%s/%s" % (self.uri_base, utils.get_id(entity))
            resp, body = self.api.method_put(uri, body=body)



class CloudMonitorCheck(BaseResource):
    """
    Represents a check defined for an entity.
    """
    def __init__(self, manager, info, entity=None, key=None, loaded=False):
        super(CloudMonitorCheck, self).__init__(manager, info, key=key,
                loaded=loaded)
        self.set_entity(entity)


    def set_entity(self, entity):
        if entity is None:
            # Not yet available
            return
        if not isinstance(entity, CloudMonitorEntity):
            entity = self.manager.get(entity)
        self.entity = entity
        self._metrics_manager = CloudMonitorMetricsManager(self.manager.api,
                uri_base="entities/%s/checks/%s/metrics" % (self.entity.id,
                self.id), resource_class=CloudMonitorMetric, response_key=None,
                plural_response_key=None)


    @property
    def name(self):
        return self.label


    def get(self):
        """Reloads the check with its current values."""
        new = self.manager.get(self)
        if new:
            self._add_details(new._info)

    reload = get


    def update(self, label=None, name=None, disabled=None, metadata=None,
            monitoring_zones_poll=None, timeout=None, period=None,
            target_alias=None, target_hostname=None, target_receiver=None):
        """
        Updates an existing check with any of the parameters.
        """
        self.manager.update(self, label=label, name=name,
                disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)


    def delete(self):
        """Removes this check from its entity."""
        self.manager.delete(self)


    def list_metrics(self, limit=None, marker=None, return_next=False):
        """
        Returns a list of all the metrics associated with this check.
        """
        return self._metrics_manager.list(limit=limit, marker=marker,
                return_next=return_next)


    def get_metric_data_points(self, metric, start, end, points=None,
            resolution=None, stats=None):
        """
        Returns the data points for a given metric for the given period. The
        'start' and 'end' times must be specified; they can be be either Python
        date/datetime values, or a Unix timestamp.

        The 'points' parameter represents the number of points to return. The
        'resolution' parameter represents the granularity of the data. You must
        specify either 'points' or 'resolution'. The allowed values for
        resolution are:
            FULL
            MIN5
            MIN20
            MIN60
            MIN240
            MIN1440

        Finally, the 'stats' parameter specifies the stats you want returned.
        By default only the 'average' is returned. You omit this parameter,
        pass in a single value, or pass in a list of values. The allowed values
        are:
            average
            variance
            min
            max
        """
        return self._metrics_manager.get_metric_data_points(metric, start, end,
                points=points, resolution=resolution, stats=stats)


    def create_alarm(self, notification_plan, criteria=None, disabled=False,
            label=None, name=None, metadata=None):
        """
        Creates an alarm that binds this check with a notification plan.
        """
        return self.manager.create_alarm(self.entity, self, notification_plan,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)



class CloudMonitorCheckType(BaseResource):
    """
    Represents the type of monitor check to be run. Each check type
    """
    @property
    def field_names(self):
        """
        Returns a list of all field names for this check type.
        """
        return [field["name"] for field in self.fields]


    @property
    def required_field_names(self):
        """
        Returns a list of the names of all required fields for this check type.
        """
        return [field["name"] for field in self.fields
                if not field["optional"]]


    @property
    def optional_field_names(self):
        """
        Returns a list of the names of all optional fields for this check type.
        """
        return [field["name"] for field in self.fields
                if field["optional"]]



class CloudMonitorZone(BaseResource):
    """
    Represents a location from which Cloud Monitoring collects data.
    """
    @property
    def name(self):
        return self.label



class CloudMonitorNotification(BaseResource):
    """
    Represents an action to take when an alarm is triggered.
    """
    @property
    def name(self):
        return self.label


    def update(self, details):
        """
        Updates this notification with the supplied details.
        """
        return self.manager.update_notification(self, details)



class CloudMonitorNotificationType(BaseResource):
    """
    Represents a class of action to take when an alarm is triggered.
    """
    @property
    def name(self):
        return self.label



class CloudMonitorNotificationPlan(BaseResource):
    """
    A Notification plan is a list of the notification actions to take when an
    alarm is triggered.
    """
    @property
    def name(self):
        return self.label



class CloudMonitorMetric(BaseResource):
    """
    Metrics represent statistics about the checks defined on an entity.
    """
    pass



class CloudMonitorAlarm(BaseResource):
    """
    Alarms bind alerting rules, entities, and notification plans into a logical
    unit.
    """
    def __init__(self, manager, info, entity, key=None, loaded=False):
        super(CloudMonitorAlarm, self).__init__(manager, info, key=key,
                loaded=loaded)
        if not isinstance(entity, CloudMonitorEntity):
            entity = manager.get(entity)
        self.entity = entity


    def update(self, criteria=None, disabled=False, label=None, name=None,
            metadata=None):
        """
        Updates this alarm.
        """
        return self.entity.update_alarm(self, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)


    def get(self):
        """
        Fetches the current state of the alarm from the API and updates the
        object.
        """
        new_alarm = self.entity.get_alarm(self)
        if new_alarm:
            self._add_details(new_alarm._info)
    # Alias reload() to get()
    reload = get


    @property
    def name(self):
        return self.label



class CloudMonitorClient(BaseClient):
    """
    This is the base client for creating and managing Cloud Monitoring.
    """

    def __init__(self, *args, **kwargs):
        super(CloudMonitorClient, self).__init__(*args, **kwargs)
        self.name = "Cloud Monitoring"


    def _configure_manager(self):
        """
        Creates the Manager instances to handle monitoring.
        """
        self._entity_manager = CloudMonitorEntityManager(self,
                uri_base="entities", resource_class=CloudMonitorEntity,
                response_key=None, plural_response_key=None)
        self._check_type_manager = _PaginationManager(self,
                uri_base="check_types", resource_class=CloudMonitorCheckType,
                response_key=None, plural_response_key=None)
        self._monitoring_zone_manager = BaseManager(self,
                uri_base="monitoring_zones", resource_class=CloudMonitorZone,
                response_key=None, plural_response_key=None)
        self._notification_manager = CloudMonitorNotificationManager(self,
                uri_base="notifications",
                resource_class=CloudMonitorNotification,
                response_key=None, plural_response_key=None)
        self._notification_plan_manager = CloudMonitorNotificationPlanManager(
                self, uri_base="notification_plans",
                resource_class=CloudMonitorNotificationPlan,
                response_key=None, plural_response_key=None)
        self._changelog_manager = _EntityFilteringManger(self,
                uri_base="changelogs/alarms", resource_class=None,
                response_key=None, plural_response_key=None)
        self._overview_manager = _EntityFilteringManger(self,
                uri_base="views/overview", resource_class=None,
                response_key="value", plural_response_key=None)


    def get_account(self):
        """
        Returns a dict with the following keys: id, webhook_token, and metadata.
        """
        resp, resp_body = self.method_get("/account")
        return resp_body


    def get_audits(self):
        """
        Every write operation performed against the API (PUT, POST or DELETE)
        generates an audit record that is stored for 30 days. Audits record a
        variety of information about the request including the method, URL,
        headers, query string, transaction ID, the request body and the
        response code. They also store information about the action performed
        including a JSON list of the previous state of any modified objects.
        For example, if you perform an update on an entity, this will record
        the state of the entity before modification.
        """
        resp, resp_body = self.method_get("/audits")
        return resp_body["values"]


    def list_entities(self, limit=None, marker=None, return_next=False):
        return self._entity_manager.list(limit=limit, marker=marker,
                return_next=return_next)


    def get_entity(self, entity):
        return self._entity_manager.get(entity)


    def create_entity(self, label=None, name=None, agent=None,
            ip_addresses=None, metadata=None):
        # NOTE: passing a non-None value for ip_addresses is required so that
        # the _create_body() method can distinguish this as a request for a
        # body dict for entities.
        ip_addresses = ip_addresses or {}
        resp = self._entity_manager.create(label=label, name=name, agent=agent,
                ip_addresses=ip_addresses, metadata=metadata,
                return_response=True)
        if resp.status_code == 201:
            ent_id = resp.headers["x-object-id"]
            return self.get_entity(ent_id)


    def update_entity(self, entity, agent=None, metadata=None):
        """
        Only the agent_id and metadata are able to be updated via the API.
        """
        self._entity_manager.update_entity(entity, agent=agent,
                metadata=metadata)


    def delete_entity(self, entity):
        """Deletes the specified entity."""
        self._entity_manager.delete(entity)


    def list_check_types(self, limit=None, marker=None, return_next=False):
        return self._check_type_manager.list(limit=limit, marker=marker,
                return_next=return_next)


    def get_check_type(self, check_type):
        return self._check_type_manager.get(check_type)


    @assure_entity
    def list_checks(self, entity, limit=None, marker=None, return_next=False):
        return entity.list_checks(limit=limit, marker=marker,
                return_next=return_next)


    @assure_entity
    def create_check(self, entity, label=None, name=None, check_type=None,
            disabled=False, metadata=None, details=None,
            monitoring_zones_poll=None, timeout=None, period=None,
            target_alias=None, target_hostname=None, target_receiver=None,
            test_only=False, include_debug=False):
        """
        Creates a check on the entity with the specified attributes. The
        'details' parameter should be a dict with the keys as the option name,
        and the value as the desired setting.
        """
        return entity.create_check(label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)


    @assure_entity
    def get_check(self, entity, check):
        """Returns the current check for the given entity."""
        return entity.get_check(check)


    @assure_entity
    def find_all_checks(self, entity, **kwargs):
        """
        Finds all checks for a given entity with attributes matching
        ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return entity.find_all_checks(**kwargs)


    @assure_entity
    def update_check(self, entity, check, label=None, name=None, disabled=None,
            metadata=None, monitoring_zones_poll=None, timeout=None,
            period=None, target_alias=None, target_hostname=None,
            target_receiver=None):
        """
        Updates an existing check with any of the parameters.
        """
        entity.update_check(check, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)


    @assure_entity
    def delete_check(self, entity, check):
        """
        Deletes the specified check from the entity.
        """
        return entity.delete_check(check)


    @assure_entity
    def list_metrics(self, entity, check, limit=None, marker=None,
            return_next=False):
        """
        Returns a list of all the metrics associated with the specified check.
        """
        return entity.list_metrics(check, limit=limit, marker=marker,
                return_next=return_next)


    @assure_entity
    def get_metric_data_points(self, entity, check, metric, start, end,
            points=None, resolution=None, stats=None):
        """
        Returns the data points for a given metric for the given period. The
        'start' and 'end' times must be specified; they can be be either Python
        date/datetime values, or a Unix timestamp.

        The 'points' parameter represents the number of points to return. The
        'resolution' parameter represents the granularity of the data. You must
        specify either 'points' or 'resolution'. The allowed values for
        resolution are:
            FULL
            MIN5
            MIN20
            MIN60
            MIN240
            MIN1440

        Finally, the 'stats' parameter specifies the stats you want returned.
        By default only the 'average' is returned. You omit this parameter,
        pass in a single value, or pass in a list of values. The allowed values
        are:
            average
            variance
            min
            max
        """
        return entity.get_metric_data_points(check, metric, start, end,
                points=points, resolution=resolution, stats=stats)


    def list_notifications(self):
        """Returns a list of all defined notifications."""
        return self._notification_manager.list()


    def get_notification(self, notification_id):
        """
        Returns the CloudMonitorNotification object for the specified ID.
        """
        return self._notification_manager.get(notification_id)


    def test_notification(self, notification=None, notification_type=None,
            details=None):
        """
        This allows you to test either an existing notification, or a potential
        notification before creating it. The actual notification comes from the
        same server where the actual alert messages come from. This allow you
        to, among other things, verify that your firewall is configured
        properly.

        To test an existing notification, pass it as the 'notification'
        parameter and leave the other parameters empty. To pre-test a
        notification before creating it, leave 'notification' empty, but pass
        in the 'notification_type' and 'details'.
        """
        return self._notification_manager.test_notification(
                notification=notification, notification_type=notification_type,
                details=details)


    def create_notification(self, notification_type, label=None, name=None,
            details=None):
        """
        Defines a notification for handling an alarm.
        """
        return self._notification_manager.create(notification_type,
                label=label, name=name, details=details)


    def update_notification(self, notification, details):
        """
        Updates the specified notification with the supplied details.
        """
        return self._notification_manager.update_notification(notification,
                details)


    def delete_notification(self, notification):
        """
        Deletes the specified notification.
        """
        return self._notification_manager.delete(notification)


    def create_notification_plan(self, label=None, name=None,
            critical_state=None, ok_state=None, warning_state=None):
        """
        Creates a notification plan to be executed when a monitoring check
        triggers an alarm.
        """
        return self._notification_plan_manager.create(label=label, name=name,
                critical_state=critical_state, ok_state=ok_state,
                warning_state=warning_state)


    def list_notification_plans(self):
        """
        Returns a list of all defined notification plans.
        """
        return self._notification_plan_manager.list()


    def get_notification_plan(self, notification_plan_id):
        """
        Returns the CloudMonitorNotificationPlan object for the specified ID.
        """
        return self._notification_plan_manager.get(notification_plan_id)


    def delete_notification_plan(self, notification_plan):
        """
        Deletes the specified notification plan.
        """
        return self._notification_plan_manager.delete(notification_plan)

    @assure_entity
    def create_alarm(self, entity, check, notification_plan, criteria=None,
            disabled=False, label=None, name=None, metadata=None):
        """
        Creates an alarm that binds the check on the given entity with a
        notification plan.
        """
        return entity.create_alarm(check, notification_plan, criteria=criteria,
            disabled=disabled, label=label, name=name, metadata=metadata)

    @assure_entity
    def update_alarm(self, entity, alarm, criteria=None, disabled=False,
            label=None, name=None, metadata=None):
        """
        Updates an existing alarm on the given entity.
        """
        return entity.update_alarm(alarm, criteria=criteria, disabled=disabled,
            label=label, name=name, metadata=metadata)


    @assure_entity
    def list_alarms(self, entity, limit=None, marker=None, return_next=False):
        """
        Returns a list of all the alarms created on the specified entity.
        """
        return entity.list_alarms(limit=limit, marker=marker,
                return_next=return_next)


    @assure_entity
    def get_alarm(self, entity, alarm_id):
        """
        Returns the alarm with the specified ID for the entity.
        """
        return entity.get_alarm(alarm_id)


    @assure_entity
    def delete_alarm(self, entity, alarm):
        """
        Deletes the specified alarm.
        """
        return entity.delete_alarm(alarm)


    def list_notification_types(self):
        return self._notification_manager.list_types()


    def get_notification_type(self, nt_id):
        return self._notification_manager.get_type(nt_id)


    def list_monitoring_zones(self):
        """
        Returns a list of all available monitoring zones.
        """
        return self._monitoring_zone_manager.list()


    def get_monitoring_zone(self, mz_id):
        """
        Returns the monitoring zone for the given ID.
        """
        return self._monitoring_zone_manager.get(mz_id)


    def get_changelogs(self, entity=None):
        """
        Returns a dictionary containing the changelogs. The monitoring service
        records changelogs for alarm statuses.

        You may supply an entity to filter the results to show only the alarms
        for the specified entity.
        """
        return self._changelog_manager.list(entity=entity)


    def get_overview(self, entity=None):
        """
        Returns a dictionary containing the overview information.

        Views contain a combination of data that usually includes multiple,
        different objects. The primary purpose of a view is to save API calls
        and make data retrieval more efficient. Instead of doing multiple API
        calls and then combining the result yourself, you can perform a single
        API call against the view endpoint.

        You may supply an entity to filter the results to show only the data
        for the specified entity.
        """
        return self._overview_manager.list(entity=entity)


    #################################################################
    # The following methods are defined in the generic client class,
    # but don't have meaning in monitoring, as there is not a single
    # resource that defines this module.
    #################################################################
    def list(self, limit=None, marker=None):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def get(self, item):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def delete(self, item):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def find(self, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def findall(self, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError
    #################################################################
