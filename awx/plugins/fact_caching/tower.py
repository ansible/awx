from ansible.cache.base import BaseCacheModule

class TowerCacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        pass

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def keys(self):
        pass

    def contains(self, key):
        pass

    def delete(self, key):
        pass

    def flush(self):
        pass

    def copy(self):
        pass
