import inspect
import json
import logging
import os
import os.path
import tempfile
import shutil
import requests

from django.conf import settings
from django.utils.timezone import now, timedelta
from rest_framework.exceptions import PermissionDenied

from awx.conf.license import get_license
from awx.main.models import Job
from awx.main.access import access_registry
from awx.main.models.ha import TowerAnalyticsState
from awx.main.utils import get_awx_http_client_headers, set_environ

__all__ = ['register', 'gather', 'ship']


logger = logging.getLogger('awx.main.analytics')


def _valid_license():
    try:
        if get_license(show_key=False).get('license_type', 'UNLICENSED') == 'open':
            return False
        access_registry[Job](None).check_license()
    except PermissionDenied:
        logger.exception("A valid license was not found:")
        return False
    return True


def all_collectors():
    from awx.main.analytics import collectors

    collector_dict = {}
    module = collectors
    for name, func in inspect.getmembers(module):
        if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__'):
            key = func.__awx_analytics_key__
            desc = func.__awx_analytics_description__ or ''
            version = func.__awx_analytics_version__
            collector_dict[key] = { 'name': key, 'version': version, 'description': desc}
    return collector_dict


def expensive_collectors():
    from awx.main.analytics import collectors

    ret = []
    module = collectors
    for name, func in inspect.getmembers(module):
        if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__') and func.__awx_expensive__:
            ret.append(func.__awx_analytics_key__)
    return ret


def register(key, version, description=None, format='json', expensive=False):
    """
    A decorator used to register a function as a metric collector.

    Decorated functions should do the following based on format:
    - json: return JSON-serializable objects.
    - csv: write CSV data to a filename named 'key'

    @register('projects_by_scm_type', 1)
    def projects_by_scm_type():
        return {'git': 5, 'svn': 1, 'hg': 0}
    """

    def decorate(f):
        f.__awx_analytics_key__ = key
        f.__awx_analytics_version__ = version
        f.__awx_analytics_description__ = description
        f.__awx_analytics_type__ = format
        f.__awx_expensive__ = expensive
        return f

    return decorate


def gather(dest=None, module=None, subset = None, since = None, until = now(), collection_type='scheduled'):
    """
    Gather all defined metrics and write them as JSON files in a .tgz

    :param dest:    the (optional) absolute path to write a compressed tarball
    :param module: the module to search for registered analytic collector
                    functions; defaults to awx.main.analytics.collectors
    """

    run_now = now()
    state = TowerAnalyticsState.get_solo()
    last_run = state.last_run
    logger.debug("Last analytics run was: {}".format(last_run))
    
    max_interval = now() - timedelta(weeks=4)
    if last_run < max_interval or not last_run:
        last_run = max_interval
    if since:
        last_run = since
        logger.debug("Gathering overriden to start at: {}".format(since))

    if _valid_license() is False:
        logger.exception("Invalid License provided, or No License Provided")
        return "Error: Invalid License provided, or No License Provided"

    if collection_type != 'dry-run' and not settings.INSIGHTS_TRACKING_STATE:
        logger.error("Automation Analytics not enabled. Use --dry-run to gather locally without sending.")
        return

    collector_list = []
    if module is None:
        from awx.main.analytics import collectors
        module = collectors
    for name, func in inspect.getmembers(module):
        if (
            inspect.isfunction(func) and
            hasattr(func, '__awx_analytics_key__') and
            (not subset or name in subset)
        ):
            collector_list.append((name, func))

    manifest = dict()
    dest = dest or tempfile.mkdtemp(prefix='awx_analytics')
    for name, func in collector_list:
        if func.__awx_analytics_type__ == 'json':
            key = func.__awx_analytics_key__
            path = '{}.json'.format(os.path.join(dest, key))
            with open(path, 'w', encoding='utf-8') as f:
                try:
                    json.dump(func(last_run, collection_type=collection_type, until=until), f)
                    manifest['{}.json'.format(key)] = func.__awx_analytics_version__
                except Exception:
                    logger.exception("Could not generate metric {}.json".format(key))
                    f.close()
                    os.remove(f.name)
        elif func.__awx_analytics_type__ == 'csv':
            key = func.__awx_analytics_key__
            try:
                if func(last_run, full_path=dest, until=until):
                    manifest['{}.csv'.format(key)] = func.__awx_analytics_version__
            except Exception:
                logger.exception("Could not generate metric {}.csv".format(key))

    if not manifest:
        # No data was collected
        logger.warning("No data from {} to {}".format(last_run, until))
        shutil.rmtree(dest)
        return None

    # Always include config.json if we're using our collectors
    if 'config.json' not in manifest.keys() and not module:
        from awx.main.analytics import collectors
        path = '{}.json'.format(os.path.join(dest, key))
        with open(path, 'w', encoding='utf-8') as f:
            try:
                json.dump(collectors.config(last_run), f)
                manifest['config.json'] = collectors.config.__awx_analytics_version__
            except Exception:
                logger.exception("Could not generate metric {}.json".format(key))
                f.close()
                os.remove(f.name)
                shutil.rmtree(dest)
                return None

    path = os.path.join(dest, 'manifest.json')
    with open(path, 'w', encoding='utf-8') as f:
        try:
            json.dump(manifest, f)
        except Exception:
            logger.exception("Could not generate manifest.json")
            f.close()
            os.remove(f.name)

    # can't use isoformat() since it has colons, which GNU tar doesn't like
    tarname = '_'.join([
        settings.SYSTEM_UUID,
        run_now.strftime('%Y-%m-%d-%H%M%S%z')
    ])
    try:
        tgz = shutil.make_archive(
            os.path.join(os.path.dirname(dest), tarname),
            'gztar',
            dest
        )
        return tgz
    except Exception:
        logger.exception("Failed to write analytics archive file")
    finally: 
        shutil.rmtree(dest)


def ship(path):
    """
    Ship gathered metrics to the Insights API
    """
    if not path:
        logger.error('Automation Analytics TAR not found')
        return
    if "Error:" in str(path):
        return
    try:
        logger.debug('shipping analytics file: {}'.format(path))
        url = getattr(settings, 'AUTOMATION_ANALYTICS_URL', None)
        if not url:
            logger.error('AUTOMATION_ANALYTICS_URL is not set')
            return
        rh_user = getattr(settings, 'REDHAT_USERNAME', None)
        rh_password = getattr(settings, 'REDHAT_PASSWORD', None)
        if not rh_user:
            return logger.error('REDHAT_USERNAME is not set')
        if not rh_password:
            return logger.error('REDHAT_PASSWORD is not set')
        with open(path, 'rb') as f:
            files = {'file': (os.path.basename(path), f, settings.INSIGHTS_AGENT_MIME)}
            s = requests.Session()
            s.headers = get_awx_http_client_headers()
            s.headers.pop('Content-Type')
            with set_environ(**settings.AWX_TASK_ENV):
                response = s.post(url,
                                  files=files,
                                  verify="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
                                  auth=(rh_user, rh_password),
                                  headers=s.headers,
                                  timeout=(31, 31))
            # Accept 2XX status_codes
            if response.status_code >= 300:
                return logger.exception('Upload failed with status {}, {}'.format(response.status_code,
                                                                                  response.text))
        run_now = now()
        state = TowerAnalyticsState.get_solo()
        state.last_run = run_now
        state.save()
    finally:
        # cleanup tar.gz
        os.remove(path)
