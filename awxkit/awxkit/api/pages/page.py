from contextlib import suppress
import inspect
import logging
import json
import re

from requests import Response
import http.client as http

from awxkit.utils import PseudoNamespace, is_relative_endpoint, are_same_endpoint, super_dir_set, is_list_or_tuple, to_str
from awxkit.api import utils
from awxkit.api.client import Connection
from awxkit.api.registry import URLRegistry
from awxkit.config import config
import awxkit.exceptions as exc


log = logging.getLogger(__name__)


_page_registry = URLRegistry()
get_registered_page = _page_registry.get


def is_license_invalid(response):
    if re.match(r".*Invalid license.*", response.text):
        return True
    if re.match(r".*Missing 'eula_accepted' property.*", response.text):
        return True
    if re.match(r".*'eula_accepted' must be True.*", response.text):
        return True
    if re.match(r".*Invalid license data.*", response.text):
        return True


def is_license_exceeded(response):
    if re.match(r".*license range of.*instances has been exceeded.*", response.text):
        return True
    if re.match(r".*License count of.*instances has been reached.*", response.text):
        return True
    if re.match(r".*License count of.*instances has been exceeded.*", response.text):
        return True
    if re.match(r".*License has expired.*", response.text):
        return True
    if re.match(r".*License is missing.*", response.text):
        return True


def is_duplicate_error(response):
    if re.match(r".*already exists.*", response.text):
        return True


def register_page(urls, page_cls):
    if not _page_registry.default:
        from awxkit.api.pages import Base

        _page_registry.setdefault(Base)

    if not is_list_or_tuple(urls):
        urls = [urls]
    # Register every methodless page with wildcard method
    # until more granular page objects exist (options, head, etc.)
    updated_urls = []
    for url_method_pair in urls:
        if isinstance(url_method_pair, str):
            url = url_method_pair
            method = '.*'
        else:
            url, method = url_method_pair
        updated_urls.append((url, method))

    page_cls.endpoint = updated_urls[0][0]
    return _page_registry.register(updated_urls, page_cls)


def objectify_response_json(response):
    """return a PseudoNamespace() from requests.Response.json()."""
    try:
        json = response.json()
    except ValueError:
        json = dict()

    # PseudoNamespace arg must be a dict, and json can be an array.
    # TODO: Assess if list elements should be PseudoNamespace
    if isinstance(json, dict):
        return PseudoNamespace(json)
    return json


