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
# @author: Swaminathan Vasudevan, Hewlett Packard.

import testtools

from neutronclient.common import exceptions
from neutronclient.common import utils
from neutronclient.neutron.v2_0.vpn import utils as vpn_utils


class TestVPNUtils(testtools.TestCase):

    def test_validate_lifetime_dictionary_seconds(self):
        input_str = utils.str2dict("units=seconds,value=3600")
        self.assertIsNone(vpn_utils.validate_lifetime_dict(input_str))

    def test_validate_dpd_dictionary_action_hold(self):
        input_str = utils.str2dict("action=hold,interval=30,timeout=120")
        self.assertIsNone(vpn_utils.validate_dpd_dict(input_str))

    def test_validate_dpd_dictionary_action_restart(self):
        input_str = utils.str2dict("action=restart,interval=30,timeout=120")
        self.assertIsNone(vpn_utils.validate_dpd_dict(input_str))

    def test_validate_dpd_dictionary_action_restart_by_peer(self):
        input_str = utils.str2dict(
            "action=restart-by-peer,interval=30,timeout=120"
        )
        self.assertIsNone(vpn_utils.validate_dpd_dict(input_str))

    def test_validate_dpd_dictionary_action_clear(self):
        input_str = utils.str2dict('action=clear,interval=30,timeout=120')
        self.assertIsNone(vpn_utils.validate_dpd_dict(input_str))

    def test_validate_dpd_dictionary_action_disabled(self):
        input_str = utils.str2dict('action=disabled,interval=30,timeout=120')
        self.assertIsNone(vpn_utils.validate_dpd_dict(input_str))

    def test_validate_lifetime_dictionary_invalid_unit_key(self):
        input_str = utils.str2dict('ut=seconds,value=3600')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_invalid_unit_key_value(self):
        input_str = utils.str2dict('units=seconds,val=3600')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_unsupported_units(self):
        input_str = utils.str2dict('units=minutes,value=3600')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_invalid_empty_unit(self):
        input_str = utils.str2dict('units=,value=3600')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_under_minimum_integer_value(self):
        input_str = utils.str2dict('units=seconds,value=59')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_negative_integer_value(self):
        input_str = utils.str2dict('units=seconds,value=-1')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_lifetime_dictionary_empty_value(self):
        input_str = utils.str2dict('units=seconds,value=')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_dpd_dictionary_invalid_key_action(self):
        input_str = utils.str2dict('act=hold,interval=30,timeout=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_invalid_key_interval(self):
        input_str = utils.str2dict('action=hold,int=30,timeout=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_invalid_key_timeout(self):
        input_str = utils.str2dict('action=hold,interval=30,tiut=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_unsupported_action(self):
        input_str = utils.str2dict('action=bye-bye,interval=30,timeout=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_empty_action(self):
        input_str = utils.str2dict('action=,interval=30,timeout=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_empty_interval(self):
        input_str = utils.str2dict('action=hold,interval=,timeout=120')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_negative_interval_value(self):
        input_str = utils.str2dict('action=hold,interval=-1,timeout=120')
        self._test_validate_lifetime_negative_test_case(input_str)

    def test_validate_dpd_dictionary_zero_timeout(self):
        input_str = utils.str2dict('action=hold,interval=30,timeout=0')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_empty_timeout(self):
        input_str = utils.str2dict('action=hold,interval=30,timeout=')
        self._test_validate_dpd_negative_test_case(input_str)

    def test_validate_dpd_dictionary_negative_timeout_value(self):
        input_str = utils.str2dict('action=hold,interval=30,timeout=-1')
        self._test_validate_lifetime_negative_test_case(input_str)

    def _test_validate_lifetime_negative_test_case(self, input_str):
        """Generic handler for negative lifetime tests."""
        self.assertRaises(exceptions.CommandError,
                          vpn_utils.validate_lifetime_dict,
                          (input_str))

    def _test_validate_dpd_negative_test_case(self, input_str):
        """Generic handler for negative lifetime tests."""
        self.assertRaises(exceptions.CommandError,
                          vpn_utils.validate_lifetime_dict,
                          (input_str))
