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


__all__ = ['register', 'gather', 'ship', 'table_version']


logger = logging.getLogger('awx.main.analytics')

manifest = dict()


def _valid_license():
    try:
        if get_license(show_key=False).get('license_type', 'UNLICENSED') == 'open':
            return False
        access_registry[Job](None).check_license()
    except PermissionDenied:
        logger.exception("A valid license was not found:")
        return False
    return True


def register(key, version):
    """
    A decorator used to register a function as a metric collector.

    Decorated functions should return JSON-serializable objects.

    @register('projects_by_scm_type', 1)
    def projects_by_scm_type():
        return {'git': 5, 'svn': 1, 'hg': 0}
    """

    def decorate(f):
        f.__awx_analytics_key__ = key
        f.__awx_analytics_version__ = version
        return f

    return decorate


def table_version(file_name, version):

    global manifest
    manifest[file_name] = version

    def decorate(f):
        return f

    return decorate


def gather(dest=None, module=None, collection_type='scheduled'):
    """
    Gather all defined metrics and write them as JSON files in a .tgz

    :param dest:    the (optional) absolute path to write a compressed tarball
    :pararm module: the module to search for registered analytic collector
                    functions; defaults to awx.main.analytics.collectors
    """

    run_now = now()
    state = TowerAnalyticsState.get_solo()
    last_run = state.last_run
    logger.debug("Last analytics run was: {}".format(last_run))
    
    max_interval = now() - timedelta(weeks=4)
    if last_run < max_interval or not last_run:
        last_run = max_interval

    if _valid_license() is False:
        logger.exception("Invalid License provided, or No License Provided")
        return "Error: Invalid License provided, or No License Provided"

    if collection_type != 'dry-run' and not settings.INSIGHTS_TRACKING_STATE:
        logger.error("Automation Analytics not enabled. Use --dry-run to gather locally without sending.")
        return

    if module is None:
        from awx.main.analytics import collectors
        module = collectors


    dest = dest or tempfile.mkdtemp(prefix='awx_analytics')
    for name, func in inspect.getmembers(module):
        if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__'):
            key = func.__awx_analytics_key__
            manifest['{}.json'.format(key)] = func.__awx_analytics_version__
            path = '{}.json'.format(os.path.join(dest, key))
            with open(path, 'w', encoding='utf-8') as f:
                try:
                    if func.__name__ == 'query_info':
                        json.dump(func(last_run, collection_type=collection_type), f)
                    else:
                        json.dump(func(last_run), f)
                except Exception:
                    logger.exception("Could not generate metric {}.json".format(key))
                    f.close()
                    os.remove(f.name)
    
    path = os.path.join(dest, 'manifest.json')
    with open(path, 'w', encoding='utf-8') as f:
        try:
            json.dump(manifest, f)
        except Exception:
            logger.exception("Could not generate manifest.json")
            f.close()
            os.remove(f.name)

    try:
        collectors.copy_tables(since=last_run, full_path=dest)
    except Exception:
        logger.exception("Could not copy tables")
        
    # can't use isoformat() since it has colons, which GNU tar doesn't like
    tarname = '_'.join([
        settings.SYSTEM_UUID,
        run_now.strftime('%Y-%m-%d-%H%M%S%z')
    ])
    tgz = shutil.make_archive(
        os.path.join(os.path.dirname(dest), tarname),
        'gztar',
        dest
    )
    shutil.rmtree(dest)
    return tgz


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
            response = requests.post(url, 
                                     files=files,
                                     verify="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
                                     auth=(rh_user, rh_password),
                                     timeout=(31, 31))
            if response.status_code != 202:
                return logger.exception('Upload failed with status {}, {}'.format(response.status_code,
                                                                                  response.text))
        run_now = now()
        state = TowerAnalyticsState.get_solo()
        state.last_run = run_now
        state.save()
    finally:
        # cleanup tar.gz
        os.remove(path)
