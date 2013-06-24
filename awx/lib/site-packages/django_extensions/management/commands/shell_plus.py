import os
import six
import time
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from django_extensions.management.shells import import_objects


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--plain', action='store_true', dest='plain',
                    help='Tells Django to use plain Python, not BPython nor IPython.'),
        make_option('--bpython', action='store_true', dest='bpython',
                    help='Tells Django to use BPython, not IPython.'),
        make_option('--ipython', action='store_true', dest='ipython',
                    help='Tells Django to use IPython, not BPython.'),
        make_option('--notebook', action='store_true', dest='notebook',
                    help='Tells Django to use IPython Notebook.'),
        make_option('--use-pythonrc', action='store_true', dest='use_pythonrc',
                    help='Tells Django to execute PYTHONSTARTUP file (BE CAREFULL WITH THIS!)'),
        make_option('--print-sql', action='store_true', default=False,
                    help="Print SQL queries as they're executed"),
        make_option('--dont-load', action='append', dest='dont_load', default=[],
                    help='Ignore autoloading of some apps/models. Can be used several times.'),
        make_option('--quiet-load', action='store_true', default=False, dest='quiet_load',
                    help='Do not display loaded models messages'),
    )
    help = "Like the 'shell' command but autoloads the models of all installed Django apps."

    requires_model_validation = True

    def handle_noargs(self, **options):
        use_notebook = options.get('notebook', False)
        use_ipython = options.get('ipython', False)
        use_bpython = options.get('bpython', False)
        use_plain = options.get('plain', False)
        use_pythonrc = options.get('use_pythonrc', True)

        if options.get("print_sql", False):
            # Code from http://gist.github.com/118990
            from django.db.backends import util
            sqlparse = None
            try:
                import sqlparse
            except ImportError:
                pass

            class PrintQueryWrapper(util.CursorDebugWrapper):
                def execute(self, sql, params=()):
                    starttime = time.time()
                    try:
                        return self.cursor.execute(sql, params)
                    finally:
                        execution_time = time.time() - starttime
                        raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
                        if sqlparse:
                            print(sqlparse.format(raw_sql, reindent=True))
                        else:
                            print(raw_sql)
                        print("")
                        print('Execution time: %.6fs [Database: %s]' % (execution_time, self.db.alias))
                        print("")

            util.CursorDebugWrapper = PrintQueryWrapper

        def run_notebook():
            from django.conf import settings
            from IPython.frontend.html.notebook import notebookapp
            app = notebookapp.NotebookApp.instance()
            ipython_arguments = getattr(settings, 'IPYTHON_ARGUMENTS', ['--ext', 'django_extensions.management.notebook_extension'])
            app.initialize(ipython_arguments)
            app.start()

        def run_plain():
            # Using normal Python shell
            import code
            imported_objects = import_objects(options, self.style)
            try:
                # Try activating rlcompleter, because it's handy.
                import readline
            except ImportError:
                pass
            else:
                # We don't have to wrap the following import in a 'try', because
                # we already know 'readline' was imported successfully.
                import rlcompleter
                readline.set_completer(rlcompleter.Completer(imported_objects).complete)
                readline.parse_and_bind("tab:complete")

            # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
            # conventions and get $PYTHONSTARTUP first then import user.
            if use_pythonrc:
                pythonrc = os.environ.get("PYTHONSTARTUP")
                if pythonrc and os.path.isfile(pythonrc):
                    global_ns = {}
                    with open(pythonrc) as rcfile:
                        try:
                            six.exec_(compile(rcfile.read(), pythonrc, 'exec'), global_ns)
                            imported_objects.update(global_ns)
                        except NameError:
                            pass
                # This will import .pythonrc.py as a side-effect
                try:
                    import user  # NOQA
                except ImportError:
                    pass
            code.interact(local=imported_objects)

        def run_bpython():
            from bpython import embed
            imported_objects = import_objects(options, self.style)
            embed(imported_objects)

        def run_ipython():
            try:
                from IPython import embed
                imported_objects = import_objects(options, self.style)
                embed(user_ns=imported_objects)
            except ImportError:
                # IPython < 0.11
                # Explicitly pass an empty list as arguments, because otherwise
                # IPython would use sys.argv from this script.
                # Notebook not supported for IPython < 0.11.
                from IPython.Shell import IPShell
                imported_objects = import_objects(options, self.style)
                shell = IPShell(argv=[], user_ns=imported_objects)
                shell.mainloop()

        shells = (
            ('bpython', run_bpython),
            ('ipython', run_ipython),
            ('plain', run_plain),
        )
        SETTINGS_SHELL_PLUS = getattr(settings, 'SHELL_PLUS', None)

        if use_notebook:
            run_notebook()
        elif use_plain:
            run_plain()
        elif use_ipython:
            run_ipython()
        elif use_bpython:
            run_bpython()
        elif SETTINGS_SHELL_PLUS:
            try:
                dict(shells)[SETTINGS_SHELL_PLUS]()
            except ImportError:
                import traceback
                traceback.print_exc()
                print(self.style.ERROR("Could not load '%s' Python environment." % SETTINGS_SHELL_PLUS))
        else:
            for shell_name, func in shells:
                try:
                    func()
                except ImportError:
                    continue
                else:
                    break
            else:
                import traceback
                traceback.print_exc()
                print(self.style.ERROR("Could not load any interactive Python environment."))

