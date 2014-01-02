import cgi
import email.utils
import hashlib
import getpass
import mimetypes
import os
import platform
import re
import shutil
import sys
import tempfile

import pip

from pip.backwardcompat import urllib, urlparse, raw_input
from pip.exceptions import InstallationError, HashMismatch
from pip.util import (splitext, rmtree, format_size, display_path,
                      backup_dir, ask_path_exists, unpack_file,
                      create_download_cache_folder, cache_download)
from pip.vcs import vcs
from pip.log import logger
from pip._vendor import requests
from pip._vendor.requests.adapters import BaseAdapter
from pip._vendor.requests.auth import AuthBase, HTTPBasicAuth
from pip._vendor.requests.exceptions import InvalidURL
from pip._vendor.requests.models import Response
from pip._vendor.requests.structures import CaseInsensitiveDict

__all__ = ['get_file_content',
           'is_url', 'url_to_path', 'path_to_url',
           'is_archive_file', 'unpack_vcs_link',
           'unpack_file_url', 'is_vcs_url', 'is_file_url', 'unpack_http_url']


def user_agent():
    """Return a string representing the user agent."""
    _implementation = platform.python_implementation()

    if _implementation == 'CPython':
        _implementation_version = platform.python_version()
    elif _implementation == 'PyPy':
        _implementation_version = '%s.%s.%s' % (sys.pypy_version_info.major,
                                                sys.pypy_version_info.minor,
                                                sys.pypy_version_info.micro)
        if sys.pypy_version_info.releaselevel != 'final':
            _implementation_version = ''.join([
                _implementation_version,
                sys.pypy_version_info.releaselevel,
            ])
    elif _implementation == 'Jython':
        _implementation_version = platform.python_version()  # Complete Guess
    elif _implementation == 'IronPython':
        _implementation_version = platform.python_version()  # Complete Guess
    else:
        _implementation_version = 'Unknown'

    try:
        p_system = platform.system()
        p_release = platform.release()
    except IOError:
        p_system = 'Unknown'
        p_release = 'Unknown'

    return " ".join(['pip/%s' % pip.__version__,
                     '%s/%s' % (_implementation, _implementation_version),
                     '%s/%s' % (p_system, p_release)])


class MultiDomainBasicAuth(AuthBase):

    def __init__(self, prompting=True):
        self.prompting = prompting
        self.passwords = {}

    def __call__(self, req):
        parsed = urlparse.urlparse(req.url)

        # Get the netloc without any embedded credentials
        netloc = parsed.netloc.split("@", 1)[-1]

        # Set the url of the request to the url without any credentials
        req.url = urlparse.urlunparse(parsed[:1] + (netloc,) + parsed[2:])

        # Use any stored credentials that we have for this netloc
        username, password = self.passwords.get(netloc, (None, None))

        # Extract credentials embedded in the url if we have none stored
        if username is None:
            username, password = self.parse_credentials(parsed.netloc)

        if username or password:
            # Store the username and password
            self.passwords[netloc] = (username, password)

            # Send the basic auth with this request
            req = HTTPBasicAuth(username or "", password or "")(req)

        # Attach a hook to handle 401 responses
        req.register_hook("response", self.handle_401)

        return req

    def handle_401(self, resp, **kwargs):
        # We only care about 401 responses, anything else we want to just
        #   pass through the actual response
        if resp.status_code != 401:
            return resp

        # We are not able to prompt the user so simple return the response
        if not self.prompting:
            return resp

        parsed = urlparse.urlparse(resp.url)

        # Prompt the user for a new username and password
        username = raw_input("User for %s: " % parsed.netloc)
        password = getpass.getpass("Password: ")

        # Store the new username and password to use for future requests
        if username or password:
            self.passwords[parsed.netloc] = (username, password)

        # Consume content and release the original connection to allow our new
        #   request to reuse the same one.
        resp.content
        resp.raw.release_conn()

        # Add our new username and password to the request
        req = HTTPBasicAuth(username or "", password or "")(resp.request)

        # Send our new request
        new_resp = resp.connection.send(req, **kwargs)
        new_resp.history.append(resp)

        return new_resp

    def parse_credentials(self, netloc):
        if "@" in netloc:
            userinfo = netloc.rsplit("@", 1)[0]
            if ":" in userinfo:
                return userinfo.split(":", 1)
            return userinfo, None
        return None, None


