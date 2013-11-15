#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Rackspace

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

import pyrax
from pyrax.client import BaseClient
from pyrax.cloudloadbalancers import CloudLoadBalancer
from pyrax.cloudnetworks import SERVICE_NET_ID
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils



class ScalingGroup(BaseResource):
    def __init__(self, *args, **kwargs):
        super(ScalingGroup, self).__init__(*args, **kwargs)
        self._non_display = ["active", "launchConfiguration", "links",
        "groupConfiguration", "policies", "scalingPolicies"]
        self._repr_properties = ["name", "cooldown", "metadata",
        "min_entities", "max_entities"]
        self._make_policies()


    def _make_policies(self):
        """
        Convert the 'scalingPolicies' dictionary into AutoScalePolicy objects.
        """
        self.policies = [AutoScalePolicy(self.manager, dct, self)
                for dct in self.scalingPolicies]


    def get_state(self):
        """
        Returns the current state of this scaling group.
        """
        return self.manager.get_state(self)


    def pause(self):
        """
        Pauses all execution of the policies for this scaling group.
        """
        return self.manager.pause(self)


    def resume(self):
        """
        Resumes execution of the policies for this scaling group.
        """
        return self.manager.resume(self)


    def update(self, name=None, cooldown=None, min_entities=None,
            max_entities=None, metadata=None):
        """
        Updates this ScalingGroup. One or more of the attributes can be
        specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_metadata() method.
        """
        return self.manager.update(self, name=name,
                cooldown=cooldown, min_entities=min_entities,
                max_entities=max_entities, metadata=metadata)


    def update_metadata(self, metadata):
        """
        Adds the given metadata dict to the existing metadata for this scaling
        group.
        """
        return self.manager.update_metadata(self, metadata=metadata)


    def get_configuration(self):
        """
        Returns the scaling group configuration in a dictionary.
        """
        return self.manager.get_configuration(self)


    def get_launch_config(self):
        """
        Returns the launch configuration for this scaling group.
        """
        return self.manager.get_launch_config(self)


    def update_launch_config(self, server_name=None, image=None, flavor=None,
            disk_config=None, metadata=None, personality=None, networks=None,
            load_balancers=None, key_name=None):
        """
        Updates the server launch configuration for this scaling group.
        One or more of the available attributes can be specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_launch_metadata() method.
        """
        return self.manager.update_launch_config(self, server_name=server_name,
                image=image, flavor=flavor, disk_config=disk_config,
                metadata=metadata, personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)


    def update_launch_metadata(self, metadata):
        """
        Adds the given metadata dict to the existing metadata for this scaling
        group's launch configuration.
        """
        return self.manager.update_launch_metadata(self, metadata)


    def add_policy(self, name, policy_type, cooldown, change=None,
            is_percent=False, desired_capacity=None, args=None):
        """
        Adds a policy with the given values to this scaling group. The
        'change' parameter is treated as an absolute amount, unless
        'is_percent' is True, in which case it is treated as a percentage.
        """
        return self.manager.add_policy(self, name, policy_type, cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)


    def list_policies(self):
        """
        Returns a list of all policies defined for this scaling group.
        """
        return self.manager.list_policies(self)


    def get_policy(self, policy):
        """
        Gets the detail for the specified policy.
        """
        return self.manager.get_policy(self, policy)


    def update_policy(self, policy, name=None, policy_type=None, cooldown=None,
            change=None, is_percent=False, desired_capacity=None, args=None):
        """
        Updates the specified policy. One or more of the parameters may be
        specified.
        """
        return self.manager.update_policy(scaling_group=self, policy=policy,
                name=name, policy_type=policy_type, cooldown=cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)


    def execute_policy(self, policy):
        """
        Executes the specified policy for this scaling group.
        """
        return self.manager.execute_policy(scaling_group=self, policy=policy)


    def delete_policy(self, policy):
        """
        Deletes the specified policy from this scaling group.
        """
        return self.manager.delete_policy(scaling_group=self, policy=policy)


    def add_webhook(self, policy, name, metadata=None):
        """
        Adds a webhook to the specified policy.
        """
        return self.manager.add_webhook(self, policy, name, metadata=metadata)


    def list_webhooks(self, policy):
        """
        Returns a list of all webhooks for the specified policy.
        """
        return self.manager.list_webhooks(self, policy)


    def update_webhook(self, policy, webhook, name=None, metadata=None):
        """
        Updates the specified webhook. One or more of the parameters may be
        specified.
        """
        return self.manager.update_webhook(scaling_group=self, policy=policy,
                webhook=webhook, name=name, metadata=metadata)


    def update_webhook_metadata(self, policy, webhook, metadata):
        """
        Adds the given metadata dict to the existing metadata for the specified
        webhook.
        """
        return self.manager.update_webhook_metadata(self, policy, webhook,
                metadata)


    def delete_webhook(self, policy, webhook):
        """
        Deletes the specified webhook from the specified policy.
        """
        return self.manager.delete_webhook(self, policy, webhook)


    @property
    def policy_count(self):
        return len(self.policies)


    ##################################################################
    # The following property declarations allow access to the base attributes
    # of the ScalingGroup held in the 'groupConfiguration' dict as if they
    # were native attributes.
    ##################################################################
    @property
    def name(self):
        return self.groupConfiguration.get("name")

    @name.setter
    def name(self, val):
        self.groupConfiguration["name"] = val

    @property
    def cooldown(self):
        return self.groupConfiguration.get("cooldown")

    @cooldown.setter
    def cooldown(self, val):
        self.groupConfiguration["cooldown"] = val


    @property
    def metadata(self):
        return self.groupConfiguration.get("metadata")

    @metadata.setter
    def metadata(self, val):
        self.groupConfiguration["metadata"] = val


    @property
    def min_entities(self):
        return self.groupConfiguration.get("minEntities")

    @min_entities.setter
    def min_entities(self, val):
        self.groupConfiguration["minEntities"] = val


    @property
    def max_entities(self):
        return self.groupConfiguration.get("maxEntities")

    @max_entities.setter
    def max_entities(self, val):
        self.groupConfiguration["maxEntities"] = val
    ##################################################################



