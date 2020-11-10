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
from awx.main.utils import get_awx_http_client_headers, set_environ

__all__ = ['register', 'gather', 'ship']


logger = logging.getLogger('awx.main.analytics')


def _valid_license():
    try:
        if get_license().get('license_type', 'UNLICENSED') == 'open':
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
    def _write_manifest(destdir, manifest):
        path = os.path.join(destdir, 'manifest.json')
        with open(path, 'w', encoding='utf-8') as f:
            try:
                json.dump(manifest, f)
            except Exception:
                f.close()
                os.remove(f.name)
                logger.exception("Could not generate manifest.json")

    last_run = since or settings.AUTOMATION_ANALYTICS_LAST_GATHER or (now() - timedelta(weeks=4))
    logger.debug("Last analytics run was: {}".format(settings.AUTOMATION_ANALYTICS_LAST_GATHER))
    
    if _valid_license() is False:
        logger.exception("Invalid License provided, or No License Provided")
        return None

    if collection_type != 'dry-run' and not settings.INSIGHTS_TRACKING_STATE:
        logger.error("Automation Analytics not enabled. Use --dry-run to gather locally without sending.")
        return None

    collector_list = []
    if module:
        collector_module = module
    else:
        from awx.main.analytics import collectors
        collector_module = collectors
    for name, func in inspect.getmembers(collector_module):
        if (
            inspect.isfunction(func) and
            hasattr(func, '__awx_analytics_key__') and
            (not subset or name in subset)
        ):
            collector_list.append((name, func))

    manifest = dict()
    dest = dest or tempfile.mkdtemp(prefix='awx_analytics')
    gather_dir = os.path.join(dest, 'stage')
    os.mkdir(gather_dir, 0o700)
    num_splits = 1
    for name, func in collector_list:
        if func.__awx_analytics_type__ == 'json':
            key = func.__awx_analytics_key__
            path = '{}.json'.format(os.path.join(gather_dir, key))
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
                files = func(last_run, full_path=gather_dir, until=until)
                if files:
                    manifest['{}.csv'.format(key)] = func.__awx_analytics_version__
                if len(files) > num_splits:
                    num_splits = len(files)
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
        config = collectors.config
        path = '{}.json'.format(os.path.join(gather_dir, config.__awx_analytics_key__))
        with open(path, 'w', encoding='utf-8') as f:
            try:
                json.dump(collectors.config(last_run), f)
                manifest['config.json'] = config.__awx_analytics_version__
            except Exception:
                logger.exception("Could not generate metric {}.json".format(key))
                f.close()
                os.remove(f.name)
                shutil.rmtree(dest)
                return None

    stage_dirs = [gather_dir]
    if num_splits > 1:
        for i in range(0, num_splits):
            split_path = os.path.join(dest, 'split{}'.format(i))
            os.mkdir(split_path, 0o700)
            filtered_manifest = {}
            shutil.copy(os.path.join(gather_dir, 'config.json'), split_path)
            filtered_manifest['config.json'] = manifest['config.json']
            suffix = '_split{}'.format(i)
            for file in os.listdir(gather_dir):
                if file.endswith(suffix):
                    old_file = os.path.join(gather_dir, file)
                    new_filename = file.replace(suffix, '')
                    new_file = os.path.join(split_path, new_filename)
                    shutil.move(old_file, new_file)
                    filtered_manifest[new_filename] = manifest[new_filename]
            _write_manifest(split_path, filtered_manifest)
            stage_dirs.append(split_path)

    for item in list(manifest.keys()):
        if not os.path.exists(os.path.join(gather_dir, item)):
            manifest.pop(item)
    _write_manifest(gather_dir, manifest)

    tarfiles = []
    try:
        for i in range(0, len(stage_dirs)):
            stage_dir = stage_dirs[i]
            # can't use isoformat() since it has colons, which GNU tar doesn't like
            tarname = '_'.join([
                settings.SYSTEM_UUID,
                until.strftime('%Y-%m-%d-%H%M%S%z'),
                str(i)
            ])
            tgz = shutil.make_archive(
                os.path.join(os.path.dirname(dest), tarname),
                'gztar',
                stage_dir
            )
            tarfiles.append(tgz)
    except Exception:
        shutil.rmtree(stage_dir, ignore_errors = True)
        logger.exception("Failed to write analytics archive file")
    finally:
        shutil.rmtree(dest, ignore_errors = True)
    return tarfiles


def ship(path):
    """
    Ship gathered metrics to the Insights API
    """
    if not path:
        logger.error('Automation Analytics TAR not found')
        return
    if not os.path.exists(path):
        logger.error('Automation Analytics TAR {} not found'.format(path))
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
    finally:
        # cleanup tar.gz
        if os.path.exists(path):
            os.remove(path)