class LocalFSResponse(object):

    def __init__(self, fileobj):
        self.fileobj = fileobj

    def __getattr__(self, name):
        return getattr(self.fileobj, name)

    def read(self, amt=None, decode_content=None, cache_content=False):
        return self.fileobj.read(amt)

    # Insert Hacks to Make Cookie Jar work w/ Requests
    @property
    def _original_response(self):
        class FakeMessage(object):
            def getheaders(self, header):
                return []

            def get_all(self, header, default):
                return []

        class FakeResponse(object):
            @property
            def msg(self):
                return FakeMessage()

        return FakeResponse()


class LocalFSAdapter(BaseAdapter):

    def send(self, request, stream=None, timeout=None, verify=None, cert=None,
             proxies=None):
        parsed_url = urlparse.urlparse(request.url)

        # We only work for requests with a host of localhost
        if parsed_url.netloc.lower() != "localhost":
            raise InvalidURL("Invalid URL %r: Only localhost is allowed" %
                request.url)

        real_url = urlparse.urlunparse(parsed_url[:1] + ("",) + parsed_url[2:])
        pathname = url_to_path(real_url)

        resp = Response()
        resp.status_code = 200
        resp.url = real_url

        stats = os.stat(pathname)
        modified = email.utils.formatdate(stats.st_mtime, usegmt=True)
        resp.headers = CaseInsensitiveDict({
            "Content-Type": mimetypes.guess_type(pathname)[0] or "text/plain",
            "Content-Length": stats.st_size,
            "Last-Modified": modified,
        })

        resp.raw = LocalFSResponse(open(pathname, "rb"))
        resp.close = resp.raw.close

        return resp

    def close(self):
        pass


class PipSession(requests.Session):

    timeout = None

    def __init__(self, *args, **kwargs):
        super(PipSession, self).__init__(*args, **kwargs)

        # Attach our User Agent to the request
        self.headers["User-Agent"] = user_agent()

        # Attach our Authentication handler to the session
        self.auth = MultiDomainBasicAuth()

        # Enable file:// urls
        self.mount("file://", LocalFSAdapter())

    def request(self, method, url, *args, **kwargs):
        # Make file:// urls not fail due to lack of a hostname
        parsed = urlparse.urlparse(url)
        if parsed.scheme == "file":
            url = urlparse.urlunparse(parsed[:1] + ("localhost",) + parsed[2:])

        # Allow setting a default timeout on a session
        kwargs.setdefault("timeout", self.timeout)

        # Dispatch the actual request
        return super(PipSession, self).request(method, url, *args, **kwargs)


def get_file_content(url, comes_from=None, session=None):
    """Gets the content of a file; it may be a filename, file: URL, or
    http: URL.  Returns (location, content).  Content is unicode."""
    if session is None:
        session = PipSession()

    match = _scheme_re.search(url)
    if match:
        scheme = match.group(1).lower()
        if (scheme == 'file' and comes_from
            and comes_from.startswith('http')):
            raise InstallationError(
                'Requirements file %s references URL %s, which is local'
                % (comes_from, url))
        if scheme == 'file':
            path = url.split(':', 1)[1]
            path = path.replace('\\', '/')
            match = _url_slash_drive_re.match(path)
            if match:
                path = match.group(1) + ':' + path.split('|', 1)[1]
            path = urllib.unquote(path)
            if path.startswith('/'):
                path = '/' + path.lstrip('/')
            url = path
        else:
            ## FIXME: catch some errors
            resp = session.get(url)
            resp.raise_for_status()
            return resp.url, resp.text
    try:
        f = open(url)
        content = f.read()
    except IOError:
        e = sys.exc_info()[1]
        raise InstallationError('Could not open requirements file: %s' % str(e))
    else:
        f.close()
    return url, content


_scheme_re = re.compile(r'^(http|https|file):', re.I)
_url_slash_drive_re = re.compile(r'/*([a-z])\|', re.I)


def is_url(name):
    """Returns true if the name looks like a URL"""
    if ':' not in name:
        return False
    scheme = name.split(':', 1)[0].lower()
    return scheme in ['http', 'https', 'file', 'ftp'] + vcs.all_schemes


def url_to_path(url):
    """
    Convert a file: URL to a path.
    """
    assert url.startswith('file:'), (
        "You can only turn file: urls into filenames (not %r)" % url)
    path = url[len('file:'):].lstrip('/')
    path = urllib.unquote(path)
    if _url_drive_re.match(path):
        path = path[0] + ':' + path[2:]
    else:
        path = '/' + path
    return path


