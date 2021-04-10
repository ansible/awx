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
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now, timedelta
from rest_framework.exceptions import PermissionDenied
import requests

from awx.conf.license import get_license
from awx.main.models import Job
from awx.main.access import access_registry
from awx.main.utils import get_awx_http_client_headers, set_environ, datetime_hook
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
                try:
                    if isinstance(item, str):
                        f.add(item, arcname=f'./{name}')
                    else:
                        buf = json.dumps(item).encode('utf-8')
                        info = tarfile.TarInfo(f'./{name}')
                        info.size = len(buf)
                        info.mtime = timestamp.timestamp()
                        f.addfile(info, fileobj=io.BytesIO(buf))
                    manifest[name] = version
                except Exception:
                    logger.exception(f"Could not generate metric {name}")
                    return None

            try:
                buf = json.dumps(manifest).encode('utf-8')
                info = tarfile.TarInfo('./manifest.json')
                info.size = len(buf)
                info.mtime = timestamp.timestamp()
                f.addfile(info, fileobj=io.BytesIO(buf))
            except Exception:
                logger.exception("Could not generate manifest.json")
                return None

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
            logger.log(log_level, "Not gathering analytics, configuration is invalid. Use --dry-run to gather locally without sending.")
            return None

    with advisory_lock('gather_analytics_lock', wait=False) as acquired:
        if not acquired:
            logger.log(log_level, "Not gathering analytics, another task holds lock")
            return None

        from awx.conf.models import Setting
        from awx.main.analytics import collectors
        from awx.main.signals import disable_activity_stream

        _now = now()

        # Make sure that the endpoints are not in the future.
        until = None if until is None else min(until, _now)
        since = None if since is None else min(since, _now)

        if since and not until:
            # If `since` is explicit but not `until`, `since` should be used to calculate the 4-week limit
            until = min(since + timedelta(weeks=4), _now)
        else:
            until = _now if until is None else until

        horizon = until - timedelta(weeks=4)
        if since is not None:
            # Make sure the start isn't more than 4 weeks prior to `until`.
            since = max(since, horizon)

        if since and since >= until:
            logger.warning("Start of the collection interval is later than the end, ignoring request.")
            return None

        logger.debug("Last analytics run was: {}".format(settings.AUTOMATION_ANALYTICS_LAST_GATHER))
        # LAST_GATHER time should always get truncated to less than 4 weeks back.
        last_gather = max(settings.AUTOMATION_ANALYTICS_LAST_GATHER or horizon, horizon)

        last_entries = Setting.objects.filter(key='AUTOMATION_ANALYTICS_LAST_ENTRIES').first()
        last_entries = json.loads((last_entries.value if last_entries is not None else '') or '{}', object_hook=datetime_hook)

        collector_module = module if module else collectors
        collector_list = [
            func
            for name, func in inspect.getmembers(collector_module)
            if inspect.isfunction(func) and hasattr(func, '__awx_analytics_key__') and (not subset or name in subset)
        ]
        if not any(c.__awx_analytics_key__ == 'config' for c in collector_list):
            # In order to ship to analytics, we must include the output of the built-in 'config' collector.
            collector_list.append(collectors.config)

        json_collectors = [func for func in collector_list if func.__awx_analytics_type__ == 'json']
        csv_collectors = [func for func in collector_list if func.__awx_analytics_type__ == 'csv']

        dest = pathlib.Path(dest or tempfile.mkdtemp(prefix='awx_analytics'))
        gather_dir = dest.joinpath('stage')
        gather_dir.mkdir(mode=0o700)
        tarfiles = []
        succeeded = True

        # These json collectors are pretty compact, so collect all of them before shipping to analytics.
        data = {}
        for func in json_collectors:
            key = func.__awx_analytics_key__
            filename = f'{key}.json'
            try:
                last_entry = max(last_entries.get(key) or last_gather, horizon)
                results = (func(since or last_entry, collection_type=collection_type, until=until), func.__awx_analytics_version__)
                json.dumps(results)  # throwaway check to see if the data is json-serializable
                data[filename] = results
            except Exception:
                logger.exception("Could not generate metric {}".format(filename))
        if data:
            if data.get('config.json') is None:
                logger.error("'config' collector data is missing.")
                return None

            tgzfile = package(dest.parent, data, until)
            if tgzfile is not None:
                tarfiles.append(tgzfile)
                if collection_type != 'dry-run':
                    if ship(tgzfile):
                        with disable_activity_stream():
                            for filename in data:
                                key = filename.replace('.json', '')
                                last_entries[key] = max(last_entries[key], until) if last_entries.get(key) else until
                            settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
                    else:
                        succeeded = False

        for func in csv_collectors:
            key = func.__awx_analytics_key__
            filename = f'{key}.csv'
            try:
                # These slicer functions may return a generator. The `since` parameter is
                # allowed to be None, and will fall back to LAST_ENTRIES[key] or to
                # LAST_GATHER (truncated appropriately to match the 4-week limit).
                if func.__awx_expensive__:
                    slices = func.__awx_expensive__(key, since, until)
                else:
                    slices = collectors.trivial_slicing(key, since, until)

                for start, end in slices:
                    files = func(start, full_path=gather_dir, until=end)

                    if not files:
                        if collection_type != 'dry-run':
                            with disable_activity_stream():
                                last_entries[key] = max(last_entries[key], end) if last_entries.get(key) else end
                                settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
                        continue

                    slice_succeeded = True
                    for fpath in files:
                        payload = {filename: (fpath, func.__awx_analytics_version__)}

                        payload['config.json'] = data.get('config.json')
                        if payload['config.json'] is None:
                            logger.error("'config' collector data is missing, and is required to ship.")
                            return None

                        tgzfile = package(dest.parent, payload, until)
                        if tgzfile is not None:
                            tarfiles.append(tgzfile)
                            if not ship(tgzfile):
                                slice_succeeded, succeeded = False, False
                                break

                    if slice_succeeded and collection_type != 'dry-run':
                        with disable_activity_stream():
                            last_entries[key] = max(last_entries[key], end) if last_entries.get(key) else end
                            settings.AUTOMATION_ANALYTICS_LAST_ENTRIES = json.dumps(last_entries, cls=DjangoJSONEncoder)
            except Exception:
                succeeded = False
                logger.exception("Could not generate metric {}".format(filename))

        if collection_type != 'dry-run':
            if succeeded:
                for fpath in tarfiles:
                    if os.path.exists(fpath):
                        os.remove(fpath)
            with disable_activity_stream():
                if not settings.AUTOMATION_ANALYTICS_LAST_GATHER or until > settings.AUTOMATION_ANALYTICS_LAST_GATHER:
                    settings.AUTOMATION_ANALYTICS_LAST_GATHER = until

        shutil.rmtree(dest, ignore_errors=True)  # clean up individual artifact files
        if not tarfiles:
            # No data was collected
            logger.warning("No data from {} to {}".format(since or last_gather, until))
            return None

        return tarfiles


