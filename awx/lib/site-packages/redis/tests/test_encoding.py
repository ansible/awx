from __future__ import with_statement
import pytest

from redis._compat import unichr, u, unicode
from .conftest import r as _redis_client


class TestEncoding(object):
    @pytest.fixture()
    def r(self, request):
        return _redis_client(request=request, decode_responses=True)

    def test_simple_encoding(self, r):
        unicode_string = unichr(3456) + u('abcd') + unichr(3421)
        r['unicode-string'] = unicode_string
        cached_val = r['unicode-string']
        assert isinstance(cached_val, unicode)
        assert unicode_string == cached_val

    def test_list_encoding(self, r):
        unicode_string = unichr(3456) + u('abcd') + unichr(3421)
        result = [unicode_string, unicode_string, unicode_string]
        r.rpush('a', *result)
        assert r.lrange('a', 0, -1) == result


class TestCommandsAndTokensArentEncoded(object):
    @pytest.fixture()
    def r(self, request):
        return _redis_client(request=request, charset='utf-16')

    def test_basic_command(self, r):
        r.set('hello', 'world')