class Page(object):

    endpoint = ''

    def __init__(self, connection=None, *a, **kw):
        if 'endpoint' in kw:
            self.endpoint = kw['endpoint']

        self.connection = connection or Connection(config.base_url, kw.get('verify', not config.assume_untrusted))

        self.r = kw.get('r', None)
        self.json = kw.get('json', objectify_response_json(self.r) if self.r else {})
        self.last_elapsed = kw.get('last_elapsed', None)

    def __getattr__(self, name):
        if 'json' in self.__dict__ and name in self.json:
            value = self.json[name]
            if not isinstance(value, TentativePage) and is_relative_endpoint(value):
                value = TentativePage(value, self.connection)
            elif isinstance(value, dict):
                for key, item in value.items():
                    if not isinstance(item, TentativePage) and is_relative_endpoint(item):
                        value[key] = TentativePage(item, self.connection)
            return value
        raise AttributeError("{!r} object has no attribute {!r}".format(self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if 'json' in self.__dict__ and name in self.json:
            # Update field only.  For new field use explicit patch
            self.patch(**{name: value})
        else:
            self.__dict__[name] = value

    def __str__(self):
        if hasattr(self, 'json'):
            return json.dumps(self.json, indent=4)
        return str(super(Page, self).__repr__())

    __repr__ = __str__

    def __dir__(self):
        attrs = super_dir_set(self.__class__)
        if 'json' in self.__dict__ and hasattr(self.json, 'keys'):
            attrs.update(self.json.keys())
        return sorted(attrs)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        return iter(self.json)

    @property
    def __item_class__(self):
        """Returns the class representing a single 'Page' item"""
        return self.__class__

    @classmethod
    def from_json(cls, raw, connection=None):
        resp = Response()
        data = json.dumps(raw)
        resp._content = bytes(data, 'utf-8')
        resp.encoding = 'utf-8'
        resp.status_code = 200
        return cls(r=resp, connection=connection)

    @property
    def bytes(self):
        if self.r is None:
            return b''
        return self.r.content

    def extract_data(self, response):
        """Takes a `requests.Response` and returns a data dict."""
        try:
            data = response.json()
        except ValueError as e:  # If there was no json to parse
            data = {}
            if response.text or response.status_code not in (200, 202, 204):
                text = response.text
                if len(text) > 1024:
                    text = text[:1024] + '... <<< Truncated >>> ...'
                log.debug("Unable to parse JSON response ({0.status_code}): {1} - '{2}'".format(response, e, text))

        return data

    def page_identity(self, response, request_json=None):
        """Takes a `requests.Response` and
        returns a new __item_class__ instance if the request method is not a get, or returns
           a __class__ instance if the request path is different than the caller's `endpoint`.
        """
        request_path = response.request.path_url
        if request_path == '/migrations_notran/':
            raise exc.IsMigrating('You have been redirected to the migration-in-progress page.')
        request_method = response.request.method.lower()

        self.last_elapsed = response.elapsed

        if isinstance(request_json, dict) and 'ds' in request_json:
            ds = request_json.ds
        else:
            ds = None

        data = self.extract_data(response)
        exc_str = "%s (%s) received" % (http.responses[response.status_code], response.status_code)

        exception = exception_from_status_code(response.status_code)
        if exception:
            raise exception(exc_str, data)

        if response.status_code in (http.OK, http.CREATED, http.ACCEPTED):

            # Not all JSON responses include a URL.  Grab it from the request
            # object, if needed.
            if 'url' in data:
                endpoint = data['url']
            else:
                endpoint = request_path

            data = objectify_response_json(response)

            if request_method in ('get', 'patch', 'put'):
                #  Update existing resource and return it
                if are_same_endpoint(self.endpoint, request_path):
                    self.json = data
                    self.r = response
                    return self

            registered_type = get_registered_page(request_path, request_method)
            return registered_type(self.connection, endpoint=endpoint, json=data, last_elapsed=response.elapsed, r=response, ds=ds)

        elif response.status_code == http.FORBIDDEN:
            if is_license_invalid(response):
                raise exc.LicenseInvalid(exc_str, data)
            elif is_license_exceeded(response):
                raise exc.LicenseExceeded(exc_str, data)
            else:
                raise exc.Forbidden(exc_str, data)

        elif response.status_code == http.BAD_REQUEST:
            if is_license_invalid(response):
                raise exc.LicenseInvalid(exc_str, data)
            if is_duplicate_error(response):
                raise exc.Duplicate(exc_str, data)
            else:
                raise exc.BadRequest(exc_str, data)
        else:
            raise exc.Unknown(exc_str, data)

    def update_identity(self, obj):
        """Takes a `Page` and updates attributes to reflect its content"""
        self.endpoint = obj.endpoint
        self.json = obj.json
        self.last_elapsed = obj.last_elapsed
        self.r = obj.r
        return self

    def delete(self):
        r = self.connection.delete(self.endpoint)
        with suppress(exc.NoContent):
            return self.page_identity(r)

    def get(self, all_pages=False, **query_parameters):
        r = self.connection.get(self.endpoint, query_parameters)
        page = self.page_identity(r)
        if all_pages and getattr(page, 'next', None):
            paged_results = [r.json()['results']]
            while page.next:
                r = self.connection.get(self.next)
                page = self.page_identity(r)
                paged_results.append(r.json()['results'])
            json = r.json()
            json['results'] = []
            for page in paged_results:
                json['results'].extend(page)
            page = self.__class__.from_json(json, connection=self.connection)
        return page

    def head(self):
        r = self.connection.head(self.endpoint)
        return self.page_identity(r)

    def options(self):
        r = self.connection.options(self.endpoint)
        return self.page_identity(r)

    def patch(self, **json):
        r = self.connection.patch(self.endpoint, json)
        return self.page_identity(r, request_json=json)

    def post(self, json={}):
        r = self.connection.post(self.endpoint, json)
        return self.page_identity(r, request_json=json)

    def put(self, json=None):
        """If a payload is supplied, PUT the payload. If not, submit our existing page JSON as our payload."""
        json = self.json if json is None else json
        r = self.connection.put(self.endpoint, json=json)
        return self.page_identity(r, request_json=json)

    def get_related(self, related_name, **kwargs):
        assert related_name in self.json.get('related', [])
        endpoint = self.json['related'][related_name]
        return self.walk(endpoint, **kwargs)

    def walk(self, endpoint, **kw):
        page_cls = get_registered_page(endpoint)
        return page_cls(self.connection, endpoint=endpoint).get(**kw)

    def get_natural_key(self, cache=None):
        if cache is None:
            cache = PageCache()

        if not getattr(self, 'NATURAL_KEY', None):
            log.warning("This object does not have a natural key: %s", getattr(self, 'endpoint', ''))
            return None

        natural_key = {}
        for key in self.NATURAL_KEY:
            if key in self.related:
                related_endpoint = cache.get_page(self.related[key])
                if related_endpoint is not None:
                    natural_key[key] = related_endpoint.get_natural_key(cache=cache)
                else:
                    natural_key[key] = None
            elif key in self:
                natural_key[key] = self[key]

        natural_key['type'] = self['type']
        return natural_key


_exception_map = {
    http.NO_CONTENT: exc.NoContent,
    http.NOT_FOUND: exc.NotFound,
    http.INTERNAL_SERVER_ERROR: exc.InternalServerError,
    http.BAD_GATEWAY: exc.BadGateway,
    http.METHOD_NOT_ALLOWED: exc.MethodNotAllowed,
    http.UNAUTHORIZED: exc.Unauthorized,
    http.PAYMENT_REQUIRED: exc.PaymentRequired,
    http.CONFLICT: exc.Conflict,
}


def exception_from_status_code(status_code):
    return _exception_map.get(status_code, None)


class PageList(object):

    NATURAL_KEY = None

    @property
    def __item_class__(self):
        """Returns the class representing a single 'Page' item
        With an inheritence of OrgListSubClass -> OrgList -> PageList -> Org -> Base -> Page, the following
        will return the parent class of the current object (e.g. 'Org').

        Obtaining a page type by registered endpoint is highly recommended over using this method.
        """
        mro = inspect.getmro(self.__class__)
        bl_index = mro.index(PageList)
        return mro[bl_index + 1]

    @property
    def results(self):
        items = []
        for item in self.json['results']:
            endpoint = item.get('url')
            if endpoint is None:
                registered_type = self.__item_class__
            else:
                registered_type = get_registered_page(endpoint)
            items.append(registered_type(self.connection, endpoint=endpoint, json=item, r=self.r))
        return items

    def go_to_next(self):
        if self.next:
            next_page = self.__class__(self.connection, endpoint=self.next)
            return next_page.get()

    def go_to_previous(self):
        if self.previous:
            prev_page = self.__class__(self.connection, endpoint=self.previous)
            return prev_page.get()

    def create(self, *a, **kw):
        return self.__item_class__(self.connection).create(*a, **kw)

    def get_natural_key(self, cache=None):
        log.warning("This object does not have a natural key: %s", getattr(self, 'endpoint', ''))
        return None


class TentativePage(str):
    def __new__(cls, endpoint, connection):
        return super(TentativePage, cls).__new__(cls, to_str(endpoint))

    def __init__(self, endpoint, connection):
        self.endpoint = to_str(endpoint)
        self.connection = connection

    def _create(self):
        return get_registered_page(self.endpoint)(self.connection, endpoint=self.endpoint)

    def get(self, **params):
        return self._create().get(**params)

    def create_or_replace(self, **query_parameters):
        """Create an object, and if any other item shares the name, delete that one first.

        Generally, requires 'name' of object.

        Exceptions:
          - Users are looked up by username
          - Teams need to be looked up by name + organization
        """
        page = None
        # look up users by username not name
        if 'users' in self:
            assert query_parameters.get('username'), 'For this resource, you must call this method with a "username" to look up the object by'
            page = self.get(username=query_parameters['username'])
        else:
            assert query_parameters.get('name'), 'For this resource, you must call this method with a "name" to look up the object by'
            if query_parameters.get('organization'):
                if isinstance(query_parameters.get('organization'), int):
                    page = self.get(name=query_parameters['name'], organization=query_parameters.get('organization'))
                else:
                    page = self.get(name=query_parameters['name'], organization=query_parameters.get('organization').id)
            else:
                page = self.get(name=query_parameters['name'])
        if page and page.results:
            for item in page.results:
                # We found a duplicate item, we will delete it
                # Some things, like inventory scripts, allow multiple scripts
                # by same name as long as they have different organization
                item.delete()
        # Now that we know that there is no duplicate, we create a new object
        return self.create(**query_parameters)

    def get_or_create(self, **query_parameters):
        """Get an object by this name or id if it exists, otherwise create it.

        Exceptions:
          - Users are looked up by username
          - Teams need to be looked up by name + organization
        """
        page = None
        # look up users by username not name
        if query_parameters.get('username') and 'users' in self:
            page = self.get(username=query_parameters['username'])
        if query_parameters.get('name'):
            if query_parameters.get('organization'):
                if isinstance(query_parameters.get('organization'), int):
                    page = self.get(name=query_parameters['name'], organization=query_parameters.get('organization'))
                else:
                    page = self.get(name=query_parameters['name'], organization=query_parameters.get('organization').id)
            else:
                page = self.get(name=query_parameters['name'])

        elif query_parameters.get('id'):
            page = self.get(id=query_parameters['id'])
        if page and page.results:
            item = page.results.pop()
            return item.url.get()
        else:
            # We did not find it given these params, we will create it instead
            return self.create(**query_parameters)

    def post(self, payload={}):
        return self._create().post(payload)

    def put(self):
        return self._create().put()

    def patch(self, **payload):
        return self._create().patch(**payload)

    def delete(self):
        return self._create().delete()

    def options(self):
        return self._create().options()

    def create(self, *a, **kw):
        return self._create().create(*a, **kw)

    def payload(self, *a, **kw):
        return self._create().payload(*a, **kw)

    def create_payload(self, *a, **kw):
        return self._create().create_payload(*a, **kw)

    def __str__(self):
        if hasattr(self, 'endpoint'):
            return self.endpoint
        return super(TentativePage, self).__str__()

    __repr__ = __str__

    def __eq__(self, other):
        return self.endpoint == other

    def __ne__(self, other):
        return self.endpoint != other


class PageCache(object):
    def __init__(self):
        self.options = {}
        self.pages_by_url = {}
        self.pages_by_natural_key = {}

    def get_options(self, page):
        url = page.endpoint if isinstance(page, Page) else str(page)
        if url in self.options:
            return self.options[url]

        try:
            options = page.options()
        except exc.Common:
            log.error("This endpoint raised an error: %s", url)
            return self.options.setdefault(url, None)

        warning = options.r.headers.get('Warning', '')
        if '299' in warning and 'deprecated' in warning:
            log.warning("This endpoint is deprecated: %s", url)
            return self.options.setdefault(url, None)

        return self.options.setdefault(url, options)

    def set_page(self, page):
        log.debug("set_page: %s %s", type(page), page.endpoint)
        self.pages_by_url[page.endpoint] = page
        if getattr(page, 'NATURAL_KEY', None):
            log.debug("set_page has natural key fields.")
            natural_key = page.get_natural_key(cache=self)
            if natural_key is not None:
                log.debug("set_page natural_key: %s", repr(natural_key))
                self.pages_by_natural_key[utils.freeze(natural_key)] = page.endpoint
        if 'results' in page:
            for p in page.results:
                self.set_page(p)
        return page

    def get_page(self, page):
        url = page.endpoint if isinstance(page, Page) else str(page)
        if url in self.pages_by_url:
            return self.pages_by_url[url]

        try:
            page = page.get(all_pages=True)
        except exc.Common:
            log.error("This endpoint raised an error: %s", url)
            return self.pages_by_url.setdefault(url, None)

        warning = page.r.headers.get('Warning', '')
        if '299' in warning and 'deprecated' in warning:
            log.warning("This endpoint is deprecated: %s", url)
            return self.pages_by_url.setdefault(url, None)

        log.debug("get_page: %s", page.endpoint)
        return self.set_page(page)

    def get_by_natural_key(self, natural_key):
        endpoint = self.pages_by_natural_key.get(utils.freeze(natural_key))
        log.debug("get_by_natural_key: %s, endpoint: %s", repr(natural_key), endpoint)
        if endpoint:
            return self.get_page(endpoint)
