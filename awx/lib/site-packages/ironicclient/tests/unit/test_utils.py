# -*- coding: utf-8 -*-
#
# Copyright 2013 OpenStack LLC.
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

import os
import subprocess

import mock

from ironicclient.common import utils
from ironicclient import exc
from ironicclient.tests.unit import utils as test_utils


class UtilsTest(test_utils.BaseTestCase):

    def test_args_array_to_dict(self):
        my_args = {
            'matching_metadata': ['str=foo', 'int=1', 'bool=true',
                                  'list=[1, 2, 3]', 'dict={"foo": "bar"}'],
            'other': 'value'
        }
        cleaned_dict = utils.args_array_to_dict(my_args,
                                                "matching_metadata")
        self.assertEqual({
            'matching_metadata': {'str': 'foo', 'int': 1, 'bool': True,
                                  'list': [1, 2, 3], 'dict': {'foo': 'bar'}},
            'other': 'value'
        }, cleaned_dict)

    def test_args_array_to_patch(self):
        my_args = {
            'attributes': ['str=foo', 'int=1', 'bool=true',
                           'list=[1, 2, 3]', 'dict={"foo": "bar"}'],
            'op': 'add',
        }
        patch = utils.args_array_to_patch(my_args['op'],
                                          my_args['attributes'])
        self.assertEqual([{'op': 'add', 'value': 'foo', 'path': '/str'},
                          {'op': 'add', 'value': 1, 'path': '/int'},
                          {'op': 'add', 'value': True, 'path': '/bool'},
                          {'op': 'add', 'value': [1, 2, 3], 'path': '/list'},
                          {'op': 'add', 'value': {"foo": "bar"},
                           'path': '/dict'}], patch)

    def test_args_array_to_patch_format_error(self):
        my_args = {
            'attributes': ['foobar'],
            'op': 'add',
        }
        self.assertRaises(exc.CommandError, utils.args_array_to_patch,
                          my_args['op'], my_args['attributes'])

    def test_args_array_to_patch_remove(self):
        my_args = {
            'attributes': ['/foo', 'extra/bar'],
            'op': 'remove',
        }
        patch = utils.args_array_to_patch(my_args['op'],
                                          my_args['attributes'])
        self.assertEqual([{'op': 'remove', 'path': '/foo'},
                          {'op': 'remove', 'path': '/extra/bar'}], patch)

    def test_split_and_deserialize(self):
        ret = utils.split_and_deserialize('str=foo')
        self.assertEqual(('str', 'foo'), ret)

        ret = utils.split_and_deserialize('int=1')
        self.assertEqual(('int', 1), ret)

        ret = utils.split_and_deserialize('bool=false')
        self.assertEqual(('bool', False), ret)

        ret = utils.split_and_deserialize('list=[1, "foo", 2]')
        self.assertEqual(('list', [1, "foo", 2]), ret)

        ret = utils.split_and_deserialize('dict={"foo": 1}')
        self.assertEqual(('dict', {"foo": 1}), ret)

        ret = utils.split_and_deserialize('str_int="1"')
        self.assertEqual(('str_int', "1"), ret)

    def test_split_and_deserialize_fail(self):
        self.assertRaises(exc.CommandError,
                          utils.split_and_deserialize, 'foo:bar')


