"""
runprofileserver.py

    Starts a lightweight Web server with profiling enabled.

Credits for kcachegrind support taken from lsprofcalltree.py go to:
 David Allouche
 Jp Calderone & Itamar Shtull-Trauring
 Johan Dahlin
"""

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from datetime import datetime
from django.conf import settings
import sys

try:
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    USE_STATICFILES = 'django.contrib.staticfiles' in settings.INSTALLED_APPS
except ImportError as e:
    USE_STATICFILES = False

try:
    any
except NameError:
    # backwards compatibility for <2.5
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False


def label(code):
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return '%s %s:%d' % (code.co_name,
                             code.co_filename,
                             code.co_firstlineno)


class KCacheGrind(object):
    def __init__(self, profiler):
        self.data = profiler.getstats()
        self.out_file = None

    def output(self, out_file):
        self.out_file = out_file
        self.out_file.write('events: Ticks\n')
        self._print_summary()
        for entry in self.data:
            self._entry(entry)

    def _print_summary(self):
        max_cost = 0
        for entry in self.data:
            totaltime = int(entry.totaltime * 1000)
            max_cost = max(max_cost, totaltime)
        self.out_file.write('summary: %d\n' % (max_cost,))

    def _entry(self, entry):
        out_file = self.out_file

        code = entry.code
        #print >> out_file, 'ob=%s' % (code.co_filename,)
        if isinstance(code, str):
            out_file.write('fi=~\n')
        else:
            out_file.write('fi=%s\n' % (code.co_filename,))
        out_file.write('fn=%s\n' % (label(code),))

        inlinetime = int(entry.inlinetime * 1000)
        if isinstance(code, str):
            out_file.write('0  %s\n' % inlinetime)
        else:
            out_file.write('%d %d\n' % (code.co_firstlineno, inlinetime))

        # recursive calls are counted in entry.calls
        if entry.calls:
            calls = entry.calls
        else:
            calls = []

        if isinstance(code, str):
            lineno = 0
        else:
            lineno = code.co_firstlineno

        for subentry in calls:
            self._subentry(lineno, subentry)
        out_file.write("\n")

    def _subentry(self, lineno, subentry):
        out_file = self.out_file
        code = subentry.code
        #out_file.write('cob=%s\n' % (code.co_filename,))
        out_file.write('cfn=%s\n' % (label(code),))
        if isinstance(code, str):
            out_file.write('cfi=~\n')
            out_file.write('calls=%d 0\n' % (subentry.callcount,))
        else:
            out_file.write('cfi=%s\n' % (code.co_filename,))
            out_file.write('calls=%d %d\n' % (subentry.callcount, code.co_firstlineno))

        totaltime = int(subentry.totaltime * 1000)
        out_file.write('%d %d\n' % (lineno, totaltime))


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
                    help='Tells Django to NOT use the auto-reloader.'),
        make_option('--adminmedia', dest='admin_media_path', default='',
                    help='Specifies the directory from which to serve admin media.'),
        make_option('--prof-path', dest='prof_path', default='/tmp',
                    help='Specifies the directory which to save profile information in.'),
        make_option('--prof-file', dest='prof_file', default='{path}.{duration:06d}ms.{time}',
                    help='Set filename format, default if "{path}.{duration:06d}ms.{time}".'),
        make_option('--nomedia', action='store_true', dest='no_media', default=False,
                    help='Do not profile MEDIA_URL and ADMIN_MEDIA_URL'),
        make_option('--use-cprofile', action='store_true', dest='use_cprofile', default=False,
                    help='Use cProfile if available, this is disabled per default because of incompatibilities.'),
        make_option('--kcachegrind', action='store_true', dest='use_lsprof', default=False,
                    help='Create kcachegrind compatible lsprof files, this requires and automatically enables cProfile.'),
    )
    if USE_STATICFILES:
        option_list += (
            make_option('--nostatic', action="store_false", dest='use_static_handler', default=True,
                        help='Tells Django to NOT automatically serve static files at STATIC_URL.'),
            make_option('--insecure', action="store_true", dest='insecure_serving', default=False,
                        help='Allows serving static files even if DEBUG is False.'),
        )
    help = "Starts a lightweight Web server with profiling enabled."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        import django
        import socket
        import errno
        from django.core.servers.basehttp import run
        try:
            from django.core.servers.basehttp import get_internal_wsgi_application as WSGIHandler
        except ImportError:
            from django.core.handlers.wsgi import WSGIHandler  # noqa

        try:
            from django.core.servers.basehttp import AdminMediaHandler
            HAS_ADMINMEDIAHANDLER = True
        except ImportError:
            HAS_ADMINMEDIAHANDLER = False

        try:
            from django.core.servers.basehttp import WSGIServerException as wsgi_server_exc_cls
        except ImportError:  # Django 1.6
            wsgi_server_exc_cls = socket.error

        if args:
            raise CommandError('Usage is runserver %s' % self.args)
        if not addrport:
            addr = ''
            port = '8000'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        use_reloader = options.get('use_reloader', True)
        shutdown_message = options.get('shutdown_message', '')
        no_media = options.get('no_media', False)
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            import os
            import time
            try:
                import hotshot
            except ImportError:
                pass            # python 3.x
            USE_CPROFILE = options.get('use_cprofile', False)
            USE_LSPROF = options.get('use_lsprof', False)
            if USE_LSPROF:
                USE_CPROFILE = True
            if USE_CPROFILE:
                try:
                    import cProfile
                    USE_CPROFILE = True
                except ImportError:
                    print("cProfile disabled, module cannot be imported!")
                    USE_CPROFILE = False
            if USE_LSPROF and not USE_CPROFILE:
                raise SystemExit("Kcachegrind compatible output format required cProfile from Python 2.5")
            prof_path = options.get('prof_path', '/tmp')

            prof_file = options.get('prof_file', '{path}.{duration:06d}ms.{time}')
            if not prof_file.format(path='1', duration=2, time=3):
                prof_file = '{path}.{duration:06d}ms.{time}'
                print("Filename format is wrong. Default format used: '{path}.{duration:06d}ms.{time}'.")

            def get_exclude_paths():
                exclude_paths = []
                media_url = getattr(settings, 'MEDIA_URL', None)
                if media_url:
                    exclude_paths.append(media_url)
                static_url = getattr(settings, 'STATIC_URL', None)
                if static_url:
                    exclude_paths.append(static_url)
                admin_media_prefix = getattr(settings, 'ADMIN_MEDIA_PREFIX', None)
                if admin_media_prefix:
                    exclude_paths.append(admin_media_prefix)
                return exclude_paths

            def make_profiler_handler(inner_handler):
                def handler(environ, start_response):
                    path_info = environ['PATH_INFO']
                    # when using something like a dynamic site middleware is could be necessary
                    # to refetch the exclude_paths every time since they could change per site.
                    if no_media and any(path_info.startswith(p) for p in get_exclude_paths()):
                        return inner_handler(environ, start_response)
                    path_name = path_info.strip("/").replace('/', '.') or "root"
                    profname = "%s.%d.prof" % (path_name, time.time())
                    profname = os.path.join(prof_path, profname)
                    if USE_CPROFILE:
                        prof = cProfile.Profile()
                    else:
                        prof = hotshot.Profile(profname)
                    start = datetime.now()
                    try:
                        return prof.runcall(inner_handler, environ, start_response)
                    finally:
                        # seeing how long the request took is important!
                        elap = datetime.now() - start
                        elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
                        if USE_LSPROF:
                            kg = KCacheGrind(prof)
                            kg.output(open(profname, 'w'))
                        elif USE_CPROFILE:
                            prof.dump_stats(profname)
                        profname2 = prof_file.format(path=path_name, duration=int(elapms), time=int(time.time()))
                        profname2 = os.path.join(prof_path, "%s.prof" % profname2)
                        if not USE_CPROFILE:
                            prof.close()
                        os.rename(profname, profname2)
                return handler

            print("Validating models...")
            self.validate(display_num_errors=True)
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at http://%s:%s/" % (addr, port))
            print("Quit the server with %s." % quit_command)
            path = options.get('admin_media_path', '')
            if not path:
                admin_media_path = os.path.join(django.__path__[0], 'contrib/admin/static/admin')
                if os.path.isdir(admin_media_path):
                    path = admin_media_path
                else:
                    path = os.path.join(django.__path__[0], 'contrib/admin/media')
            try:
                handler = WSGIHandler()
                if HAS_ADMINMEDIAHANDLER:
                    handler = AdminMediaHandler(handler, path)
                if USE_STATICFILES:
                    use_static_handler = options.get('use_static_handler', True)
                    insecure_serving = options.get('insecure_serving', False)
                    if (use_static_handler and (settings.DEBUG or insecure_serving)):
                        handler = StaticFilesHandler(handler)
                handler = make_profiler_handler(handler)
                run(addr, int(port), handler)
            except wsgi_server_exc_cls as e:
                # Use helpful error messages instead of ugly tracebacks.
                ERRORS = {
                    errno.EACCES: "You don't have permission to access that port.",
                    errno.EADDRINUSE: "That port is already in use.",
                    errno.EADDRNOTAVAIL: "That IP address can't be assigned-to.",
                }
                if not isinstance(e, socket.error):  # Django < 1.6
                    ERRORS[13] = ERRORS.pop(errno.EACCES)
                    ERRORS[98] = ERRORS.pop(errno.EADDRINUSE)
                    ERRORS[99] = ERRORS.pop(errno.EADDRNOTAVAIL)
                try:
                    if not isinstance(e, socket.error):  # Django < 1.6
                        error_text = ERRORS[e.args[0].args[0]]
                    else:
                        error_text = ERRORS[e.errno]
                except (AttributeError, KeyError):
                    error_text = str(e)
                sys.stderr.write(self.style.ERROR("Error: %s" % error_text) + '\n')
                # Need to use an OS exit because sys.exit doesn't work in a thread
                os._exit(1)
            except KeyboardInterrupt:
                if shutdown_message:
                    print(shutdown_message)
                sys.exit(0)
        if use_reloader:
            from django.utils import autoreload
            autoreload.main(inner_run)
        else:
            inner_run()
