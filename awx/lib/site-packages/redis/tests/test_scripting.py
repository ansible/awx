from __future__ import with_statement
import pytest

from redis import exceptions
from redis._compat import b


multiply_script = """
local value = redis.call('GET', KEYS[1])
value = tonumber(value)
return value * ARGV[1]"""


class TestScripting(object):
    @pytest.fixture(autouse=True)
    def reset_scripts(self, r):
        r.script_flush()

    def test_eval(self, r):
        r.set('a', 2)
        # 2 * 3 == 6
        assert r.eval(multiply_script, 1, 'a', 3) == 6

    def test_evalsha(self, r):
        r.set('a', 2)
        sha = r.script_load(multiply_script)
        # 2 * 3 == 6
        assert r.evalsha(sha, 1, 'a', 3) == 6

    def test_evalsha_script_not_loaded(self, r):
        r.set('a', 2)
        sha = r.script_load(multiply_script)
        # remove the script from Redis's cache
        r.script_flush()
        with pytest.raises(exceptions.NoScriptError):
            r.evalsha(sha, 1, 'a', 3)

    def test_script_loading(self, r):
        # get the sha, then clear the cache
        sha = r.script_load(multiply_script)
        r.script_flush()
        assert r.script_exists(sha) == [False]
        r.script_load(multiply_script)
        assert r.script_exists(sha) == [True]

    def test_script_object(self, r):
        r.set('a', 2)
        multiply = r.register_script(multiply_script)
        assert not multiply.sha
        # test evalsha fail -> script load + retry
        assert multiply(keys=['a'], args=[3]) == 6
        assert multiply.sha
        assert r.script_exists(multiply.sha) == [True]
        # test first evalsha
        assert multiply(keys=['a'], args=[3]) == 6

    def test_script_object_in_pipeline(self, r):
        multiply = r.register_script(multiply_script)
        assert not multiply.sha
        pipe = r.pipeline()
        pipe.set('a', 2)
        pipe.get('a')
        multiply(keys=['a'], args=[3], client=pipe)
        # even though the pipeline wasn't executed yet, we made sure the
        # script was loaded and got a valid sha
        assert multiply.sha
        assert r.script_exists(multiply.sha) == [True]
        # [SET worked, GET 'a', result of multiple script]
        assert pipe.execute() == [True, b('2'), 6]

        # purge the script from redis's cache and re-run the pipeline
        # the multiply script object knows it's sha, so it shouldn't get
        # reloaded until pipe.execute()
        r.script_flush()
        pipe = r.pipeline()
        pipe.set('a', 2)
        pipe.get('a')
        assert multiply.sha
        multiply(keys=['a'], args=[3], client=pipe)
        assert r.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert pipe.execute() == [True, b('2'), 6]
