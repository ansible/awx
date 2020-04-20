from collections import defaultdict
import logging
import re

from awxkit.utils import is_list_or_tuple, not_provided

log = logging.getLogger(__name__)


class URLRegistry(object):

    def __init__(self):
        self.store = defaultdict(dict)
        self.default = {}

    def url_pattern(self, pattern_str):
        """Converts some regex-friendly url pattern (Resources().resource string)
        to a compiled pattern.
        """
        # should account for any relative endpoint w/ query parameters
        pattern = r'^' + pattern_str + r'(\?.*)*$'
        return re.compile(pattern)

    def _generate_url_iterable(self, url_iterable):
        parsed_urls = []
        for url in url_iterable:
            method = not_provided
            if is_list_or_tuple(url):
                url, method = url
            if not is_list_or_tuple(method):
                methods = (method,)
            else:
                methods = method
            for method in methods:
                method_pattern = re.compile(method)
                url_pattern = self.url_pattern(url)
                parsed_urls.append((url_pattern, method_pattern))
        return parsed_urls

    def register(self, *args):
        """Registers a single resource (generic python type or object) to either
        1. a single url string (internally coverted via URLRegistry.url_pattern) and optional method or method iterable
        2. a list or tuple of url string and optional method or method iterables
        for retrieval via get().

        reg.register('/some/path/', ResourceOne)
        reg.get('/some/path/')
        -> ResourceOne
        reg.register('/some/other/path/', 'method', ResourceTwo)
        reg.get('/some/other/path/', 'method')
        -> ResourceTwo
        reg.register('/some/additional/path/', ('method_one', 'method_two'), ResourceThree)
        reg.get('/some/additional/path/', 'method_one')
        -> ResourceThree
        reg.get('/some/additional/path/', 'method_two')
        -> ResourceThree
        reg.register(('/some/new/path/one/', '/some/new/path/two/',
                      ('/some/other/new/path', 'method'),
                      ('/some/other/additional/path/, ('method_one', 'method_two')), ResourceFour))
        reg.get('/some/other/new/path/', 'method')
        -> ResourceFour
        """
        if not args or len(args) == 1:
            raise TypeError('register needs at least a url and Resource.')
        elif len(args) not in (2, 3):
            raise TypeError('register takes at most 3 arguments ({} given).'.format(len(args)))

        if len(args) == 3:  # url, method (iterable), and Resource
            url_iterable = (args[:2],)
            resource = args[2]
        else:
            urls, resource = args
            if not is_list_or_tuple(urls):
                url_iterable = [(urls, not_provided)]
            else:
                url_iterable = urls

        url_iterable = self._generate_url_iterable(url_iterable)
        for url_pattern, method_pattern in url_iterable:
            if url_pattern in self.store and method_pattern in self.store[url_pattern]:
                if method_pattern.pattern == not_provided:
                    exc_msg = '"{0.pattern}" already has methodless registration.'.format(url_pattern)
                else:
                    exc_msg = ('"{0.pattern}" already has registered method "{1.pattern}"'
                               .format(url_pattern, method_pattern))
                raise TypeError(exc_msg)
            self.store[url_pattern][method_pattern] = resource

    def setdefault(self, *args):
        """Establishes a default return value for get() by optional method (iterable).

        reg.setdefault(ResourceOne)
        reg.get('/some/unregistered/path')
        -> ResourceOne
        reg.setdefault('method', ResourceTwo)
        reg.get('/some/registered/methodless/path/', 'method')
        -> ResourceTwo
        reg.setdefault(('method_one', 'method_two'), ResourceThree)
        reg.get('/some/unregistered/path', 'method_two')
        -> ResourceThree
        reg.setdefault('supports.*regex', ResourceFour)
        reg.get('supports123regex')
        -> ResourceFour
        """
        if not args:
            raise TypeError('setdefault needs at least a Resource.')
        if len(args) == 1:  # all methods
            self.default[re.compile('.*')] = args[0]
        elif len(args) == 2:
            if is_list_or_tuple(args[0]):
                methods = args[0]
            else:
                methods = (args[0],)
            for method in methods:
                method_pattern = re.compile(method)
                self.default[method_pattern] = args[1]
        else:
            raise TypeError('setdefault takes at most 2 arguments ({} given).'.format(len(args)))

    def get(self, url, method=not_provided):
        """Returns a single resource by previously registered path and optional method where
        1.  If a registration was methodless and a method is provided to get() the return value will be
            None or, if applicable, a registry default (see setdefault()).
        2.  If a registration included a method (excluding the method wildcard '.*') and no method is provided to get()
            the return value will be None or, if applicable, a registry default.

        reg.register('/some/path/', ResourceOne)
        reg.get('/some/path/')
        -> ResourceOne
        reg.get('/some/path/', 'method')
        -> None
        reg.register('/some/other/path/', 'method', ResourceTwo)
        reg.get('/some/other/path/', 'method')
        -> ResourceTwo
        reg.get('/some/other/path')
        -> None
        reg.register('/some/additional/path/', '.*', ResourceThree)
        reg.get('/some/additional/path/', 'method')
        -> ResourceThree
        reg.get('/some/additional/path/')
        -> ResourceThree
        """
        registered_type = None
        default_methods = list(self.default)
        # Make sure dot character evaluated last
        default_methods.sort(key=lambda x: x.pattern == '.*')
        for method_key in default_methods:
            if method_key.match(method):
                registered_type = self.default[method_key]
                break

        for re_key in self.store:
            if re_key.match(url):
                keys = list(self.store[re_key])
                keys.sort(key=lambda x: x.pattern == '.*')
                for method_key in keys:
                    if method_key.match(method):
                        registered_type = self.store[re_key][method_key]
                        break
        log.debug('Retrieved {} by url: {}'.format(registered_type, url))
        return registered_type
