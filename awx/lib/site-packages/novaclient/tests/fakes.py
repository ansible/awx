"""
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might raise AssertionError. I've indicated in comments the
places where actual behavior differs from the spec.
"""

from novaclient import base


def assert_has_keys(dict, required=[], optional=[]):
    keys = dict.keys()
    for k in required:
        try:
            assert k in keys
        except AssertionError:
            extra_keys = set(keys).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                    list(extra_keys))


class FakeClient(object):

    def assert_called(self, method, url, body=None, pos=-1):
        """
        Assert than an API method was just called.
        """
        expected = (method, url)
        called = self.client.callstack[pos][0:2]

        assert self.client.callstack, \
                       "Expected %s %s but no calls were made." % expected

        assert expected == called, 'Expected %s %s; got %s %s' % \
                                               (expected + called)

        if body is not None:
            if self.client.callstack[pos][2] != body:
                raise AssertionError('%r != %r' %
                                     (self.client.callstack[pos][2], body))

    def assert_called_anytime(self, method, url, body=None):
        """
        Assert than an API method was called anytime in the test.
        """
        expected = (method, url)

        assert self.client.callstack, \
                       "Expected %s %s but no calls were made." % expected

        found = False
        for entry in self.client.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, 'Expected %s; got %s' % \
                              (expected, self.client.callstack)
        if body is not None:
            try:
                assert entry[2] == body
            except AssertionError:
                print(entry[2])
                print("!=")
                print(body)
                raise

        self.client.callstack = []

    def clear_callstack(self):
        self.client.callstack = []

    def authenticate(self):
        pass


# Fake class that will be used as an extension
class FakeManager(base.Manager):
    pass