class ScalingGroupManager(BaseManager):
    def __init__(self, api, resource_class=None, response_key=None,
            plural_response_key=None, uri_base=None):
        super(ScalingGroupManager, self).__init__(api,
                resource_class=resource_class, response_key=response_key,
                plural_response_key=plural_response_key, uri_base=uri_base)


    def get_state(self, scaling_group):
        """
        Returns the current state of the specified scaling group as a
        dictionary.
        """
        uri = "/%s/%s/state" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_get(uri)
        data = resp_body["group"]
        ret = {}
        ret["active"] = [itm["id"] for itm in data["active"]]
        ret["active_capacity"] = data["activeCapacity"]
        ret["desired_capacity"] = data["desiredCapacity"]
        ret["pending_capacity"] = data["pendingCapacity"]
        ret["paused"] = data["paused"]
        return ret


    def pause(self, scaling_group):
        """
        Pauses all execution of the policies for the specified scaling group.
        """
        uri = "/%s/%s/pause" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_post(uri)
        return None


    def resume(self, scaling_group):
        """
        Resumes execution of the policies for the specified scaling group.
        """
        uri = "/%s/%s/resume" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_post(uri)
        return None


    def get_configuration(self, scaling_group):
        """
        Returns the scaling group's configuration in a dictionary.
        """
        uri = "/%s/%s/config" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_get(uri)
        return resp_body.get("groupConfiguration")


    def replace(self, scaling_group, name, cooldown, min_entities,
            max_entities, metadata=None):
        """
        Replace an existing ScalingGroup configuration. All of the attributes
        must be specified If you wish to delete any of the optional attributes,
        pass them in as None.
        """
        body = self._create_group_config_body(name, cooldown, min_entities,
                max_entities, metadata=metadata)
        group_id = utils.get_id(scaling_group)
        uri = "/%s/%s/config" % (self.uri_base, group_id)
        resp, resp_body = self.api.method_put(uri, body=body)


    def update(self, scaling_group, name=None, cooldown=None,
            min_entities=None, max_entities=None, metadata=None):
        """
        Updates an existing ScalingGroup. One or more of the attributes can
        be specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_metadata() method.
        """
        if not isinstance(scaling_group, ScalingGroup):
            scaling_group = self.get(scaling_group)
        uri = "/%s/%s/config" % (self.uri_base, scaling_group.id)
        if cooldown is None:
            cooldown = scaling_group.cooldown
        if min_entities is None:
            min_entities = scaling_group.min_entities
        if max_entities is None:
            max_entities = scaling_group.max_entities
        body = {"name": name or scaling_group.name,
                "cooldown": cooldown,
                "minEntities": min_entities,
                "maxEntities": max_entities,
                "metadata": metadata or scaling_group.metadata,
                }
        resp, resp_body = self.api.method_put(uri, body=body)
        return None


    def update_metadata(self, scaling_group, metadata):
        """
        Adds the given metadata dict to the existing metadata for the scaling
        group.
        """
        if not isinstance(scaling_group, ScalingGroup):
            scaling_group = self.get(scaling_group)
        curr_meta = scaling_group.metadata
        curr_meta.update(metadata)
        return self.update(scaling_group, metadata=curr_meta)


    def get_launch_config(self, scaling_group):
        """
        Returns the launch configuration for the specified scaling group.
        """
        uri = "/%s/%s/launch" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_get(uri)
        ret = {}
        data = resp_body.get("launchConfiguration")
        ret["type"] = data.get("type")
        args = data.get("args", {})
        ret["load_balancers"] = args.get("loadBalancers")
        srv = args.get("server", {})
        ret["name"] = srv.get("name")
        ret["flavor"] = srv.get("flavorRef")
        ret["image"] = srv.get("imageRef")
        ret["disk_config"] = srv.get("OS-DCF:diskConfig")
        ret["metadata"] = srv.get("metadata")
        ret["personality"] = srv.get("personality")
        ret["networks"] = srv.get("networks")
        ret["key_name"] = srv.get("key_name")
        return ret


    def replace_launch_config(self, scaling_group, launch_config_type,
            server_name, image, flavor, disk_config=None, metadata=None,
            personality=None, networks=None, load_balancers=None,
            key_name=None):
        """
        Replace an existing launch configuration. All of the attributes must be
        specified. If you wish to delete any of the optional attributes, pass
        them in as None.
        """
        group_id = utils.get_id(scaling_group)
        uri = "/%s/%s/launch" % (self.uri_base, group_id)
        body = self._create_launch_config_body(
                launch_config_type=launch_config_type, server_name=server_name,
                image=image, flavor=flavor, disk_config=disk_config,
                metadata=metadata, personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)
        resp, resp_body = self.api.method_put(uri, body=body)


    def update_launch_config(self, scaling_group, server_name=None, image=None,
            flavor=None, disk_config=None, metadata=None, personality=None,
            networks=None, load_balancers=None, key_name=None):
        """
        Updates the server launch configuration for an existing scaling group.
        One or more of the available attributes can be specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_launch_metadata() method.
        """
        if not isinstance(scaling_group, ScalingGroup):
            scaling_group = self.get(scaling_group)
        uri = "/%s/%s/launch" % (self.uri_base, scaling_group.id)
        largs = scaling_group.launchConfiguration.get("args", {})
        srv_args = largs.get("server", {})
        lb_args = largs.get("loadBalancers", {})
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": server_name or srv_args.get("name"),
                        "imageRef": image or srv_args.get("imageRef"),
                        "flavorRef": "%s" % flavor or srv_args.get("flavorRef"),
                        "OS-DCF:diskConfig": disk_config or
                                srv_args.get("OS-DCF:diskConfig"),
                        "personality": personality or
                                srv_args.get("personality"),
                        "networks": networks or srv_args.get("networks"),
                        "metadata": metadata or srv_args.get("metadata"),
                    },
                    "loadBalancers": load_balancers or lb_args,
                },
            }
        key_name = key_name or srv_args.get("key_name")
        if key_name:
            body["args"]["server"] = key_name
        resp, resp_body = self.api.method_put(uri, body=body)
        return None


    def update_launch_metadata(self, scaling_group, metadata):
        """
        Adds the given metadata dict to the existing metadata for the scaling
        group's launch configuration.
        """
        if not isinstance(scaling_group, ScalingGroup):
            scaling_group = self.get(scaling_group)
        curr_meta = scaling_group.launchConfiguration.get("args", {}).get(
                "server", {}).get("metadata", {})
        curr_meta.update(metadata)
        return self.update_launch_config(scaling_group, metadata=curr_meta)


    def add_policy(self, scaling_group, name, policy_type, cooldown,
            change=None, is_percent=False, desired_capacity=None, args=None):
        """
        Adds a policy with the given values to the specified scaling group. The
        'change' parameter is treated as an absolute amount, unless
        'is_percent' is True, in which case it is treated as a percentage.
        """
        uri = "/%s/%s/policies" % (self.uri_base, utils.get_id(scaling_group))
        body = self._create_policy_body(name, policy_type, cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)
        # "body" needs to be a list
        body = [body]
        resp, resp_body = self.api.method_post(uri, body=body)
        pol_info = resp_body.get("policies")[0]
        return AutoScalePolicy(self, pol_info, scaling_group)


    def _create_policy_body(self, name, policy_type, cooldown, change=None,
            is_percent=None, desired_capacity=None, args=None):
        body = {"name": name, "cooldown": cooldown, "type": policy_type}
        if change is not None:
            if is_percent:
                body["changePercent"] = change
            else:
                body["change"] = change
        if desired_capacity is not None:
            body["desiredCapacity"] = desired_capacity
        if args is not None:
            body["args"] = args
        return body


    def list_policies(self, scaling_group):
        """
        Returns a list of all policies defined for the specified scaling group.
        """
        uri = "/%s/%s/policies" % (self.uri_base, utils.get_id(scaling_group))
        resp, resp_body = self.api.method_get(uri)
        return [AutoScalePolicy(self, data, scaling_group)
                for data in resp_body.get("policies", [])]


    def get_policy(self, scaling_group, policy):
        """
        Gets the detail for the specified policy.
        """
        uri = "/%s/%s/policies/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        resp, resp_body = self.api.method_get(uri)
        data = resp_body.get("policy")
        return AutoScalePolicy(self, data, scaling_group)


    def replace_policy(self, scaling_group, policy, name,
            policy_type, cooldown, change=None, is_percent=False,
            desired_capacity=None, args=None):
        """
        Replace an existing policy. All of the attributes must be specified. If
        you wish to delete any of the optional attributes, pass them in as
        None.
        """
        policy_id = utils.get_id(policy)
        group_id = utils.get_id(scaling_group)
        uri = "/%s/%s/policies/%s" % (self.uri_base, group_id, policy_id)
        body = self._create_policy_body(name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)
        resp, resp_body = self.api.method_put(uri, body=body)


    def update_policy(self, scaling_group, policy, name=None, policy_type=None,
            cooldown=None, change=None, is_percent=False,
            desired_capacity=None, args=None):
        """
        Updates the specified policy. One or more of the parameters may be
        specified.
        """
        uri = "/%s/%s/policies/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        if not isinstance(policy, AutoScalePolicy):
            # Received an ID
            policy = self.get_policy(scaling_group, policy)
        body = {"name": name or policy.name,
                "type": policy_type or policy.type,
                "cooldown": cooldown or policy.cooldown,
                }
        if desired_capacity is not None or change is not None:
            if desired_capacity is not None:
                body["desiredCapacity"] = desired_capacity
            elif change is not None:
                if is_percent:
                    body["changePercent"] = change
                else:
                    body["change"] = change
        else:
            if getattr(policy, 'changePercent', None) is not None:
                body["changePercent"] = policy.changePercent
            elif getattr(policy, 'change', None) is not None:
                body["change"] = policy.change
            elif getattr(policy, 'desiredCapacity', None) is not None:
                body["desiredCapacity"] = policy.desiredCapacity
        args = args or getattr(policy, 'args', None)
        if args is not None:
            body["args"] = args
        resp, resp_body = self.api.method_put(uri, body=body)
        return None


    def execute_policy(self, scaling_group, policy):
        """
        Executes the specified policy for this scaling group.
        """
        uri = "/%s/%s/policies/%s/execute" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        resp, resp_body = self.api.method_post(uri)
        return None


    def delete_policy(self, scaling_group, policy):
        """
        Deletes the specified policy from the scaling group.
        """
        uri = "/%s/%s/policies/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        resp, resp_body = self.api.method_delete(uri)

    def _create_webhook_body(self, name, metadata=None):
        if metadata is None:
            # If updating a group with existing metadata, metadata MUST be
            # passed. Leaving it out causes Otter to return 400.
            metadata = {}
        body = {"name": name, "metadata": metadata}
        return body

    def add_webhook(self, scaling_group, policy, name, metadata=None):
        """
        Adds a webhook to the specified policy.
        """
        uri = "/%s/%s/policies/%s/webhooks" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        body = self._create_webhook_body(name, metadata=metadata)
        # "body" needs to be a list
        body = [body]
        resp, resp_body = self.api.method_post(uri, body=body)
        data = resp_body.get("webhooks")[0]
        return AutoScaleWebhook(self, data, policy, scaling_group)


    def list_webhooks(self, scaling_group, policy):
        """
        Returns a list of all webhooks for the specified policy.
        """
        uri = "/%s/%s/policies/%s/webhooks" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy))
        resp, resp_body = self.api.method_get(uri)
        return [AutoScaleWebhook(self, data, policy, scaling_group)
                for data in resp_body.get("webhooks", [])]


    def get_webhook(self, scaling_group, policy, webhook):
        """
        Gets the detail for the specified webhook.
        """
        uri = "/%s/%s/policies/%s/webhooks/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy),
                utils.get_id(webhook))
        resp, resp_body = self.api.method_get(uri)
        data = resp_body.get("webhook")
        return AutoScaleWebhook(self, data, policy, scaling_group)


    def replace_webhook(self, scaling_group, policy, webhook, name,
            metadata=None):
        """
        Replace an existing webhook. All of the attributes must be specified.
        If you wish to delete any of the optional attributes, pass them in as
        None.
        """
        uri = "/%s/%s/policies/%s/webhooks/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy),
                utils.get_id(webhook))
        group_id = utils.get_id(scaling_group)
        policy_id = utils.get_id(policy)
        webhook_id = utils.get_id(webhook)
        body = self._create_webhook_body(name, metadata=metadata)
        resp, resp_body = self.api.method_put(uri, body=body)


    def update_webhook(self, scaling_group, policy, webhook, name=None,
            metadata=None):
        """
        Updates the specified webhook. One or more of the parameters may be
        specified.
        """
        uri = "/%s/%s/policies/%s/webhooks/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy),
                utils.get_id(webhook))
        if not isinstance(webhook, AutoScaleWebhook):
            # Received an ID
            webhook = self.get_webhook(scaling_group, policy, webhook)
        body = {"name": name or webhook.name,
                "metadata": metadata or webhook.metadata,
                }
        resp, resp_body = self.api.method_put(uri, body=body)
        webhook.reload()
        return webhook


    def update_webhook_metadata(self, scaling_group, policy, webhook, metadata):
        """
        Adds the given metadata dict to the existing metadata for the specified
        webhook.
        """
        if not isinstance(webhook, AutoScaleWebhook):
            webhook = self.get_webhook(scaling_group, policy, webhook)
        curr_meta = webhook.metadata or {}
        curr_meta.update(metadata)
        return self.update_webhook(scaling_group, policy, webhook,
                metadata=curr_meta)


    def delete_webhook(self, scaling_group, policy, webhook):
        """
        Deletes the specified webhook from the specified policy.
        """
        uri = "/%s/%s/policies/%s/webhooks/%s" % (self.uri_base,
                utils.get_id(scaling_group), utils.get_id(policy),
                utils.get_id(webhook))
        resp, resp_body = self.api.method_delete(uri)
        return None


    @staticmethod
    def _resolve_lbs(load_balancers):
        """
        Takes either a single LB reference or a list of references and returns
        the dictionary required for creating a Scaling Group.

        References can be either a dict that matches the structure required by
        the autoscale API, a CloudLoadBalancer instance, or the ID of the load
        balancer.
        """
        lb_args = []
        lbs = utils.coerce_string_to_list(load_balancers)
        for lb in lbs:
            if isinstance(lb, dict):
                lb_args.append(lb)
            elif isinstance(lb, CloudLoadBalancer):
                lb_args.append({
                        "loadBalancerId": lb.id,
                        "port": lb.port,
                        })
            else:
                # See if it's an ID for a Load Balancer
                try:
                    instance = pyrax.cloud_loadbalancers.get(lb)
                except Exception:
                    raise exc.InvalidLoadBalancer("Received an invalid "
                            "specification for a Load Balancer: '%s'" % lb)
                lb_args.append({
                        "loadBalancerId": instance.id,
                        "port": instance.port,
                        })
        return lb_args


    def _create_body(self, name, cooldown, min_entities, max_entities,
            launch_config_type, server_name, image, flavor, disk_config=None,
            metadata=None, personality=None, networks=None,
            load_balancers=None, scaling_policies=None, group_metadata=None,
            key_name=None):
        """
        Used to create the dict required to create any of the following:
            A Scaling Group
        """
        if disk_config is None:
            disk_config = "AUTO"
        if metadata is None:
            metadata = {}
        if personality is None:
            personality = []
        if networks is None:
            # Default to ServiceNet only
            networks = [{"uuid": SERVICE_NET_ID}]
        if scaling_policies is None:
            scaling_policies = []
        group_config = self._create_group_config_body(name, cooldown,
                min_entities, max_entities, metadata=group_metadata)
        launch_config = self._create_launch_config_body(launch_config_type,
                server_name, image, flavor, disk_config=disk_config,
                metadata=metadata, personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)
        body = {
                "groupConfiguration": group_config,
                "launchConfiguration": launch_config,
                "scalingPolicies": scaling_policies,
                }
        return body


    def _create_group_config_body(self, name, cooldown, min_entities,
            max_entities, metadata=None):
        if metadata is None:
            # If updating a group with existing metadata, metadata MUST be
            # passed. Leaving it out causes Otter to return 400.
            metadata = {}
        body = {
                "name": name,
                "cooldown": cooldown,
                "minEntities": min_entities,
                "maxEntities": max_entities,
                "metadata": metadata,
                }
        return body


    def _create_launch_config_body(self, launch_config_type,
            server_name, image, flavor, disk_config=None, metadata=None,
            personality=None, networks=None, load_balancers=None,
            key_name=None):
        server_args = {
                "flavorRef": "%s" % flavor,
                "name": server_name,
                "imageRef": utils.get_id(image),
                }
        if metadata is not None:
            server_args["metadata"] = metadata
        if personality is not None:
            server_args["personality"] = personality
        if networks is not None:
            server_args["networks"] = networks
        if disk_config is not None:
            server_args["OS-DCF:diskConfig"] = disk_config
        if key_name is not None:
            server_args["key_name"] = key_name
        if load_balancers is None:
            load_balancers = []
        load_balancer_args = self._resolve_lbs(load_balancers)
        return {"type": launch_config_type,
                "args": {"server": server_args,
                         "loadBalancers": load_balancer_args}}



