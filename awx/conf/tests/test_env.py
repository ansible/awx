

# Ensure that our autouse overwrites are working
def test_cache(settings):
    assert settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'
    assert settings.CACHES['default']['LOCATION'].startswith('unique-')
