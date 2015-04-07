# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might raise AssertionError. I've indicated in comments the
places where actual behavior differs from the spec.
"""

from __future__ import print_function


def assert_has_keys(dict, required=[], optional=[]):
    for k in required:
        try:
            assert k in dict
        except AssertionError:
            extra_keys = set(dict).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                                 list(extra_keys))


class FakeClient(object):

    def _dict_match(self, partial, real):

        result = True
        try:
            for key, value in partial.items():
                if type(value) is dict:
                    result = self._dict_match(value, real[key])
                else:
                    assert real[key] == value
                    result = True
        except (AssertionError, KeyError):
            result = False
        return result

    def assert_called(self, method, url, body=None,
                      partial_body=None, pos=-1, **kwargs):
        """
        Assert than an API method was just called.
        """
        expected = (method, url)
        called = self.client.callstack[pos][0:2]

        assert self.client.callstack, ("Expected %s %s but no calls "
                                       "were made." % expected)

        assert expected == called, 'Expected %s %s; got %s %s' % (
            expected + called)

        if body is not None:
            assert self.client.callstack[pos][2] == body

        if partial_body is not None:
            try:
                assert self._dict_match(partial_body,
                                        self.client.callstack[pos][2])
            except AssertionError:
                print(self.client.callstack[pos][2])
                print("does not contain")
                print(partial_body)
                raise

    def assert_called_anytime(self, method, url, body=None, partial_body=None):
        """
        Assert than an API method was called anytime in the test.
        """
        expected = (method, url)

        assert self.client.callstack, ("Expected %s %s but no calls "
                                       "were made." % expected)

        found = False
        for entry in self.client.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, 'Expected %s %s; got %s' % (
            expected + (self.client.callstack, ))

        if body is not None:
            try:
                assert entry[2] == body
            except AssertionError:
                print(entry[2])
                print("!=")
                print(body)
                raise

        if partial_body is not None:
            try:
                assert self._dict_match(partial_body, entry[2])
            except AssertionError:
                print(entry[2])
                print("does not contain")
                print(partial_body)
                raise

    def clear_callstack(self):
        self.client.callstack = []

    def authenticate(self):
        pass