class CommonParamsForListTest(test_utils.BaseTestCase):
    def setUp(self):
        super(CommonParamsForListTest, self).setUp()
        self.args = mock.Mock(marker=None, limit=None,
                              sort_key=None, sort_dir=None)
        self.args.detail = False
        self.expected_params = {'detail': False}

    def test_nothing_set(self):
        self.assertEqual(self.expected_params,
                         utils.common_params_for_list(self.args, [], []))

    def test_marker_and_limit(self):
        self.args.marker = 'foo'
        self.args.limit = 42
        self.expected_params.update({'marker': 'foo', 'limit': 42})
        self.assertEqual(self.expected_params,
                         utils.common_params_for_list(self.args, [], []))

    def test_invalid_limit(self):
        self.args.limit = -42
        self.assertRaises(exc.CommandError,
                          utils.common_params_for_list,
                          self.args, [], [])

    def test_sort_key_and_sort_dir(self):
        self.args.sort_key = 'field'
        self.args.sort_dir = 'desc'
        self.expected_params.update({'sort_key': 'field', 'sort_dir': 'desc'})
        self.assertEqual(self.expected_params,
                         utils.common_params_for_list(self.args,
                                                      ['field'],
                                                      []))

    def test_sort_key_allows_label(self):
        self.args.sort_key = 'Label'
        self.expected_params.update({'sort_key': 'field'})
        self.assertEqual(self.expected_params,
                         utils.common_params_for_list(self.args,
                                                      ['field', 'field2'],
                                                      ['Label', 'Label2']))

    def test_sort_key_invalid(self):
        self.args.sort_key = 'something'
        self.assertRaises(exc.CommandError,
                          utils.common_params_for_list,
                          self.args,
                          ['field', 'field2'],
                          [])

    def test_sort_dir_invalid(self):
        self.args.sort_dir = 'something'
        self.assertRaises(exc.CommandError,
                          utils.common_params_for_list,
                          self.args,
                          [],
                          [])

    def test_detail(self):
        self.args.detail = True
        self.expected_params['detail'] = True
        self.assertEqual(self.expected_params,
                         utils.common_params_for_list(self.args, [], []))


class CommonFiltersTest(test_utils.BaseTestCase):
    def test_limit(self):
        result = utils.common_filters(limit=42)
        self.assertEqual(['limit=42'], result)

    def test_limit_0(self):
        result = utils.common_filters(limit=0)
        self.assertEqual([], result)

    def test_other(self):
        for key in ('marker', 'sort_key', 'sort_dir'):
            result = utils.common_filters(**{key: 'test'})
            self.assertEqual(['%s=test' % key], result)


@mock.patch.object(subprocess, 'Popen')
class MakeConfigDriveTest(test_utils.BaseTestCase):

    def setUp(self):
        super(MakeConfigDriveTest, self).setUp()
        # expected genisoimage cmd
        self.genisoimage_cmd = ['genisoimage', '-o', mock.ANY,
                                '-ldots', '-allow-lowercase',
                                '-allow-multidot', '-l',
                                '-publisher', 'ironicclient-configdrive 0.1',
                                '-quiet', '-J', '-r', '-V',
                                'config-2', mock.ANY]

    def test_make_configdrive(self, mock_popen):
        fake_process = mock.Mock(returncode=0)
        fake_process.communicate.return_value = ('', '')
        mock_popen.return_value = fake_process

        with utils.tempdir() as dirname:
            utils.make_configdrive(dirname)

        mock_popen.assert_called_once_with(self.genisoimage_cmd,
                                           stderr=subprocess.PIPE,
                                           stdout=subprocess.PIPE)
        fake_process.communicate.assert_called_once_with()

    @mock.patch.object(os, 'access')
    def test_make_configdrive_non_readable_dir(self, mock_access, mock_popen):
        mock_access.return_value = False
        self.assertRaises(exc.CommandError, utils.make_configdrive, 'fake-dir')
        mock_access.assert_called_once_with('fake-dir', os.R_OK)
        self.assertFalse(mock_popen.called)

    @mock.patch.object(os, 'access')
    def test_make_configdrive_oserror(self, mock_access, mock_popen):
        mock_access.return_value = True
        mock_popen.side_effect = OSError('boom')

        self.assertRaises(exc.CommandError, utils.make_configdrive, 'fake-dir')
        mock_access.assert_called_once_with('fake-dir', os.R_OK)
        mock_popen.assert_called_once_with(self.genisoimage_cmd,
                                           stderr=subprocess.PIPE,
                                           stdout=subprocess.PIPE)

    @mock.patch.object(os, 'access')
    def test_make_configdrive_non_zero_returncode(self, mock_access,
                                                  mock_popen):
        fake_process = mock.Mock(returncode=123)
        fake_process.communicate.return_value = ('', '')
        mock_popen.return_value = fake_process

        self.assertRaises(exc.CommandError, utils.make_configdrive, 'fake-dir')
        mock_access.assert_called_once_with('fake-dir', os.R_OK)
        mock_popen.assert_called_once_with(self.genisoimage_cmd,
                                           stderr=subprocess.PIPE,
                                           stdout=subprocess.PIPE)
        fake_process.communicate.assert_called_once_with()
