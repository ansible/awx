from nose.tools import ok_


def fail(msg):
    raise AssertionError(msg)


def assert_in(thing, seq, msg=None):
    msg = msg or "'%s' not found in %s" % (thing, seq)
    ok_(thing in seq, msg)


def assert_not_in(thing, seq, msg=None):
    msg = msg or "unexpected '%s' found in %s" % (thing, seq)
    ok_(thing not in seq, msg)


def assert_has_keys(dict, required=[], optional=[]):
    keys = dict.keys()
    for k in required:
        assert_in(k, keys, "required key %s missing from %s" % (k, dict))
    allowed_keys = set(required) | set(optional)
    extra_keys = set(keys).difference(allowed_keys)
    if extra_keys:
        fail("found unexpected keys: %s" % list(extra_keys))


def assert_isinstance(thing, kls):
    ok_(isinstance(thing, kls), "%s is not an instance of %s" % (thing, kls))