_drive_re = re.compile('^([a-z]):', re.I)
_url_drive_re = re.compile('^([a-z])[:|]', re.I)


def path_to_url(path):
    """
    Convert a path to a file: URL.  The path will be made absolute and have
    quoted path parts.
    """
    path = os.path.normpath(os.path.abspath(path))
    drive, path = os.path.splitdrive(path)
    filepath = path.split(os.path.sep)
    url = '/'.join([urllib.quote(part) for part in filepath])
    if not drive:
        url = url.lstrip('/')
    return 'file:///' + drive + url


def is_archive_file(name):
    """Return True if `name` is a considered as an archive file."""
    archives = ('.zip', '.tar.gz', '.tar.bz2', '.tgz', '.tar', '.pybundle',
               '.whl')
    ext = splitext(name)[1].lower()
    if ext in archives:
        return True
    return False


def unpack_vcs_link(link, location, only_download=False):
    vcs_backend = _get_used_vcs_backend(link)
    if only_download:
        vcs_backend.export(location)
    else:
        vcs_backend.unpack(location)


def unpack_file_url(link, location):
    source = url_to_path(link.url)
    content_type = mimetypes.guess_type(source)[0]
    if os.path.isdir(source):
        # delete the location since shutil will create it again :(
        if os.path.isdir(location):
            rmtree(location)
        shutil.copytree(source, location, symlinks=True)
    else:
        unpack_file(source, location, content_type, link)


def _get_used_vcs_backend(link):
    for backend in vcs.backends:
        if link.scheme in backend.schemes:
            vcs_backend = backend(link.url)
            return vcs_backend


def is_vcs_url(link):
    return bool(_get_used_vcs_backend(link))


def is_file_url(link):
    return link.url.lower().startswith('file:')


def _check_hash(download_hash, link):
    if download_hash.digest_size != hashlib.new(link.hash_name).digest_size:
        logger.fatal("Hash digest size of the package %d (%s) doesn't match the expected hash name %s!"
                    % (download_hash.digest_size, link, link.hash_name))
        raise HashMismatch('Hash name mismatch for package %s' % link)
    if download_hash.hexdigest() != link.hash:
        logger.fatal("Hash of the package %s (%s) doesn't match the expected hash %s!"
                     % (link, download_hash.hexdigest(), link.hash))
        raise HashMismatch('Bad %s hash for package %s' % (link.hash_name, link))


def _get_hash_from_file(target_file, link):
    try:
        download_hash = hashlib.new(link.hash_name)
    except (ValueError, TypeError):
        logger.warn("Unsupported hash name %s for package %s" % (link.hash_name, link))
        return None

    fp = open(target_file, 'rb')
    while True:
        chunk = fp.read(4096)
        if not chunk:
            break
        download_hash.update(chunk)
    fp.close()
    return download_hash


def _download_url(resp, link, temp_location):
    fp = open(temp_location, 'wb')
    download_hash = None
    if link.hash and link.hash_name:
        try:
            download_hash = hashlib.new(link.hash_name)
        except ValueError:
            logger.warn("Unsupported hash name %s for package %s" % (link.hash_name, link))
    try:
        total_length = int(resp.headers['content-length'])
    except (ValueError, KeyError, TypeError):
        total_length = 0
    downloaded = 0
    show_progress = total_length > 40 * 1000 or not total_length
    show_url = link.show_url
    try:
        if show_progress:
            ## FIXME: the URL can get really long in this message:
            if total_length:
                logger.start_progress('Downloading %s (%s): ' % (show_url, format_size(total_length)))
            else:
                logger.start_progress('Downloading %s (unknown size): ' % show_url)
        else:
            logger.notify('Downloading %s' % show_url)
        logger.info('Downloading from URL %s' % link)

        for chunk in resp.iter_content(4096):
            downloaded += len(chunk)
            if show_progress:
                if not total_length:
                    logger.show_progress('%s' % format_size(downloaded))
                else:
                    logger.show_progress('%3i%%  %s' % (100 * downloaded / total_length, format_size(downloaded)))
            if download_hash is not None:
                download_hash.update(chunk)
            fp.write(chunk)
        fp.close()
    finally:
        if show_progress:
            logger.end_progress('%s downloaded' % format_size(downloaded))
    return download_hash


