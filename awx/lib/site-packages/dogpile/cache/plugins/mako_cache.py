"""
Mako Integration
----------------

dogpile.cache includes a `Mako <http://www.makotemplates.org>`_ plugin
that replaces `Beaker <http://beaker.groovie.org>`_
as the cache backend.
Setup a Mako template lookup using the "dogpile.cache" cache implementation
and a region dictionary::

    from dogpile.cache import make_region
    from mako.lookup import TemplateLookup

    my_regions = {
        "local":make_region().configure(
                    "dogpile.cache.dbm",
                    expiration_time=360,
                    arguments={"filename":"file.dbm"}
                ),
        "memcached":make_region().configure(
                    "dogpile.cache.pylibmc",
                    expiration_time=3600,
                    arguments={"url":["127.0.0.1"]}
                )
    }

    mako_lookup = TemplateLookup(
        directories=["/myapp/templates"],
        cache_impl="dogpile.cache",
        cache_args={
            'regions':my_regions
        }
    )

To use the above configuration in a template, use the ``cached=True``
argument  on any Mako tag which accepts it, in conjunction with the
name of the desired region as the ``cache_region`` argument::

    <%def name="mysection()" cached="True" cache_region="memcached">
        some content that's cached
    </%def>


"""
from mako.cache import CacheImpl


class MakoPlugin(CacheImpl):
    """A Mako ``CacheImpl`` which talks to dogpile.cache."""

    def __init__(self, cache):
        super(MakoPlugin, self).__init__(cache)
        try:
            self.regions = self.cache.template.cache_args['regions']
        except KeyError:
            raise KeyError(
                "'cache_regions' argument is required on the "
                "Mako Lookup or Template object for usage "
                "with the dogpile.cache plugin.")

    def _get_region(self, **kw):
        try:
            region = kw['region']
        except KeyError:
            raise KeyError(
                "'cache_region' argument must be specified with 'cache=True'"
                "within templates for usage with the dogpile.cache plugin.")
        try:
            return self.regions[region]
        except KeyError:
            raise KeyError("No such region '%s'" % region)

    def get_and_replace(self, key, creation_function, **kw):
        expiration_time = kw.pop("timeout", None)
        return self._get_region(**kw).get_or_create(
            key, creation_function,
            expiration_time=expiration_time)

    def get_or_create(self, key, creation_function, **kw):
        return self.get_and_replace(key, creation_function, **kw)

    def put(self, key, value, **kw):
        self._get_region(**kw).put(key, value)

    def get(self, key, **kw):
        expiration_time = kw.pop("timeout", None)
        return self._get_region(**kw).get(key, expiration_time=expiration_time)

    def invalidate(self, key, **kw):
        self._get_region(**kw).delete(key)
