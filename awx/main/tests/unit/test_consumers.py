from collections import namedtuple

import pytest

from awx.main.consumers import origin_is_valid


def _msg(origin):
    return namedtuple('message', ('content',))({
        'headers': [
            ('origin', origin)
        ]
    })


@pytest.mark.parametrize('origin, trusted, valid', [
    ('https://tower.example.org', ['https://tower.example.org'], True),           # exact match
    ('https://tower.example.org/', ['https://tower.example.org'], True),          # trailing slash match
    ('https://tower.example.org', ['https://.example.org'], True),                # wildcard match
    ('https://proxy.tower.example.org', ['https://.tower.example.org'], True),    # complex wildcard match
    ('', ['https://tower.example.org'], False),                                   # origin header empty
    (None, ['https://tower.example.org'], False),                                 # origin header unset
    ('https://[\">[', ['https://tower.example.org'], False),                      # origin header garbage
    ('file:///bad.html', ['https://tower.example.org'], False),                   # file:// origin blocked
    ('http://tower.example.org', ['https://tower.example.org'], False),           # http != https
    ('https://tower.example.org:443', ['https://tower.example.org:8043'], False), # port mismatch
    ('https://evil.example.com', ['https://tower.example.org'], False),           # domain mismatch
    ('https://tower.example.org', [], False),                                     # no trusted hosts
    ('https://a', ['https://a', 'https://b'], True),                              # multiple with a match
    ('https://evil', ['https://a', 'https://b'], False),                          # multiple no match
])
def test_trusted_origin(origin, trusted, valid):
    assert origin_is_valid(_msg(origin), trusted) is valid
