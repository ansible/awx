import logging

import requests

from awxkit import exceptions as exc
from awxkit.config import config


log = logging.getLogger(__name__)


class ConnectionException(exc.Common):

    pass


class Token_Auth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer {0.token}'.format(self)
        return request


def log_elapsed(r, *args, **kwargs):  # requests hook to display API elapsed time
    log.debug('"{0.request.method} {0.url}" elapsed: {0.elapsed}'.format(r))


class Connection(object):
    """A requests.Session wrapper for establishing connection w/ AWX instance"""

    def __init__(self, server, verify=False):
        self.server = server
        self.verify = verify
        # Note: We use the old sessionid here incase someone is trying to connect to an older AWX version
        # There is a check below so that if AWX returns an X-API-Session-Cookie-Name we will grab it and
        # connect with the new session cookie name.
        self.session_cookie_name = 'sessionid'

        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        self.session = requests.Session()
        self.uses_session_cookie = False

    def get_session_requirements(self, next='/api/'):
        self.get('/api/')  # this causes a cookie w/ the CSRF token to be set
        return dict(next=next)

    def login(self, username=None, password=None, token=None, **kwargs):
        if username and password:
            _next = kwargs.get('next')
            if _next:
                headers = self.session.headers.copy()
                response = self.post('/api/login/', headers=headers, data=dict(username=username, password=password, next=_next))
                # The login causes a redirect so we need to search the history of the request to find the header
                for historical_response in response.history:
                    if 'X-API-Session-Cookie-Name' in historical_response.headers:
                        self.session_cookie_name = historical_response.headers.get('X-API-Session-Cookie-Name')

                self.session_id = self.session.cookies.get(self.session_cookie_name, None)
                self.uses_session_cookie = True
            else:
                self.session.auth = (username, password)
        elif token:
            self.session.auth = Token_Auth(token)
        else:
            self.session.auth = None

    def logout(self):
        if self.uses_session_cookie:
            self.session.cookies.pop(self.session_cookie_name, None)
        else:
            self.session.auth = None

    def request(self, relative_endpoint, method='get', json=None, data=None, query_parameters=None, headers=None):
        """Core requests.Session wrapper that returns requests.Response objects"""
        session_request_method = getattr(self.session, method, None)
        if not session_request_method:
            raise ConnectionException(message="Unknown request method: {0}".format(method))

        use_endpoint = relative_endpoint
        if self.server.endswith('/'):
            self.server = self.server[:-1]
        if use_endpoint.startswith('/'):
            use_endpoint = use_endpoint[1:]
        url = '/'.join([self.server, use_endpoint])

        kwargs = dict(verify=self.verify, params=query_parameters, json=json, data=data, hooks=dict(response=log_elapsed))

        if headers is not None:
            kwargs['headers'] = headers

        if method in ('post', 'put', 'patch', 'delete'):
            kwargs.setdefault('headers', {})['X-CSRFToken'] = self.session.cookies.get('csrftoken')
            kwargs['headers']['Referer'] = url

        for attempt in range(1, config.client_connection_attempts + 1):
            try:
                response = session_request_method(url, **kwargs)
                break
            except requests.exceptions.ConnectionError as err:
                if attempt == config.client_connection_attempts:
                    raise err
                log.exception('Failed to reach url: {0}.  Retrying.'.format(url))

        return response

    def delete(self, relative_endpoint):
        return self.request(relative_endpoint, method='delete')

    def get(self, relative_endpoint, query_parameters=None, headers=None):
        return self.request(relative_endpoint, method='get', query_parameters=query_parameters, headers=headers)

    def head(self, relative_endpoint):
        return self.request(relative_endpoint, method='head')

    def options(self, relative_endpoint):
        return self.request(relative_endpoint, method='options')

    def patch(self, relative_endpoint, json):
        return self.request(relative_endpoint, method='patch', json=json)

    def post(self, relative_endpoint, json=None, data=None, headers=None):
        return self.request(relative_endpoint, method='post', json=json, data=data, headers=headers)

    def put(self, relative_endpoint, json):
        return self.request(relative_endpoint, method='put', json=json)
