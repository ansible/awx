#    (c) Copyright 2013 Hewlett-Packard Development Company, L.P.
#    All Rights Reserved.
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
#
# @author: Swaminathan Vasudevan, Hewlett-Packard.
#


"""VPN Utilities and helper functions."""


from neutronclient.common import exceptions
from neutronclient.i18n import _

dpd_supported_actions = ['hold', 'clear', 'restart',
                         'restart-by-peer', 'disabled']
dpd_supported_keys = ['action', 'interval', 'timeout']

lifetime_keys = ['units', 'value']
lifetime_units = ['seconds']


def validate_dpd_dict(dpd_dict):
    for key, value in dpd_dict.items():
        if key not in dpd_supported_keys:
            message = _(
                "DPD Dictionary KeyError: "
                "Reason-Invalid DPD key : "
                "'%(key)s' not in %(supported_key)s ") % {
                    'key': key, 'supported_key': dpd_supported_keys}
            raise exceptions.CommandError(message)
        if key == 'action' and value not in dpd_supported_actions:
            message = _(
                "DPD Dictionary ValueError: "
                "Reason-Invalid DPD action : "
                "'%(key_value)s' not in %(supported_action)s ") % {
                    'key_value': value,
                    'supported_action': dpd_supported_actions}
            raise exceptions.CommandError(message)
        if key in ('interval', 'timeout'):
            try:
                if int(value) <= 0:
                    raise ValueError()
            except ValueError:
                message = _(
                    "DPD Dictionary ValueError: "
                    "Reason-Invalid positive integer value: "
                    "'%(key)s' = %(value)s ") % {
                        'key': key, 'value': value}
                raise exceptions.CommandError(message)
            else:
                dpd_dict[key] = int(value)
    return


def validate_lifetime_dict(lifetime_dict):

    for key, value in lifetime_dict.items():
        if key not in lifetime_keys:
            message = _(
                "Lifetime Dictionary KeyError: "
                "Reason-Invalid unit key : "
                "'%(key)s' not in %(supported_key)s ") % {
                    'key': key, 'supported_key': lifetime_keys}
            raise exceptions.CommandError(message)
        if key == 'units' and value not in lifetime_units:
            message = _(
                "Lifetime Dictionary ValueError: "
                "Reason-Invalid units : "
                "'%(key_value)s' not in %(supported_units)s ") % {
                    'key_value': key, 'supported_units': lifetime_units}
            raise exceptions.CommandError(message)
        if key == 'value':
            try:
                if int(value) < 60:
                    raise ValueError()
            except ValueError:
                message = _(
                    "Lifetime Dictionary ValueError: "
                    "Reason-Invalid value should be at least 60:"
                    "'%(key_value)s' = %(value)s ") % {
                        'key_value': key, 'value': value}
                raise exceptions.CommandError(message)
            else:
                lifetime_dict['value'] = int(value)
    return


def lifetime_help(policy):
    lifetime = _("%s lifetime attributes. "
                 "'units'-seconds, default:seconds. "
                 "'value'-non negative integer, default:3600.") % policy
    return lifetime


def dpd_help(policy):
    dpd = _(" %s Dead Peer Detection attributes."
            " 'action'-hold,clear,disabled,restart,restart-by-peer."
            " 'interval' and 'timeout' are non negative integers. "
            " 'interval' should be less than 'timeout' value. "
            " 'action', default:hold 'interval', default:30, "
            " 'timeout', default:120.") % policy.capitalize()
    return dpd