def _copy_file(filename, location, content_type, link):
    copy = True
    download_location = os.path.join(location, link.filename)
    if os.path.exists(download_location):
        response = ask_path_exists(
            'The file %s exists. (i)gnore, (w)ipe, (b)ackup ' %
            display_path(download_location), ('i', 'w', 'b'))
        if response == 'i':
            copy = False
        elif response == 'w':
            logger.warn('Deleting %s' % display_path(download_location))
            os.remove(download_location)
        elif response == 'b':
            dest_file = backup_dir(download_location)
            logger.warn('Backing up %s to %s'
                        % (display_path(download_location), display_path(dest_file)))
            shutil.move(download_location, dest_file)
    if copy:
        shutil.copy(filename, download_location)
        logger.indent -= 2
        logger.notify('Saved %s' % display_path(download_location))


def unpack_http_url(link, location, download_cache, download_dir=None,
                    session=None):
    if session is None:
        session = PipSession()

    temp_dir = tempfile.mkdtemp('-unpack', 'pip-')
    temp_location = None
    target_url = link.url.split('#', 1)[0]

    already_cached = False
    cache_file = None
    cache_content_type_file = None
    download_hash = None
    if download_cache:
        cache_file = os.path.join(download_cache,
                                   urllib.quote(target_url, ''))
        cache_content_type_file = cache_file + '.content-type'
        already_cached = (
            os.path.exists(cache_file) and
            os.path.exists(cache_content_type_file)
            )
        if not os.path.isdir(download_cache):
            create_download_cache_folder(download_cache)

    already_downloaded = None
    if download_dir:
        already_downloaded = os.path.join(download_dir, link.filename)
        if not os.path.exists(already_downloaded):
            already_downloaded = None

    if already_downloaded:
        temp_location = already_downloaded
        content_type = mimetypes.guess_type(already_downloaded)[0]
        logger.notify('File was already downloaded %s' % already_downloaded)
        if link.hash:
            download_hash = _get_hash_from_file(temp_location, link)
            try:
                _check_hash(download_hash, link)
            except HashMismatch:
                logger.warn(
                    'Previously-downloaded file %s has bad hash, '
                    're-downloading.' % temp_location
                    )
                temp_location = None
                os.unlink(already_downloaded)
                already_downloaded = None

    # We have a cached file, and we haven't already found a good downloaded copy
    if already_cached and not temp_location:
        with open(cache_content_type_file) as fp:
            content_type = fp.read().strip()
        temp_location = cache_file
        logger.notify('Using download cache from %s' % cache_file)
        if link.hash and link.hash_name:
            download_hash = _get_hash_from_file(cache_file, link)
            try:
                _check_hash(download_hash, link)
            except HashMismatch:
                logger.warn(
                    'Cached file %s has bad hash, '
                    're-downloading.' % temp_location
                    )
                temp_location = None
                os.unlink(cache_file)
                os.unlink(cache_content_type_file)
                already_cached = False

    # We don't have either a cached or a downloaded copy
    if not temp_location:
        try:
            resp = session.get(target_url, stream=True)
            resp.raise_for_status()
        except requests.HTTPError as exc:
            logger.fatal("HTTP error %s while getting %s" %
                         (exc.response.status_code, link))
            raise

        content_type = resp.headers.get('content-type', '')
        filename = link.filename  # fallback
        # Have a look at the Content-Disposition header for a better guess
        content_disposition = resp.headers.get('content-disposition')
        if content_disposition:
            type, params = cgi.parse_header(content_disposition)
            # We use ``or`` here because we don't want to use an "empty" value
            # from the filename param.
            filename = params.get('filename') or filename
        ext = splitext(filename)[1]
        if not ext:
            ext = mimetypes.guess_extension(content_type)
            if ext:
                filename += ext
        if not ext and link.url != resp.url:
            ext = os.path.splitext(resp.url)[1]
            if ext:
                filename += ext
        temp_location = os.path.join(temp_dir, filename)
        download_hash = _download_url(resp, link, temp_location)
        if link.hash and link.hash_name:
            _check_hash(download_hash, link)

    if download_dir and not already_downloaded:
        _copy_file(temp_location, download_dir, content_type, link)
    unpack_file(temp_location, location, content_type, link)
    if cache_file and not already_cached:
        cache_download(cache_file, temp_location, content_type)
    if not (already_cached or already_downloaded):
        os.unlink(temp_location)
    os.rmdir(temp_dir)