def ship(path):
    """
    Ship gathered metrics to the Insights API
    """
    if not path:
        logger.error('Automation Analytics TAR not found')
        return False
    if not os.path.exists(path):
        logger.error('Automation Analytics TAR {} not found'.format(path))
        return False
    if "Error:" in str(path):
        return False

    logger.debug('shipping analytics file: {}'.format(path))
    url = getattr(settings, 'AUTOMATION_ANALYTICS_URL', None)
    if not url:
        logger.error('AUTOMATION_ANALYTICS_URL is not set')
        return False
    rh_user = getattr(settings, 'REDHAT_USERNAME', None)
    rh_password = getattr(settings, 'REDHAT_PASSWORD', None)
    if not rh_user:
        logger.error('REDHAT_USERNAME is not set')
        return False
    if not rh_password:
        logger.error('REDHAT_PASSWORD is not set')
        return False
    with open(path, 'rb') as f:
        files = {'file': (os.path.basename(path), f, settings.INSIGHTS_AGENT_MIME)}
        s = requests.Session()
        s.headers = get_awx_http_client_headers()
        s.headers.pop('Content-Type')
        with set_environ(**settings.AWX_TASK_ENV):
            response = s.post(
                url, files=files, verify="/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", auth=(rh_user, rh_password), headers=s.headers, timeout=(31, 31)
            )
        # Accept 2XX status_codes
        if response.status_code >= 300:
            logger.error('Upload failed with status {}, {}'.format(response.status_code, response.text))
            return False

        return True