class AutoScalePolicy(BaseResource):
    def __init__(self, manager, info, scaling_group, *args, **kwargs):
        super(AutoScalePolicy, self).__init__(manager, info, *args, **kwargs)
        if not isinstance(scaling_group, ScalingGroup):
            scaling_group = manager.get(scaling_group)
        self.scaling_group = scaling_group
        self._non_display = ["links", "scaling_group"]


    def get(self):
        """
        Gets the details for this policy.
        """
        return self.manager.get_policy(self.scaling_group, self)
    reload = get


    def delete(self):
        """
        Deletes this policy.
        """
        return self.manager.delete_policy(self.scaling_group, self)


    def update(self, name=None, policy_type=None, cooldown=None, change=None,
            is_percent=False, desired_capacity=None, args=None):
        """
        Updates this policy. One or more of the parameters may be
        specified.
        """
        return self.manager.update_policy(scaling_group=self.scaling_group,
                policy=self, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)


    def execute(self):
        """
        Executes this policy.
        """
        return self.manager.execute_policy(self.scaling_group, self)


    def add_webhook(self, name, metadata=None):
        """
        Adds a webhook to this policy.
        """
        return self.manager.add_webhook(self.scaling_group, self, name,
                metadata=metadata)


    def list_webhooks(self):
        """
        Returns a list of all webhooks for this policy.
        """
        return self.manager.list_webhooks(self.scaling_group, self)


    def get_webhook(self, webhook):
        """
        Gets the detail for the specified webhook.
        """
        return self.manager.get_webhook(self.scaling_group, self, webhook)


    def update_webhook(self, webhook, name=None, metadata=None):
        """
        Updates the specified webhook. One or more of the parameters may be
        specified.
        """
        return self.manager.update_webhook(self.scaling_group, policy=self,
                webhook=webhook, name=name, metadata=metadata)


    def update_webhook_metadata(self, webhook, metadata):
        """
        Adds the given metadata dict to the existing metadata for the specified
        webhook.
        """
        return self.manager.update_webhook_metadata(self.scaling_group, self,
                webhook, metadata)


    def delete_webhook(self, webhook):
        """
        Deletes the specified webhook from this policy.
        """
        return self.manager.delete_webhook(self.scaling_group, self, webhook)



