from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django_extensions.management.utils import setup_logger, RedirectHandler
from optparse import make_option
import os
import sys
import time

try:
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    USE_STATICFILES = 'django.contrib.staticfiles' in settings.INSTALLED_APPS
except ImportError:
    USE_STATICFILES = False

import logging
logger = logging.getLogger(__name__)

from django_extensions.management.technical_response import null_technical_500_response


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
                    help='Tells Django to NOT use the auto-reloader.'),
        make_option('--browser', action='store_true', dest='open_browser',
                    help='Tells Django to open a browser.'),
        make_option('--adminmedia', dest='admin_media_path', default='',
                    help='Specifies the directory from which to serve admin media.'),
        make_option('--threaded', action='store_true', dest='threaded',
                    help='Run in multithreaded mode.'),
        make_option('--output', dest='output_file', default=None,
                    help='Specifies an output file to send a copy of all messages (not flushed immediately).'),
        make_option('--print-sql', action='store_true', default=False,
                    help="Print SQL queries as they're executed"),
        make_option('--cert', dest='cert_path', action="store", type="string",
                    help='To use SSL, specify certificate path.'),

    )
    if USE_STATICFILES:
        option_list += (
            make_option('--nostatic', action="store_false", dest='use_static_handler', default=True,
                        help='Tells Django to NOT automatically serve static files at STATIC_URL.'),
            make_option('--insecure', action="store_true", dest='insecure_serving', default=False,
                        help='Allows serving static files even if DEBUG is False.'),
        )
    help = "Starts a lightweight Web server for development."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        import django

        setup_logger(logger, self.stderr, filename=options.get('output_file', None))  # , fmt="[%(name)s] %(message)s")
        logredirect = RedirectHandler(__name__)

        # Redirect werkzeug log items
        werklogger = logging.getLogger('werkzeug')
        werklogger.setLevel(logging.INFO)
        werklogger.addHandler(logredirect)
        werklogger.propagate = False

        if options.get("print_sql", False):
            from django.db.backends import util
            try:
                import sqlparse
            except ImportError:
                sqlparse = None  # noqa

            class PrintQueryWrapper(util.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        execution_time = time.time() - starttime
                        therest = ' -- [Execution time: %.6fs] [Database: %s]' % (execution_time, self.db.alias)
                        if sqlparse:
                            logger.info(sqlparse.format(raw_sql, reindent=True) + therest)
                        else:
                            logger.info(raw_sql + therest)

            util.CursorDebugWrapper = PrintQueryWrapper

        try:
            from django.core.servers.basehttp import AdminMediaHandler
            USE_ADMINMEDIAHANDLER = True
        except ImportError:
            USE_ADMINMEDIAHANDLER = False

        try:
            from django.core.servers.basehttp import get_internal_wsgi_application as WSGIHandler
        except ImportError:
            from django.core.handlers.wsgi import WSGIHandler  # noqa
        try:
            from werkzeug import run_simple, DebuggedApplication
        except ImportError:
            raise CommandError("Werkzeug is required to use runserver_plus.  Please visit http://werkzeug.pocoo.org/ or install via pip. (pip install Werkzeug)")

        # usurp django's handler
        from django.views import debug
        debug.technical_500_response = null_technical_500_response

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

        threaded = options.get('threaded', False)
        use_reloader = options.get('use_reloader', True)
        open_browser = options.get('open_browser', False)
        cert_path = options.get("cert_path")
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            print("Validating models...")
            self.validate(display_num_errors=True)
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at http://%s:%s/" % (addr, port))
            print("Using the Werkzeug debugger (http://werkzeug.pocoo.org/)")
            print("Quit the server with %s." % quit_command)
            path = options.get('admin_media_path', '')
            if not path:
                admin_media_path = os.path.join(django.__path__[0], 'contrib/admin/static/admin')
                if os.path.isdir(admin_media_path):
                    path = admin_media_path
                else:
                    path = os.path.join(django.__path__[0], 'contrib/admin/media')
            handler = WSGIHandler()
            if USE_ADMINMEDIAHANDLER:
                handler = AdminMediaHandler(handler, path)
            if USE_STATICFILES:
                use_static_handler = options.get('use_static_handler', True)
                insecure_serving = options.get('insecure_serving', False)
                if use_static_handler and (settings.DEBUG or insecure_serving):
                    handler = StaticFilesHandler(handler)
            if open_browser:
                import webbrowser
                url = "http://%s:%s/" % (addr, port)
                webbrowser.open(url)
            if cert_path:
                """
                OpenSSL is needed for SSL support.

                This will make flakes8 throw warning since OpenSSL is not used
                directly, alas, this is the only way to show meaningful error
                messages. See:
                http://lucumr.pocoo.org/2011/9/21/python-import-blackbox/
                for more information on python imports.
                """
                try:
                    import OpenSSL  # NOQA
                except ImportError:
                    raise CommandError("Python OpenSSL Library is "
                                       "required to use runserver_plus with ssl support. "
                                       "Install via pip (pip install pyOpenSSL).")

                dir_path, cert_file = os.path.split(cert_path)
                if not dir_path:
                    dir_path = os.getcwd()
                root, ext = os.path.splitext(cert_file)
                certfile = os.path.join(dir_path, root + ".crt")
                keyfile = os.path.join(dir_path, root + ".key")
                try:
                    from werkzeug.serving import make_ssl_devcert
                    if os.path.exists(certfile) and \
                            os.path.exists(keyfile):
                                ssl_context = (certfile, keyfile)
                    else:  # Create cert, key files ourselves.
                        ssl_context = make_ssl_devcert(
                            os.path.join(dir_path, root), host='localhost')
                except ImportError:
                    print("Werkzeug version is less than 0.9, trying adhoc certificate.")
                    ssl_context = "adhoc"

            else:
                ssl_context = None
            run_simple(
                addr,
                int(port),
                DebuggedApplication(handler, True),
                use_reloader=use_reloader,
                use_debugger=True,
                threaded=threaded,
                ssl_context=ssl_context
            )
        inner_run()
