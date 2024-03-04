from contextlib import contextmanager, suppress

from awxkit import api, exceptions
from awxkit.config import config


__all__ = ('as_user', 'check_related', 'delete_all', 'uses_sessions')


def get_all(endpoint):
    results = []
    while True:
        get_args = dict(page_size=200) if 'page_size' not in endpoint else dict()
        resource = endpoint.get(**get_args)
        results.extend(resource.results)
        if not resource.next:
            return results
        endpoint = resource.next


def _delete_all(endpoint):
    while True:
        resource = endpoint.get()
        for item in resource.results:
            try:
                item.delete()
            except Exception as e:
                print(e)
        if not resource.next:
            return


def delete_all(v):
    for endpoint in (
        v.unified_jobs,
        v.job_templates,
        v.workflow_job_templates,
        v.notification_templates,
        v.projects,
        v.inventory,
        v.hosts,
        v.labels,
        v.credentials,
        v.teams,
        v.users,
        v.organizations,
        v.schedules,
    ):
        _delete_all(endpoint)


def check_related(resource):
    examined = []
    for related in resource.related.values():
        if related in examined:
            continue
        print(related)
        with suppress(exceptions.NotFound):
            child_related = related.get()
            examined.append(related)
            if 'results' in child_related and child_related.results:
                child_related = child_related.results.pop()
            if 'related' in child_related:
                for _related in child_related.related.values():
                    if not isinstance(_related, api.page.TentativePage) or _related in examined:
                        continue
                    print(_related)
                    with suppress(exceptions.NotFound):
                        _related.get()
                        examined.append(_related)


@contextmanager
def as_user(v, username, password=None):
    """Context manager to allow running tests as an alternative login user."""
    access_token = False
    if not isinstance(v, api.client.Connection):
        connection = v.connection
    else:
        connection = v

    if isinstance(username, api.User):
        password = username.password
        username = username.username

    if isinstance(username, api.OAuth2AccessToken):
        access_token = username.token
        username = None
        password = None

    try:
        if config.use_sessions:
            session_id = None
            domain = None
            # requests doesn't provide interface for retrieving
            # domain segregated cookies other than iterating.
            for cookie in connection.session.cookies:
                if cookie.name == connection.session_cookie_name:
                    session_id = cookie.value
                    domain = cookie.domain
                    break
            if session_id:
                del connection.session.cookies[connection.session_cookie_name]
            if access_token:
                kwargs = dict(token=access_token)
            else:
                kwargs = connection.get_session_requirements()
        else:
            previous_auth = connection.session.auth
            kwargs = dict()
        connection.login(username, password, **kwargs)
        yield
    finally:
        if config.use_sessions:
            if access_token:
                connection.session.auth = None
            del connection.session.cookies[connection.session_cookie_name]
            if session_id:
                connection.session.cookies.set(connection.session_cookie_name, session_id, domain=domain)
        else:
            connection.session.auth = previous_auth


def uses_sessions(connection):
    session_login = connection.get(f"{config.api_base_path}login/")
    return session_login.status_code == 200