class AutoScaleWebhook(BaseResource):
    def __init__(self, manager, info, policy, scaling_group, *args, **kwargs):
        super(AutoScaleWebhook, self).__init__(manager, info, *args, **kwargs)
        if not isinstance(policy, AutoScalePolicy):
            policy = manager.get_policy(scaling_group, policy)
        self.policy = policy
        self._non_display = ["links", "policy"]


    def get(self):
        return self.policy.get_webhook(self)
    reload = get


    def update(self, name=None, metadata=None):
        """
        Updates this webhook. One or more of the parameters may be specified.
        """
        return self.policy.update_webhook(self, name=name, metadata=metadata)


    def update_metadata(self, metadata):
        """
        Adds the given metadata dict to the existing metadata for this webhook.
        """
        return self.policy.update_webhook_metadata(self, metadata)


    def delete(self):
        """
        Deletes this webhook.
        """
        return self.policy.delete_webhook(self)



class AutoScaleClient(BaseClient):
    """
    This is the primary class for interacting with AutoScale.
    """
    name = "Autoscale"

    def _configure_manager(self):
        """
        Creates a manager to handle autoscale operations.
        """
        self._manager = ScalingGroupManager(self,
                resource_class=ScalingGroup, response_key="group",
                uri_base="groups")


    def get_state(self, scaling_group):
        """
        Returns the current state of the specified scaling group.
        """
        return self._manager.get_state(scaling_group)


    def pause(self, scaling_group):
        """
        Pauses all execution of the policies for the specified scaling group.
        """
        #NOTE: This is not yet implemented. The code is based on the docs,
        # so it should either work or be pretty close.
        return self._manager.pause(scaling_group)


    def resume(self, scaling_group):
        """
        Resumes execution of the policies for the specified scaling group.
        """
        #NOTE: This is not yet implemented. The code is based on the docs,
        # so it should either work or be pretty close.
        return self._manager.resume(scaling_group)


    def replace(self, scaling_group, name, cooldown, min_entities,
            max_entities, metadata=None):
        """
        Replace an existing ScalingGroup configuration. All of the attributes
        must be specified. If you wish to delete any of the optional
        attributes, pass them in as None.
        """
        return self._manager.replace(scaling_group, name, cooldown,
                min_entities, max_entities, metadata=metadata)


    def update(self, scaling_group, name=None, cooldown=None, min_entities=None,
            max_entities=None, metadata=None):
        """
        Updates an existing ScalingGroup. One or more of the attributes can be
        specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_metadata() method.
        """
        return self._manager.update(scaling_group, name=name, cooldown=cooldown,
                min_entities=min_entities, max_entities=max_entities,
                metadata=metadata)


    def update_metadata(self, scaling_group, metadata):
        """
        Adds the given metadata dict to the existing metadata for the scaling
        group.
        """
        return self._manager.update_metadata(scaling_group, metadata)


    def get_configuration(self, scaling_group):
        """
        Returns the scaling group's configuration in a dictionary.
        """
        return self._manager.get_configuration(scaling_group)


    def get_launch_config(self, scaling_group):
        """
        Returns the launch configuration for the specified scaling group.
        """
        return self._manager.get_launch_config(scaling_group)


    def replace_launch_config(self, scaling_group, launch_config_type,
            server_name, image, flavor, disk_config=None, metadata=None,
            personality=None, networks=None, load_balancers=None,
            key_name=None):
        """
        Replace an existing launch configuration. All of the attributes must be
        specified. If you wish to delete any of the optional attributes, pass
        them in as None.
        """
        return self._manager.replace_launch_config(scaling_group,
                launch_config_type, server_name, image, flavor,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)


    def update_launch_config(self, scaling_group, server_name=None, image=None,
            flavor=None, disk_config=None, metadata=None, personality=None,
            networks=None, load_balancers=None, key_name=None):
        """
        Updates the server launch configuration for an existing scaling group.
        One or more of the available attributes can be specified.

        NOTE: if you specify metadata, it will *replace* any existing metadata.
        If you want to add to it, you either need to pass the complete dict of
        metadata, or call the update_launch_metadata() method.
        """
        return self._manager.update_launch_config(scaling_group,
                server_name=server_name, image=image, flavor=flavor,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)


    def update_launch_metadata(self, scaling_group, metadata):
        """
        Adds the given metadata dict to the existing metadata for the scaling
        group's launch configuration.
        """
        return self._manager.update_launch_metadata(scaling_group, metadata)


    def add_policy(self, scaling_group, name, policy_type, cooldown,
            change=None, is_percent=False, desired_capacity=None, args=None):
        """
        Adds a policy with the given values to the specified scaling group. The
        'change' parameter is treated as an absolute amount, unless
        'is_percent' is True, in which case it is treated as a percentage.
        """
        return self._manager.add_policy(scaling_group, name, policy_type,
                cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)


    def list_policies(self, scaling_group):
        """
        Returns a list of all policies defined for the specified scaling group.
        """
        return self._manager.list_policies(scaling_group)


    def get_policy(self, scaling_group, policy):
        """
        Gets the detail for the specified policy.
        """
        return self._manager.get_policy(scaling_group, policy)


    def replace_policy(self, scaling_group, policy, name,
            policy_type, cooldown, change=None, is_percent=False,
            desired_capacity=None, args=None):
        """
        Replace an existing policy. All of the attributes must be specified. If
        you wish to delete any of the optional attributes, pass them in as
        None.
        """
        return self._manager.replace_policy(scaling_group, policy, name,
                policy_type, cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)


    def update_policy(self, scaling_group, policy, name=None, policy_type=None,
            cooldown=None, change=None, is_percent=False,
            desired_capacity=None, args=None):
        """
        Updates the specified policy. One or more of the parameters may be
        specified.
        """
        return self._manager.update_policy(scaling_group, policy, name=name,
                policy_type=policy_type, cooldown=cooldown, change=change,
                is_percent=is_percent, desired_capacity=desired_capacity,
                args=args)


    def execute_policy(self, scaling_group, policy):
        """
        Executes the specified policy for the scaling group.
        """
        return self._manager.execute_policy(scaling_group=scaling_group,
                policy=policy)


    def delete_policy(self, scaling_group, policy):
        """
        Deletes the specified policy from the scaling group.
        """
        return self._manager.delete_policy(scaling_group=scaling_group,
                policy=policy)


    def add_webhook(self, scaling_group, policy, name, metadata=None):
        """
        Adds a webhook to the specified policy.
        """
        return self._manager.add_webhook(scaling_group, policy, name,
                metadata=metadata)


    def list_webhooks(self, scaling_group, policy):
        """
        Returns a list of all webhooks defined for the specified policy.
        """
        return self._manager.list_webhooks(scaling_group, policy)


    def get_webhook(self, scaling_group, policy, webhook):
        """
        Gets the detail for the specified webhook.
        """
        return self._manager.get_webhook(scaling_group, policy, webhook)


    def replace_webhook(self, scaling_group, policy, webhook, name,
            metadata=None):
        """
        Replace an existing webhook. All of the attributes must be specified.
        If you wish to delete any of the optional attributes, pass them in as
        None.
        """
        return self._manager.replace_webhook(scaling_group, policy, webhook,
                name, metadata=metadata)


    def update_webhook(self, scaling_group, policy, webhook, name=None,
            metadata=None):
        """
        Updates the specified webhook. One or more of the parameters may be
        specified.
        """
        return self._manager.update_webhook(scaling_group=scaling_group,
                policy=policy, webhook=webhook, name=name, metadata=metadata)


    def update_webhook_metadata(self, scaling_group, policy, webhook, metadata):
        """
        Adds the given metadata dict to the existing metadata for the specified
        webhook.
        """
        return self._manager.update_webhook_metadata(scaling_group, policy,
                webhook, metadata)


    def delete_webhook(self, scaling_group, policy, webhook):
        """
        Deletes the specified webhook from the policy.
        """
        return self._manager.delete_webhook(scaling_group, policy, webhook)
