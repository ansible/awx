import inspect
import io
import json
import logging
import os
import os.path
import pathlib
import shutil
import tarfile
import tempfile

from django.conf import settings
from django.utils.timezone import now, timedelta
from rest_framework.exceptions import PermissionDenied
import requests

from awx.conf.license import get_license
from awx.main.models import Job
from awx.main.access import access_registry
from awx.main.utils import get_awx_http_client_headers, set_environ
from awx.main.utils.pglock import advisory_lock

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

    return {
        func.__awx_analytics_key__: {
            'name': func.__awx_analytics_key__,
            'version': func.__awx_analytics_version__,
            'description': func.__awx_analytics_description__ or '',
        }
        for name, func in inspect.getmembers(collectors)
        if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__')
    }


def register(key, version, description=None, format='json', expensive=None):
    """
    A decorator used to register a function as a metric collector.

    Decorated functions should do the following based on format:
    - json: return JSON-serializable objects.
    - csv: write CSV data to a filename named 'key'

    @register('projects_by_scm_type', 1)
    def projects_by_scm_type():
        return {'git': 5, 'svn': 1}
    """

    def decorate(f):
        f.__awx_analytics_key__ = key
        f.__awx_analytics_version__ = version
        f.__awx_analytics_description__ = description
        f.__awx_analytics_type__ = format
        f.__awx_expensive__ = expensive
        return f

    return decorate


def package(target, data, timestamp):
    try:
        tarname_base = f'{settings.SYSTEM_UUID}-{timestamp.strftime("%Y-%m-%d-%H%M%S%z")}'
        path = pathlib.Path(target)
        index = len(list(path.glob(f'{tarname_base}-*.*')))
        tarname = f'{tarname_base}-{index}.tar.gz'

        manifest = {}
        with tarfile.open(target.joinpath(tarname), 'w:gz') as f:
            for name, (item, version) in data.items():
                manifest[name] = version
                if isinstance(item, str):
                    info = f.gettarinfo(item, arcname=name)
                    f.addfile(info)
                else:
                    info = tarfile.TarInfo(name)
                    fileobj = io.BytesIO(json.dumps(item).encode('utf-8'))
                    fileobj.size = len(fileobj.getvalue())
                    f.addfile(info, fileobj=fileobj)

            info = tarfile.TarInfo('manifest.json')
            fileobj = io.BytesIO(json.dumps(manifest).encode('utf-8'))
            fileobj.size = len(fileobj.getvalue())
            f.addfile(info, fileobj=fileobj)

        return f.name
    except Exception:
        logger.exception("Failed to write analytics archive file")
        return None


def gather(dest=None, module=None, subset=None, since=None, until=None, collection_type='scheduled'):
    """
    Gather all defined metrics and write them as JSON files in a .tgz

    :param dest:   the (optional) absolute path to write a compressed tarball
    :param module: the module to search for registered analytic collector
                   functions; defaults to awx.main.analytics.collectors
    """
    log_level = logging.ERROR if collection_type != 'scheduled' else logging.DEBUG

    if not _valid_license():
        logger.log(log_level, "Invalid License provided, or No License Provided")
        return None

    if collection_type != 'dry-run':
        if not settings.INSIGHTS_TRACKING_STATE:
            logger.log(log_level, "Automation Analytics not enabled. Use --dry-run to gather locally without sending.")
            return None

        if not (settings.AUTOMATION_ANALYTICS_URL and settings.REDHAT_USERNAME and settings.REDHAT_PASSWORD):
            logger.log(log_level, "Not gathering analytics, configuration is invalid")
            return None

    with advisory_lock('gather_analytics_lock', wait=False) as acquired:
        if not acquired:
            logger.log(log_level, "Not gathering analytics, another task holds lock")
            return None

        from awx.conf.models import Setting
        from awx.main.analytics import collectors
        from awx.main.signals import disable_activity_stream

        if until is None:
            until = now()
        last_run = since or settings.AUTOMATION_ANALYTICS_LAST_GATHER or (until - timedelta(weeks=4))
        last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
        last_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}')
        logger.debug("Last analytics run was: {}".format(settings.AUTOMATION_ANALYTICS_LAST_GATHER))

        collector_module = module if module else collectors
        collector_list = [
            func
            for name, func in inspect.getmembers(collector_module)
            if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__') and (not subset or name in subset)
        ]
        if collection_type != 'dry-run' and not any(c.__awx_analytics_key__ == 'config' for c in collector_list):
            # In order to ship to analytics, we must include the output of the built-in 'config' collector.
            collector_list.append(collectors.config)

        json_collectors = [func for func in collector_list if func.__awx_analytics_type__ == 'json']
        csv_collectors = [func for func in collector_list if func.__awx_analytics_type__ == 'csv']

        dest = pathlib.Path(dest or tempfile.mkdtemp(prefix='awx_analytics'))
        gather_dir = dest.joinpath('stage')
        gather_dir.mkdir(mode=0o700)
        tarfiles = []

        # These json collectors are pretty compact, so collect all of them before shipping to analytics.
        data = {}
        for func in json_collectors:
            key = func.__awx_analytics_key__
            filename = f'{key}.json'
            try:
                data[filename] = (func(last_run, collection_type=collection_type, until=until), func.__awx_analytics_version__)
            except Exception:
                logger.exception("Could not generate metric {}".format(filename))
        if data:
            tgzfile = package(dest.parent, data, until)
            if tgzfile is not None:
                tarfiles.append(tgzfile)

                if collection_type != 'dry-run':
                    if data.get('config.json') is None:
                        logger.error("'config' collector data is missing, and is required to ship.")
                        return None
                    ship(tgzfile)
                    with disable_activity_stream():
                        for filename in data:
                            last_entries[filename.replace('.json', '')] = until
                        settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries)

        for func in csv_collectors:
            key = func.__awx_analytics_key__
            filename = f'{key}.csv'
            try:
                slices = [(last_run, until)]
                if func.__awx_expensive__:
                    slices = func.__awx_expensive__(key, last_run, until)  # it's ok if this returns a generator
                for start, end in slices:
                    files = func(start, full_path=gather_dir, until=end)

                    if not files:
                        continue
                    for fpath in files:
                        payload = {filename: (fpath, func.__awx_analytics_version__)}
                        if collection_type != 'dry-run':
                            payload['config.json'] = data.get('config.json')
                            if payload['config.json'] is None:
                                logger.error("'config' collector data is missing, and is required to ship.")
                                return None
                        tgzfile = package(dest.parent, payload, until)
                        if tgzfile is not None:
                            tarfiles.append(tgzfile)

                            if collection_type != 'dry-run':
                                ship(tgzfile)
                                with disable_activity_stream():
                                    last_entries[key] = end
                                    settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries)
            except Exception:
                logger.exception("Could not generate metric {}".format(filename))

        with disable_activity_stream():
            settings.AUTOMATION_ANALYTICS_LAST_GATHER = until

        shutil.rmtree(dest, ignore_errors=True)  # clean up individual artifact files
        if not tarfiles:
            # No data was collected
            logger.warning("No data from {} to {}".format(last_run, until))
            return None

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
                response = s.post(
                    url,
                    files=files,
                    verify="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
                    auth=(rh_user, rh_password),
                    headers=s.headers,
                    timeout=(31, 31),
                )
            # Accept 2XX status_codes
            if response.status_code >= 300:
                return logger.exception('Upload failed with status {}, {}'.format(response.status_code, response.text))
    finally:
        # cleanup tar.gz
        if os.path.exists(path):
            os.remove(path)
